from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src.data_preprocessing.ads_schema import UnifiedAdsSchema
from src.data_preprocessing.ads_preprocessor import AdsPreprocessor
from src.data_preprocessing.ads_preprocessing_pipeline import UnifiedAdsPipeline
from src.feature_extraction.platform_summary import build_platform_summary
from src.feature_extraction.health_scoring import add_health_scores
from src.LLMs_and_Prompts.prompt_loader import PromptLoader
from src.LLMs_and_Prompts.prompt_builder import PromptBuilder
from src.LLMs_and_Prompts.api_client import LLMApiClient


@dataclass
class TruthEngineConfig:
    data_path: Path
    provider: str = "openai"
    model: str = "gpt-5-mini"
    campaign_objective: str = "Leads"
    primary_goal: str = "increase qualified leads"
    kpis: List[str] = None
    industry: str = "Retail"
    offering: str = "Membership plan"
    audience: str = "People shopping for monthly essentials"
    funnel_stage: str = "conversion"

    def __post_init__(self) -> None:
        if self.kpis is None:
            self.kpis = ["leads", "cpl"]
        self.data_path = Path(self.data_path)


def run_truth_engine(config: TruthEngineConfig) -> Dict[str, Any]:
    """
    Unified entry point that mixes:
      - Sarah's preprocessing & prompt builder
      - Marwa-style platform summary/totals
      - Magdy-inspired health scoring
    """
    schema = UnifiedAdsSchema()
    preprocessor = AdsPreprocessor(schema=schema)
    pipeline = UnifiedAdsPipeline(preprocessor=preprocessor, schema=schema)

    # 1) Load, validate, aggregate, and compute KPIs as a DataFrame
    df = pipeline.transform_to_df(config.data_path)

    # 2) Compute health scores / campaign_state (Magdy-style)
    df_health = add_health_scores(df)

    # 3) Build Marwa-style platform summary / totals
    summary = build_platform_summary(df_health)

    # 4) Convert into campaign_platforms_data JSON for prompting (Sarah-style)
    campaign_platforms_data = preprocessor.convert_to_json(
        df_health, campaign_objective=config.campaign_objective
    )

    # 5) Build prompts
    loader = PromptLoader.from_module_dir()
    builder = PromptBuilder(loader=loader)

    campaign_target = {
        "primary_goal": config.primary_goal,
        "kpis": config.kpis,
    }
    business_domain = {
        "industry": config.industry,
        "offering": config.offering,
        "audience": config.audience,
        "funnel_stage": config.funnel_stage,
    }

    messages = builder.build_LLMs_prompt(
        sysPromptPath="prompt_system.txt",
        userPromptPath="prompt_user.txt",
        campaign_target=campaign_target,
        business_domain=business_domain,
        campaign_platforms_data=campaign_platforms_data,
    )

    # 6) Call the LLM (OpenAI-backed client; provider flag reserved for future use)
    if config.provider.lower() != "openai":
        raise ValueError(f"Unsupported provider '{config.provider}'. Only 'openai' is supported here.")

    client = LLMApiClient(model=config.model)
    result_json: Dict[str, Any] = client.generate_json(messages)

    return {
        "platform_summary": summary["platform_summary"],
        "totals": summary["totals"],
        "campaign_platforms_data": campaign_platforms_data,
        "llm_response": result_json,
        "messages": messages,
    }

