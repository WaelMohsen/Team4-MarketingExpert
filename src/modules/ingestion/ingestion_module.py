import os
import pandas as pd
from src.core.base_module import BaseModule
from src.core.execution_context import ExecutionContext
from .loader import DataLoader
from src.shared.models.ads_schema import UnifiedAdsSchema

from src.shared.utils.observability import observe, update_current_observation

class IngestionModule(BaseModule):
    """
    Module for loading raw ads data and applying initial schema mapping.
    """

    def __init__(self, name: str = "Ingestion"):
        super().__init__(name)
        self.loader = DataLoader()
        self.schema = UnifiedAdsSchema()

    @observe(as_type="span", name="Ingestion")
    def run(self, context: ExecutionContext) -> ExecutionContext:
        source = context.get_metadata("input_csv")
        if not source:
            raise ValueError("Input CSV source not found in metadata.")

        # Load data
        context.raw_df = self.loader.load(source)
        
        # Canonicalize columns
        context.raw_df = self.schema.canonicalize_columns(context.raw_df)
        
        # Validate schema
        self.schema.validate_required(context.raw_df)

        update_current_observation(
            metadata={
                "source": str(source),
                "rows_loaded": str(len(context.raw_df)) if context.raw_df is not None else "0"
            }
        )
        
        return context

    def save(self, context: ExecutionContext):
        # Ingestion results are typically the raw_df in context, 
        # we might save a copy to CSV for audit
        output_dir = context.get_metadata("output_json_dir", "data/outputs/")
        audit_dir = os.path.join(output_dir, "audit")
        os.makedirs(audit_dir, exist_ok=True)
        
        if context.raw_df is not None:
            context.raw_df.to_csv(os.path.join(audit_dir, "ingested_data.csv"), index=False)
