import json
import os
import argparse
import logging
from dotenv import load_dotenv

from typing                                             import List, Dict, Any
from src.data_preprocessing.data_loader                 import AdsDataLoader
from src.data_preprocessing.ads_schema                  import UnifiedAdsSchema
from src.data_preprocessing.ads_preprocessor            import AdsPreprocessor
from src.data_preprocessing.ads_preprocessing_pipeline  import UnifiedAdsPipeline
from src.LLMs_and_Prompts.prompt_loader                 import PromptLoader
from src.LLMs_and_Prompts.prompt_builder                import PromptBuilder
from src.LLMs_and_Prompts.api_client                    import LLMApiClient

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(message)s')
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
    parser = argparse.ArgumentParser(description="Unified Ads Pipeline")
    parser.add_argument("--input-csv", type=str, default="Unified-Marketing-Truth-Engine/data/raw/ads_data.csv")
    parser.add_argument("--output-json-dir", type=str, default="Unified-Marketing-Truth-Engine/data/outputs/")
    parser.add_argument("--num-campaigns", type=int, default=6, help="Number of rows to include in a single batch LLM call")
    return parser.parse_args()

def main():
    args = parse_args()

    schema       = UnifiedAdsSchema()
    preprocessor = AdsPreprocessor(schema=schema)
    pipeline     = UnifiedAdsPipeline(preprocessor=preprocessor, schema=schema)

    # Pass a FILE PATH directly (pipeline will load it using AdsDataLoader)
    # transform() = read -> map -> validate -> types -> duplicates -> compute KPIs

    logger.info(f"Loading and processing data from: {args.input_csv}")
    campaign_platforms_data = pipeline.transform(
        args.input_csv,
        aggregate=False,        # row-by-row — batch slicing happens below
        remove_duplicates=False,
        compute_kpis=True,
        campaign_objective="Leads",
    )
    
    # Restrict processing to args.num_campaigns
    campaign_platforms_data = campaign_platforms_data[:args.num_campaigns]

    loader = PromptLoader.from_module_dir()
    builder = PromptBuilder(loader=loader)
    
    from src.LLMs_and_Prompts.structured_outputs import AnalysisResponse, RecommendationResponse
    
    client = LLMApiClient(
        model=os.getenv("OPENAI_MODEL"),
        max_output_tokens=4000,
    )
    
    os.makedirs(args.output_json_dir, exist_ok=True)
    
    # --- Derive batch-level metadata from the first row, falling back to defaults ---
    # All rows in a batch share the same campaign target and business domain.
    # To override per-row in the future, split campaign_platforms_data into sub-batches first.
    first_row = campaign_platforms_data[0] if campaign_platforms_data else {}

    kpis_raw = first_row.get("kpis")
    kpis = [k.strip() for k in kpis_raw.split(",")] if isinstance(kpis_raw, str) else DEFAULT_CAMPAIGN_TARGET["kpis"]

    batch_campaign_target = {
        "primary_goal": first_row.get("primary_goal", DEFAULT_CAMPAIGN_TARGET["primary_goal"]),
        "kpis": kpis,
    }

    batch_business_domain = {
        "industry":    first_row.get("industry",    DEFAULT_BUSINESS_DOMAIN["industry"]),
        "offering":    first_row.get("offering",    DEFAULT_BUSINESS_DOMAIN["offering"]),
        "audience":    first_row.get("audience",    DEFAULT_BUSINESS_DOMAIN["audience"]),
        "funnel_stage":first_row.get("funnel_stage",DEFAULT_BUSINESS_DOMAIN["funnel_stage"]),
    }

    batch_size = len(campaign_platforms_data)
    output_path = os.path.join(args.output_json_dir, f"batch_{batch_size}_result.json")

    if os.path.exists(output_path):
        logger.info(f"\n--- Skipping batch of {batch_size} rows (result already exists at {output_path}) ---")
        return []

    logger.info(f"\n--- Processing batch of {batch_size} rows in a single LLM call ---")

    # --- Stage 1: Analysis — pass ALL rows at once ---
    analysis_messages = builder.build_analysis_prompt(
        sysPromptPath="prompt_system_analysis.txt",
        userPromptPath="prompt_user_analysis.txt",
        campaign_platforms_data=campaign_platforms_data,  # full batch, not [single_row]
    )

    logger.info(f"\n--- Executing Stage 1: Analysis (batch of {batch_size}) ---")
    analysis_result: Dict[str, Any] = client.generate_json(analysis_messages, response_format=AnalysisResponse)
    logger.info(f"\n=== Stage 1 LLM JSON Response (Analysis) ===\n")
    logger.info(json.dumps(analysis_result, ensure_ascii=False, indent=2))

    # --- Stage 2: Recommendations — based on the batch analysis ---
    recommendation_messages = builder.build_recommendation_prompt(
        sysPromptPath="prompt_system_recommendation.txt",
        userPromptPath="prompt_user_recommendation.txt",
        campaign_target=batch_campaign_target,
        business_domain=batch_business_domain,
        analysis_json=analysis_result,
    )

    logger.info(f"\n--- Executing Stage 2: Recommendations (batch of {batch_size}) ---")
    recommendation_result: Dict[str, Any] = client.generate_json(recommendation_messages, response_format=RecommendationResponse)
    logger.info(f"\n=== Stage 2 LLM JSON Response (Recommendations) ===\n")
    logger.info(json.dumps(recommendation_result, ensure_ascii=False, indent=2))

    # --- Combine and save the single batch result ---
    batch_result = {
        "batch_size":              batch_size,
        "campaign_target":         batch_campaign_target,
        "business_domain":         batch_business_domain,
        "input_data":              campaign_platforms_data,  # all rows preserved
        "analysis_response":       analysis_result,
        "recommendation_response": recommendation_result,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(batch_result, f, ensure_ascii=False, indent=2)

    logger.info(f"\n--- Batch result saved to: {output_path} ---")
    return [batch_result]

if __name__ == "__main__":
    main()