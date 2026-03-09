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
        "Data/raw/global_ads_performance_dataset.csv",
        compute_kpis=True,
        campaign_objective = "Leads"
    )
    
    #print(campaign_platforms_data)

    # --- Prompting layer ---
    loader = PromptLoader.from_module_dir()
    builder = PromptBuilder(loader=loader)
    
    # Load a prompt by passing its relative path manually
    promptPath = "Prompt 1.txt"
    prompt = loader.load_prompt_text(path = promptPath)

    # Load a prompt that is inside LLMs_and_Prompts 
    #prompt = loader.load_text("Prompt 1.txt")
    
    campaign_target={"primary_goal": "increase qualified leads",
                    "kpis": ["leads", "cpl"]}
    
    business_domain={
            "industry": "Retail",
            "offering": "Membership plan",
            "audience": "People shopping for monthly essentials",
            "funnel_stage": "conversion",
        }
    
    # IMPORTANT: this should return a list[{"role": "...", "content": "..."}]    
    messages = builder.build_LLMs_prompt(
        sysPromptPath="prompt_system.txt",
        userPromptPath="prompt_user.txt",
        campaign_target=campaign_target,
        business_domain=business_domain,
        campaign_platforms_data = campaign_platforms_data)
    
    # messages is what you send to your LLM api_client
    print("\n--- SYSTEM ---\n")
    #print(messages[0]["role"], messages[0]["content"][:])
    print("\n--- USER ---\n")
    #print(messages[1]["role"], messages[1]["content"][:])

    # Optional: save messages to file for debugging / inspection
    with open("Data/outputs/messages.json", "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

    # Call the LLM via api_client ---
    client = LLMApiClient(
        model="gpt-5-mini",
        #temperature=0.3,
        max_output_tokens=1200,
    )


    # If your prompt expects normal text output instead, use:
    # result_text = client.generate(messages)
    # print(result_text)


    # If your prompt expects JSON output:
    result: Dict[str, Any] = client.generate_json(messages)
    print("\n=== LLM JSON Response ===\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # If your prompt expects normal text output instead, use:
    # result_text = client.generate(messages)
    # print(result_text)

    
    return messages


    

if __name__ == "__main__":
    main()