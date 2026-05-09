import os
import argparse
import logging
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

from src.core.pipeline_engine import PipelineEngine
from src.core.execution_context import ExecutionContext
from src.modules.ingestion.ingestion_module import IngestionModule
from src.modules.preprocessing.preprocessing_module import PreprocessingModule
from src.modules.enrichment.enrichment_module import EnrichmentModule
from src.modules.analysis.analysis_module import AnalysisModule
from src.modules.recommendation.recommendation_module import RecommendationModule
from src.modules.evaluation.evaluation_module import EvaluationModule

# Setup logging
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(name)s | %(message)s')
logger = logging.getLogger(__name__)



def parse_args():
    parser = argparse.ArgumentParser(description="Modular Ads Pipeline Engine - Strict Row-by-Row")
    parser.add_argument("--input-csv", type=str, default="data/raw/ads_data.csv")
    parser.add_argument("--output-base-dir", type=str, default="data/outputs/")
    parser.add_argument("--row-limit", type=int, default=None, help="Limit the total number of rows to process")
    parser.add_argument("--batch-size", type=int, default=6, help="Number of rows processed in a single LLM call (default: 6)")
    parser.add_argument("--skip-evaluation", action="store_true", help="Skip evaluation stage")
    return parser.parse_args()

def main():
    args = parse_args()

    # 1. Create a timestamped run folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    global_dir = os.path.join(args.output_base_dir, "_global", f"run_{timestamp}", "results")
    os.makedirs(global_dir, exist_ok=True)
    logger.info(f"Initialized Global Run Folder: {global_dir}")

    # 2. Phase A: Preparation (Ingestion & Preprocessing)
    # We clean the whole file once to ensure standardized structure
    engine = PipelineEngine()
    
    prep_context = ExecutionContext()
    prep_context.set_metadata("input_csv", args.input_csv)
    # Global intermediate data saved to central audit
    prep_context.set_metadata("output_json_dir", global_dir) 

    prep_engine = PipelineEngine()
    prep_engine.add_module(IngestionModule())
    prep_engine.add_module(PreprocessingModule())
    
    logger.info("Executing Preparation Phase (Ingestion & Preprocessing)...")
    prep_context = prep_engine.run(prep_context)
    
    if prep_context.errors:
        logger.error(f"Preparation phase failed: {prep_context.errors}")
        return

    processed_df = prep_context.processed_df
    if processed_df is None or processed_df.empty:
        logger.error("No data found after preprocessing. Exiting.")
        return

    # Apply row limit if specified
    if args.row_limit is not None:
        processed_df = processed_df.iloc[:args.row_limit]
        logger.info(f"Limiting execution to first {args.row_limit} rows.")

    # 3. Phase B: Batch Processing
    # Slice processed_df into batches of --batch-size rows.
    # To change batch size at runtime: --batch-size N
    # To change the permanent default: edit default=6 in parse_args() only.
    batch_size = args.batch_size
    total_rows = len(processed_df)

    granular_modules = [
        EnrichmentModule(),
        AnalysisModule(),
        RecommendationModule()
    ]
    if not args.skip_evaluation:
        granular_modules.append(EvaluationModule())

    logger.info(f"Starting Batch Processing: {total_rows} rows → batches of {batch_size}.")

    for batch_start in range(0, total_rows, batch_size):
        batch_end = min(batch_start + batch_size, total_rows)
        df_batch = processed_df.iloc[batch_start:batch_end]

        batch_label = f"batch_{batch_start + 1}_{batch_end}"
        batch_dir = os.path.join(args.output_base_dir, batch_label, f"run_{timestamp}", "results")
        os.makedirs(batch_dir, exist_ok=True)

        logger.info(f"--- Processing {batch_label} (rows {batch_start + 1}–{batch_end}) ---")

        # Derive metadata from the first row; all rows in a batch share
        # the same campaign target and business domain.
        first_row = df_batch.iloc[0]

        campaign_target = {
            "primary_goal": str(first_row.get("primary_goal", "Unknown")),
        }

        business_domain = {
            "industry":     str(first_row.get("industry",     "Unknown")),
            "offering":     str(first_row.get("offering",     "Unknown")),
            "audience":     str(first_row.get("audience",     "Unknown")),
            "funnel_stage": str(first_row.get("funnel_stage", "Unknown")),
        }

        # Build a fresh context for this batch
        batch_context = ExecutionContext()
        batch_context.set_metadata("campaign_target",  campaign_target)
        batch_context.set_metadata("business_domain",  business_domain)
        batch_context.set_metadata("output_json_dir",  batch_dir)
        batch_context.runtime_output_path = batch_dir

        # Pass the full batch slice — modules receive a multi-row DataFrame
        batch_context.processed_df = df_batch.reset_index(drop=True)

        # Execute granular modules against the full batch context
        for module in granular_modules:
            try:
                batch_context = module.run(batch_context)
                module.save(batch_context)
            except Exception as e:
                logger.error(f"Error in {module.name} for {batch_label}: {e}")
                batch_context.errors.append(f"{module.name}: {e}")

    logger.info(f"All batches processed. Results available under: {args.output_base_dir}")

if __name__ == "__main__":
    main()