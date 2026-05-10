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

from src.shared.utils.observability import observe, set_trace_metadata, propagate_attributes, flush_langfuse

# Setup logging
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(name)s | %(message)s')
logger = logging.getLogger(__name__)

@observe()
def process_campaign(i, row, timestamp, args, granular_modules):
    campaign_name = f"campaign_{i+1}"
    row_dir = os.path.join(args.output_base_dir, campaign_name, f"run_{timestamp}", "results")
    os.makedirs(row_dir, exist_ok=True)
    
    logger.info(f"--- Processing {campaign_name} ---")
    
    # Pull campaign target from row data
    campaign_target = {
        "primary_goal": str(row.get("primary_goal", "Unknown")),
    }
    
    business_domain = {
        "industry": str(row.get("industry", "Unknown")),
        "offering": str(row.get("offering", "Unknown")),
        "audience": str(row.get("audience", "Unknown")),
        "funnel_stage": str(row.get("funnel_stage", "Unknown")),
    }

    # Use propagate_attributes for row-specific context that child spans should inherit
    with propagate_attributes(
        trace_name=f"Analysis: {campaign_name}",
        metadata={
            "campaign": campaign_name,
            "row_index": str(i)
        },
        tags=[campaign_name, "production"]
    ):
        # Create a fresh context for this specific row
        row_context = ExecutionContext()
        
        # Pass essential metadata
        row_context.set_metadata("campaign_target", campaign_target)
        row_context.set_metadata("business_domain", business_domain)
        row_context.set_metadata("output_json_dir", row_dir)
        row_context.runtime_output_path = row_dir
        row_context.processed_df = pd.DataFrame([row])

        # Execute granular modules
        for module in granular_modules:
            try:
                row_context = module.run(row_context)
                module.save(row_context)
            except Exception as e:
                logger.error(f"Error in {module.name} for {campaign_name}: {e}")
                row_context.errors.append(f"{module.name}: {e}")
        
        return row_context

def parse_args():
    parser = argparse.ArgumentParser(description="Modular Ads Pipeline Engine - Strict Row-by-Row")
    parser.add_argument("--input-csv", type=str, default="data/raw/ads_data.csv")
    parser.add_argument("--output-base-dir", type=str, default="data/outputs/")
    parser.add_argument("--row-limit", type=int, default=None, help="Limit the number of rows to process")
    parser.add_argument("--skip-evaluation", action="store_true", help="Skip evaluation stage")
    return parser.parse_args()

@observe(name="Pipeline Preparation")
def run_preparation_phase(args, global_dir):
    # Phase A: Preparation (Ingestion & Preprocessing)
    prep_context = ExecutionContext()
    prep_context.set_metadata("input_csv", args.input_csv)
    prep_context.set_metadata("output_json_dir", global_dir) 

    prep_engine = PipelineEngine()
    prep_engine.add_module(IngestionModule())
    prep_engine.add_module(PreprocessingModule())
    
    logger.info("Executing Preparation Phase (Ingestion & Preprocessing)...")
    prep_context = prep_engine.run(prep_context)
    return prep_context

def main():
    args = parse_args()

    # 1. Create a timestamped run folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    global_dir = os.path.join(args.output_base_dir, "_global", f"run_{timestamp}", "results")
    os.makedirs(global_dir, exist_ok=True)
    logger.info(f"Initialized Global Run Folder: {global_dir}")

    # Use propagate_attributes for global run context
    with propagate_attributes(session_id=f"run_{timestamp}", tags=[os.path.basename(args.input_csv)]):
        prep_context = run_preparation_phase(args, global_dir)
        
        if prep_context.errors:
            logger.error(f"Preparation phase failed: {prep_context.errors}")
            return

        processed_df = prep_context.processed_df
        if processed_df is None or processed_df.empty:
            logger.error("No data found after preprocessing. Exiting.")
            return

        if args.row_limit is not None:
            processed_df = processed_df.iloc[:args.row_limit]
            logger.info(f"Limiting execution to first {args.row_limit} rows.")

        # 3. Phase B: Iterative Row-by-Row Processing
        granular_modules = [
            EnrichmentModule(),
            AnalysisModule(),
            RecommendationModule()
        ]

        if not args.skip_evaluation:
            granular_modules.append(EvaluationModule())

        for i, row in processed_df.iterrows():
            process_campaign(i, row, timestamp, args, granular_modules)

        logger.info(f"All campaigns processed. Results available under: {args.output_base_dir}")
        
    # Flush Langfuse before exit
    flush_langfuse()

if __name__ == "__main__":
    main()