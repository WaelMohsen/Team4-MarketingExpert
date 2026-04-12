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
    parser.add_argument("--num-campaigns", type=int, default=2, help="Number of campaigns (rows) to process")
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
        usecols=None, # Use all available columns
        aggregate=False, # Process row by row
        remove_duplicates=False,
        compute_kpis=True,
        campaign_objective = "Leads"
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
    
    final_results = []
    
    for idx, campaign_data in enumerate(campaign_platforms_data):
        output_path = os.path.join(args.output_json_dir, f"campaign_{idx+1}_result.json")
        
        if os.path.exists(output_path):
            logger.info(f"\n--- Skipping Campaign {idx+1}/{len(campaign_platforms_data)} (Result already exists) ---")
            continue

        logger.info(f"\n--- Processing Campaign {idx+1}/{len(campaign_platforms_data)} ---")
        
        # Extract dynamic metadata if available, else fall back to defaults
        primary_goal = campaign_data.get("primary_goal", DEFAULT_CAMPAIGN_TARGET["primary_goal"])
        kpis_raw = campaign_data.get("kpis")
        if isinstance(kpis_raw, str):
            kpis = [k.strip() for k in kpis_raw.split(",")]
        else:
            kpis = DEFAULT_CAMPAIGN_TARGET["kpis"]
            
        current_campaign_target = {
            "primary_goal": primary_goal,
            "kpis": kpis
        }

        current_business_domain = {
            "industry": campaign_data.get("industry", DEFAULT_BUSINESS_DOMAIN["industry"]),
            "offering": campaign_data.get("offering", DEFAULT_BUSINESS_DOMAIN["offering"]),
            "audience": campaign_data.get("audience", DEFAULT_BUSINESS_DOMAIN["audience"]),
            "funnel_stage": campaign_data.get("funnel_stage", DEFAULT_BUSINESS_DOMAIN["funnel_stage"]),
        }

        # --- Prompting layer : Stage 1 (Analysis) ---
        analysis_messages = builder.build_analysis_prompt(
            sysPromptPath="prompt_system_analysis.txt",
            userPromptPath="prompt_user_analysis.txt",
            campaign_platforms_data=[campaign_data]
        )
        
        logger.info(f"\n--- Executing Stage 1: Analysis for Campaign {idx+1} ---")
        analysis_result: Dict[str, Any] = client.generate_json(analysis_messages, response_format=AnalysisResponse)
        logger.info(f"\n=== Stage 1 LLM JSON Response (Analysis) for Campaign {idx+1} ===\n")
        logger.info(json.dumps(analysis_result, ensure_ascii=False, indent=2))
        
        # --- Prompting layer : Stage 2 (Recommendation) ---
        recommendation_messages = builder.build_recommendation_prompt(
            sysPromptPath="prompt_system_recommendation.txt",
            userPromptPath="prompt_user_recommendation.txt",
            campaign_target=current_campaign_target,
            business_domain=current_business_domain,
            analysis_json=analysis_result
        )

        logger.info(f"\n--- Executing Stage 2: Recommendations for Campaign {idx+1} ---")
        recommendation_result: Dict[str, Any] = client.generate_json(recommendation_messages, response_format=RecommendationResponse)
        
        logger.info(f"\n=== Stage 2 LLM JSON Response (Recommendations) for Campaign {idx+1} ===\n")
        logger.info(json.dumps(recommendation_result, ensure_ascii=False, indent=2))
        
        # Combine everything
        campaign_result = {
            "campaign_target": current_campaign_target,
            "business_domain": current_business_domain,
            "input_data": campaign_data,
            "analysis_response": analysis_result,
            "recommendation_response": recommendation_result
        }
        
        # Save each campaign result to its own JSON file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(campaign_result, f, ensure_ascii=False, indent=2)
            
        final_results.append(campaign_result)
        
    return final_results

if __name__ == "__main__":
    main()