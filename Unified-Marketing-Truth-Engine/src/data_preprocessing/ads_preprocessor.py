from typing import Dict, Optional, Union, List
import pandas as pd

from .ads_schema import UnifiedAdsSchema


class AdsPreprocessor:
    """
    Preprocessing only:
    - map platform columns to unified columns
    - type enforcement
    - missing-value handling
    - duplicate removal
    """

    # Metrics that should be summed when aggregating
    DEFAULT_SUM_COLS = [
        "impressions",
        "clicks",
        "spend",
        "conversions",
        "conversion_value",
        "reach",
        "frequency",
    ]

    def __init__(self, schema: UnifiedAdsSchema):
        self.schema = schema

    def enforce_types(
        self,
        df: pd.DataFrame,
        *,
        parse_dates: bool = True,
        fill_missing_metrics_with_zero: bool = True,
    ) -> pd.DataFrame:
        df = df.copy()

        if parse_dates and "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

        for col in self.schema.numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        if fill_missing_metrics_with_zero:
            for col in ["impressions", "clicks", "spend", "conversions", "conversion_value"]:
                if col in df.columns:
                    df[col] = df[col].fillna(0)

        return df

    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        keys = [
            c
            for c in ["date", "platform", "account_id", "campaign_id", "adset_id", "ad_id"]
            if c in df.columns
        ]
        if keys:
            return df.drop_duplicates(subset=keys, keep="last").reset_index(drop=True)

        return df.drop_duplicates(keep="last").reset_index(drop=True)

    def aggregate_single_campaign(
        self,
        df: pd.DataFrame,
        *,
        platform_col: str = "platform",
        group_by_date: bool = False,
        time_granularity: Optional[str] = None,  # e.g. "D", "W", "M"
        sum_cols: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Aggregates rows according to platform (and optionally date)
        so that the result has one row per platform (and date, if enabled).
        """
        df = df.copy()

        if sum_cols is None:
            sum_cols = [c for c in self.DEFAULT_SUM_COLS if c in df.columns]

        # Apply time-based aggregation to the date column
        if time_granularity and "date" in df.columns:
            if not pd.api.types.is_datetime64_any_dtype(df["date"]):
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df["date"] = df["date"].dt.to_period(time_granularity).dt.to_timestamp()

        group_keys: List[str] = []
        if platform_col in df.columns:
            group_keys.append(platform_col)
        if group_by_date and "date" in df.columns:
            group_keys.append("date")

        agg_spec = {c: "sum" for c in sum_cols}
        if group_keys:
            out = (
                df.groupby(group_keys, dropna=False, as_index=False)
                .agg(agg_spec)
                .reset_index(drop=True)
            )
        else:
            # No platform column → aggregate entire dataframe into single row
            out = df.agg(agg_spec)
            out = out.to_frame().T  # convert Series → single-row DataFrame        
        return out    
    
    def _get_metric(self, row: pd.Series, *keys: str) -> Optional[float]:
        """Try to get a numeric value from row using multiple keys (case-insensitive)."""
        # Create a lowercase map of existing keys for matching
        row_keys_lower = {str(k).lower(): k for k in row.index}
        
        for key in keys:
            # Check exact match
            if key in row:
                return self._num(row[key])
            # Check case-insensitive match
            kl = key.lower()
            if kl in row_keys_lower:
                return self._num(row[row_keys_lower[kl]])
        return None

    def convert_to_json(
        self,
        df: pd.DataFrame,
        *,
        campaign_objective: str = "Leads",
    ) -> List[Dict[str, Union[str, Dict[str, Optional[float]]]]]:
        """
        Convert aggregated platform DataFrame into the LLM-compatible
        `campaign_platforms_data` structure.

        Assumes:
        - One row per platform (after aggregation)
        - KPI columns may already exist (ctr, cpc, cvr, cpa, etc.)
        - Optional health columns (health_score, campaign_state, top_action_1..3)
        """

        df = df.copy()
        campaign_platforms_data: List[Dict] = []

        # Define metric columns to exclude from top-level since they are in 'metrics'
        # These are matched case-insensitively later.
        metric_cols_base = {
            "spend", "impressions", "reach", "clicks", "ctr", "cpc", "conversions", 
            "cvr", "cpa", "conversion_value", "roas", "leads", "cpl", "video_views", 
            "engagements", "platform", "revenue"
        }

        for _, row in df.iterrows():
            metrics = {
                "spend": self._get_metric(row, "spend"),
                "impressions": self._get_metric(row, "impressions"),
                "reach": self._get_metric(row, "reach"),
                "clicks": self._get_metric(row, "clicks"),
                "ctr": self._get_metric(row, "ctr", "CTR"),
                "cpc": self._get_metric(row, "cpc", "CPC"),
                "conversions": self._get_metric(row, "conversions"),
                "conversion_rate": self._get_metric(row, "conversion_rate", "cvr", "CVR"),
                "cpa": self._get_metric(row, "cpa", "CPA"),
                "revenue": self._get_metric(row, "revenue", "conversion_value", "Revenue"),
                "roas": self._get_metric(row, "roas", "ROAS"),
                "leads": self._get_metric(row, "leads"),
                "cpl": self._get_metric(row, "cpl"),
                "video_views": self._get_metric(row, "video_views"),
                "engagements": self._get_metric(row, "engagements"),
            }

            campaign_data = {
                "platform": str(row.get("platform")),
                "objective": campaign_objective,
                "metrics": metrics
            }

            # Add any other additional metadata columns available in the row
            for col in df.columns:
                # Use case-insensitive check for exclusion
                if col.lower() not in metric_cols_base:
                    val = row.get(col)
                    campaign_data[col] = str(val) if pd.notna(val) else None

            campaign_platforms_data.append(campaign_data)

            # Optional categorical health information — attach to campaign_data before append
            state = row.get("campaign_state")
            if isinstance(state, str) and state:
                campaign_data["campaign_state"] = state

            for i in range(1, 4):
                col = f"top_action_{i}"
                if col in df.columns:
                    val = row.get(col)
                    if isinstance(val, str) and val:
                        campaign_data[col] = val

        return campaign_platforms_data

    @staticmethod
    def _num(value) -> Optional[float]:
        """
        Convert NaN to None and cast numeric values to float.
        """
        if pd.isna(value):
            return None
        try:
            return float(value)
        except Exception:
            return None