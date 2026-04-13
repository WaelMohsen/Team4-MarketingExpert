import os
import pandas as pd
from src.core.base_module import BaseModule
from src.core.execution_context import ExecutionContext
from .preprocessor import Preprocessor
from src.shared.models.ads_schema import UnifiedAdsSchema
from src.shared.models.metrics import metrics_calculator

class PreprocessingModule(BaseModule):
    """
    Module for data cleaning, type enforcement, duplicate removal, 
    and basic metric calculation.
    """

    def __init__(self, name: str = "Preprocessing"):
        super().__init__(name)
        self.schema = UnifiedAdsSchema()
        self.preprocessor = Preprocessor(schema=self.schema)

    def run(self, context: ExecutionContext) -> ExecutionContext:
        if context.raw_df is None:
            raise ValueError("Raw DataFrame not found in context. Ensure IngestionModule ran first.")

        df = context.raw_df.copy()

        # Enforce types
        df = self.preprocessor.enforce_types(
            df,
            parse_dates=context.get_metadata("parse_dates", True),
            fill_missing_metrics_with_zero=context.get_metadata("fill_missing_metrics_with_zero", True),
        )

        # Remove duplicates
        if context.get_metadata("remove_duplicates", True):
            df = self.preprocessor.remove_duplicates(df)

        # Compute basic metrics
        if context.get_metadata("compute_kpis", True):
            df = metrics_calculator.compute_all(df)

        context.processed_df = df
        return context

    def save(self, context: ExecutionContext):
        output_dir = context.get_metadata("output_json_dir", "data/outputs/")
        audit_dir = os.path.join(output_dir, "audit")
        os.makedirs(audit_dir, exist_ok=True)
        
        if context.processed_df is not None:
            context.processed_df.to_csv(os.path.join(audit_dir, "processed_data.csv"), index=False)
