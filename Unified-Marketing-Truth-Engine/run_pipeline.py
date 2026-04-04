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
    parser.add_argument("--input-csv", type=str, default="data/raw/global_ads_performance_dataset.csv")
    parser.add_argument("--analysis-output", type=str, default="data/outputs/analysis.json")
    parser.add_argument("--recommendations-output", type=str, default="data/outputs/recommendations.json")
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
        usecols=["date", "platform", "campaign_type", "impressions", "clicks", "spend", "conversions", "revenue"],
        compute_kpis=True,
        campaign_objective = "Leads"
    )
    
    #print(campaign_platforms_data)

    # --- Prompting layer : Stage 1 (Analysis) ---
    loader = PromptLoader.from_module_dir()
    builder = PromptBuilder(loader=loader)
    
    analysis_messages = builder.build_analysis_prompt(
        sysPromptPath="prompt_system_analysis.txt",
        userPromptPath="prompt_user_analysis.txt",
        campaign_platforms_data=campaign_platforms_data
    )
    
    from src.LLMs_and_Prompts.structured_outputs import AnalysisResponse, RecommendationResponse
    
    logger.info("\n--- Executing Stage 1: Analysis ---")
    
    client = LLMApiClient(
        model=os.getenv("OPENAI_MODEL"),
        max_output_tokens=1500,
    )
    
    analysis_result: Dict[str, Any] = client.generate_json(analysis_messages, response_format=AnalysisResponse)
    logger.info("\n=== Stage 1 LLM JSON Response (Analysis) ===\n")
    logger.info(json.dumps(analysis_result, ensure_ascii=False, indent=2))
    
    # Save intermediate for debugging
    os.makedirs(os.path.dirname(args.analysis_output), exist_ok=True)
    with open(args.analysis_output, "w", encoding="utf-8") as f:
        json.dump(analysis_result, f, ensure_ascii=False, indent=2)

    # --- Prompting layer : Stage 2 (Recommendation) ---
    recommendation_messages = builder.build_recommendation_prompt(
        sysPromptPath="prompt_system_recommendation.txt",
        userPromptPath="prompt_user_recommendation.txt",
        campaign_target=DEFAULT_CAMPAIGN_TARGET,
        business_domain=DEFAULT_BUSINESS_DOMAIN,
        analysis_json=analysis_result
    )

    logger.info("\n--- Executing Stage 2: Recommendations ---")
    recommendation_result: Dict[str, Any] = client.generate_json(recommendation_messages, response_format=RecommendationResponse)
    
    logger.info("\n=== Stage 2 LLM JSON Response (Recommendations) ===\n")
    logger.info(json.dumps(recommendation_result, ensure_ascii=False, indent=2))
    
    # Optional: save messages to file for debugging / inspection
    os.makedirs(os.path.dirname(args.recommendations_output), exist_ok=True)
    with open(args.recommendations_output, "w", encoding="utf-8") as f:
        json.dump(recommendation_result, f, ensure_ascii=False, indent=2)
    
    return recommendation_result

if __name__ == "__main__":
    main()