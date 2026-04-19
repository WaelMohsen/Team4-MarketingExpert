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

DEFAULT_CAMPAIGN_TARGET = {
    "primary_goal": "increase qualified leads",
    "kpis": ["leads", "cpl"]
}

DEFAULT_BUSINESS_DOMAIN = {
    "industry": "Retail",
    "offering": "Membership plan",
    "audience": "People shopping for monthly essentials",
    "funnel_stage": "conversion",
}

def parse_args():
    parser = argparse.ArgumentParser(description="Modular Ads Pipeline Engine - Strict Row-by-Row")
    parser.add_argument("--input-csv", type=str, default="data/raw/ads_data.csv")
    parser.add_argument("--output-base-dir", type=str, default="data/outputs/")
    parser.add_argument("--row-limit", type=int, default=None, help="Limit the number of rows to process")
    parser.add_argument("--skip-evaluation", action="store_true", help="Skip evaluation stage")
    return parser.parse_args()

def main():
    args = parse_args()

    # 1. Create a timestamped run folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    global_dir = os.path.join(args.output_base_dir, "_global", timestamp, "results")
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

    # 3. Phase B: Iterative Row-by-Row Processing
    granular_modules = [
        EnrichmentModule(),
        AnalysisModule(),
        RecommendationModule()
    ]
    if not args.skip_evaluation:
        granular_modules.append(EvaluationModule())

    logger.info(f"Starting Granular Processing for {len(processed_df)} campaigns...")

    for i, row in processed_df.iterrows():
        campaign_name = f"campaign_{i+1}"
        row_dir = os.path.join(args.output_base_dir, campaign_name, f"run_{timestamp}", "results")
        os.makedirs(row_dir, exist_ok=True)
        
        logger.info(f"--- Processing {campaign_name} ---")
        
        # Create a fresh context for this specific row
        row_context = ExecutionContext()
        # Pass essential metadata
        row_context.set_metadata("campaign_target", DEFAULT_CAMPAIGN_TARGET)
        row_context.set_metadata("business_domain", DEFAULT_BUSINESS_DOMAIN)
        row_context.set_metadata("output_json_dir", row_dir) # Base for relative paths
        
        # This is where modules will save their individual results
        row_context.runtime_output_path = row_dir
        
        # Important: The module expects a DataFrame in processed_df
        # We wrap the single row in a DF
        row_context.processed_df = pd.DataFrame([row])

        # Execute granular modules manually for this context
        for module in granular_modules:
            try:
                row_context = module.run(row_context)
                module.save(row_context)
            except Exception as e:
                logger.error(f"Error in {module.name} for {campaign_name}: {e}")
                row_context.errors.append(f"{module.name}: {e}")

    logger.info(f"All campaigns processed. Results available under: {args.output_base_dir}")

if __name__ == "__main__":
    main()