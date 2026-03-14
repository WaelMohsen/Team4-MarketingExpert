import json
from typing                                             import List, Dict, Any
from src.data_preprocessing.data_loader                 import AdsDataLoader
from src.data_preprocessing.ads_schema                  import UnifiedAdsSchema
from src.data_preprocessing.ads_preprocessor            import AdsPreprocessor
from src.data_preprocessing.ads_preprocessing_pipeline  import UnifiedAdsPipeline
from src.LLMs_and_Prompts.prompt_loader                 import PromptLoader
from src.LLMs_and_Prompts.prompt_builder                import PromptBuilder
from src.LLMs_and_Prompts.api_client                    import LLMApiClient

def main():
    schema       = UnifiedAdsSchema()
    preprocessor = AdsPreprocessor(schema=schema)
    pipeline     = UnifiedAdsPipeline(preprocessor=preprocessor, schema=schema)

    # Pass a FILE PATH directly (pipeline will load it using AdsDataLoader)
    # transform() = read -> map -> validate -> types -> duplicates -> compute KPIs

    campaign_platforms_data = pipeline.transform(
        "data/raw/global_ads_performance_dataset.csv",
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
    
    print("\n--- Executing Stage 1: Analysis ---")
    
    client = LLMApiClient(
        model="gpt-5-mini",
        max_output_tokens=1500,
    )
    
    analysis_result: Dict[str, Any] = client.generate_json(analysis_messages, response_format=AnalysisResponse)
    print("\n=== Stage 1 LLM JSON Response (Analysis) ===\n")
    print(json.dumps(analysis_result, ensure_ascii=False, indent=2))
    
    # Save intermediate for debugging
    with open("data/outputs/analysis.json", "w", encoding="utf-8") as f:
        json.dump(analysis_result, f, ensure_ascii=False, indent=2)

    # --- Prompting layer : Stage 2 (Recommendation) ---
    campaign_target = {
        "primary_goal": "increase qualified leads",
        "kpis": ["leads", "cpl"]
    }
    
    business_domain = {
        "industry": "Retail",
        "offering": "Membership plan",
        "audience": "People shopping for monthly essentials",
        "funnel_stage": "conversion",
    }
    
    recommendation_messages = builder.build_recommendation_prompt(
        sysPromptPath="prompt_system_recommendation.txt",
        userPromptPath="prompt_user_recommendation.txt",
        campaign_target=campaign_target,
        business_domain=business_domain,
        analysis_json=analysis_result
    )

    print("\n--- Executing Stage 2: Recommendations ---")
    recommendation_result: Dict[str, Any] = client.generate_json(recommendation_messages, response_format=RecommendationResponse)
    
    print("\n=== Stage 2 LLM JSON Response (Recommendations) ===\n")
    print(json.dumps(recommendation_result, ensure_ascii=False, indent=2))
    
    # Optional: save messages to file for debugging / inspection
    with open("data/outputs/recommendations.json", "w", encoding="utf-8") as f:
        json.dump(recommendation_result, f, ensure_ascii=False, indent=2)
    
    return recommendation_result

if __name__ == "__main__":
    main()