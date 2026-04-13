import os
import json
import pandas as pd
from src.core.base_module import BaseModule
from src.core.execution_context import ExecutionContext
from .extractor import FeatureExtractor
from .platform_summary import build_platform_summary
from src.modules.preprocessing.preprocessor import Preprocessor
from src.shared.models.ads_schema import UnifiedAdsSchema

class EnrichmentModule(BaseModule):
    """
    Module for feature extraction and high-density campaign enrichment.
    Strictly handles individual campaign rows.
    """

    def __init__(self, name: str = "Enrichment"):
        super().__init__(name)
        self.schema = UnifiedAdsSchema()
        self.extractor = FeatureExtractor()

    def run(self, context: ExecutionContext) -> ExecutionContext:
        if context.processed_df is None:
            raise ValueError("Row data not found in context.")

        df = context.processed_df.copy()

        # 1. Build the flat identity and metrics summary
        base_summary = build_platform_summary(df)

        # 2. Extract advanced diagnostics
        features = self.extractor.extract(df)

        # 3. Merge into a unified, high-density campaign data object
        # We prioritize metrics from build_platform_summary but take diagnostics from features
        enriched_payload = {
            **base_summary,
            "automated_diagnostics": features.get("diagnostics", {})
        }

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
