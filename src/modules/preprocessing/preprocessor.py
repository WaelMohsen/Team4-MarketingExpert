from typing import Dict, Optional, Union, List
import pandas as pd

from src.shared.models.ads_schema import UnifiedAdsSchema


class Preprocessor:
    """
    Standardized preprocessing logic for ads data.
    - Type enforcement
    - Missing-value handling
    - Duplicate removal
    - Aggregation
    """

    def __init__(self, schema: UnifiedAdsSchema):
        self.schema = schema

    def enforce_types(
        self,
        df: pd.DataFrame,
        *,
        parse_dates: bool = True,
        fill_missing_metrics_with_zero: bool = True,
    ) -> pd.DataFrame:
        """
        Ensures columns match the types defined in the schema.
        Input data is copied before modification.
        """
        df = df.copy()

        if parse_dates and "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

        # Convert all numeric columns defined in the schema
        for col in self.schema.numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        if fill_missing_metrics_with_zero:
            # Focus on critical metrics for analysis
            critical_metrics = ["impressions", "clicks", "spend", "conversions", "conversion_value"]
            for col in critical_metrics:
                if col in df.columns:
                    df[col] = df[col].fillna(0)

        return df

    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Removes duplicates based on campaign and temporal identity keys.
        """
        df = df.copy()

        # Prioritize unified identity keys
        keys = [
            c
            for c in ["date", "platform", "account_id", "campaign_id", "adset_id", "ad_id"]
            if c in df.columns
        ]
        
        if keys:
            return df.drop_duplicates(subset=keys, keep="last").reset_index(drop=True)

        return df.drop_duplicates(keep="last").reset_index(drop=True)

