import os
import json
import pandas as pd
from src.core.base_module import BaseModule
from src.core.execution_context import ExecutionContext
from .platform_summary import build_platform_summary
from src.modules.preprocessing.preprocessor import Preprocessor
from src.shared.models.ads_schema import UnifiedAdsSchema

from src.shared.utils.observability import observe, update_current_observation

class EnrichmentModule(BaseModule):
    """
    Module for feature extraction and high-density campaign enrichment.
    Strictly handles individual campaign rows.
    """

    def __init__(self, name: str = "Enrichment"):
        super().__init__(name)
        self.schema = UnifiedAdsSchema()

    @observe(as_type="span", name="Enrichment")
    def run(self, context: ExecutionContext) -> ExecutionContext:
        if context.processed_df is None:
            raise ValueError("Row data not found in context.")

        df = context.processed_df.copy()

        # 0. Retrieve primary_goal from context metadata
        campaign_target = context.get_metadata("campaign_target", {})
        primary_goal = campaign_target.get("primary_goal")

        # 1. Build the flat identity and metrics summary
        base_summary = build_platform_summary(df, primary_goal=primary_goal)

        # 2. Merge into a unified, high-density campaign data object
        enriched_payload = {
            **base_summary
        }

        update_current_observation(
            metadata={
                "primary_goal": str(primary_goal),
                "enriched_fields": str(list(enriched_payload.keys()))
            }
        )

        context.enriched_data = {
            "campaign_data": enriched_payload,
            "processed_df": df
        }
        
        return context

    def save(self, context: ExecutionContext):
        output_dir = context.runtime_output_path or os.path.join(context.get_metadata("output_json_dir", "data/outputs/"), "audit")
        os.makedirs(output_dir, exist_ok=True)
        
        if context.enriched_data:
            save_payload = context.enriched_data.get("campaign_data", {})
            
            with open(os.path.join(output_dir, "enriched_summary.json"), "w", encoding="utf-8") as f:
                json.dump(save_payload, f, ensure_ascii=False, indent=2, default=str)
            
            # Save the enriched tabular row too
            enriched_df = context.enriched_data.get("processed_df")
            if enriched_df is not None:
                enriched_df.to_csv(os.path.join(output_dir, "enriched_data.csv"), index=False)
