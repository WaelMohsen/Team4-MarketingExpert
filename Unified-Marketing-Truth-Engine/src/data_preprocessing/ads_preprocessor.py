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
    DEFAULT_SUM_COLS = ["impressions", "clicks", "spend", "conversions", "conversion_value", "reach", "frequency"]

    def __init__(self, schema: UnifiedAdsSchema):
        self.schema = schema

    def enforce_types(self, df: pd.DataFrame,*, parse_dates: bool = True, fill_missing_metrics_with_zero: bool = True) -> pd.DataFrame:
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

        keys = [c for c in ["date", "platform", "account_id", "campaign_id", "adset_id", "ad_id"] if c in df.columns]
        if keys:
            return df.drop_duplicates(subset=keys, keep="last").reset_index(drop=True)

        return df.drop_duplicates(keep="last").reset_index(drop=True)

    def aggregate_single_campaign(
        self,
        df: pd.DataFrame,
        *,
        platform_col: str = "platform",
        group_by_date: bool = False,
        time_granularity: Optional[str] = None,  # e.g. "D", "W", "M" if you want per-day/per-week/per-month
        sum_cols: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Aggregates rows accurding to "platform" -> one row per platform
        time_granularity:
          - If provided and "date" exists, date is floored to that grain (e.g. "D","W","M")
        """
        df = df.copy()

        if sum_cols is None:
            sum_cols = [c for c in self.DEFAULT_SUM_COLS if c in df.columns]

        # Apply time-based aggregation to the date column
        if time_granularity and "date" in df.columns:
            if not pd.api.types.is_datetime64_any_dtype(df["date"]):
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df["date"] = df["date"].dt.to_period(time_granularity).dt.to_timestamp()

        if platform_col in df.columns:
            if group_by_date and "date" in df.columns:
                group_keys.append("date")
            group_keys = [c for c in ["platform"] if c in df.columns]

        #if not group_keys:
        #    raise ValueError("Cannot aggregate: no grouping keys found (need at least 'platform').")
       
        agg_spec = {c: "sum" for c in sum_cols}
        if group_keys:
            # Normal grouped aggregation
            out = df.groupby(group_keys, dropna=False, as_index=False).agg(agg_spec)
        else:
            # No platform column → aggregate entire dataframe into single row
            out = df.agg(agg_spec)
            out = out.to_frame().T  # convert Series → single-row DataFrame        
        return out    
    
    def convert_to_json(
        self,
        df: pd.DataFrame,
        *,
        campaign_objective: str = "Leads"
    ) -> List[Dict[str, Union[str, Dict[str, Optional[float]]]]]:
        """
        Convert aggregated platform DataFrame
        into the LLM-compatible `campaign_platforms_data` structure.

        Assumes:
        - One row per platform (after aggregation)
        - KPI columns may already exist (ctr, cpc, cvr, cpa, etc.)
        """

        df = df.copy()
        campaign_platforms_data: List[Dict] = []

        for _, row in df.iterrows():

            metrics = {
                "spend": self._num(row.get("spend")),
                "impressions": self._num(row.get("impressions")),
                "reach": self._num(row.get("reach")),
                "clicks": self._num(row.get("clicks")),
                "ctr": self._num(row.get("ctr")),
                "cpc": self._num(row.get("cpc")),
                "conversions": self._num(row.get("conversions")),
                "conversion_rate": self._num(row.get("cvr")),
                "cpa": self._num(row.get("cpa")),
                "revenue": self._num(row.get("conversion_value")),
                "roas": self._num(row.get("roas")),
                "leads": self._num(row.get("leads")),
                "cpl": self._num(row.get("cpl")),
                "video_views": self._num(row.get("video_views")),
                "engagements": self._num(row.get("engagements")),
            }

            campaign_platforms_data.append({
                "platform": str(row.get("platform")),
                "objective": campaign_objective,
                "metrics": metrics
            })

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