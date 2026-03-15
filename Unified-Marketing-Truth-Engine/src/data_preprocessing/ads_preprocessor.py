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
            # No grouping keys → aggregate entire dataframe into a single row
            out = df.agg(agg_spec).to_frame().T.reset_index(drop=True)

        return out

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
                # Optional health metrics
                "health_score": self._num(row.get("health_score")),
            }

            payload: Dict[str, Union[str, Dict[str, Optional[float]]]] = {
                "platform": str(row.get("platform")),
                "objective": campaign_objective,
                "metrics": metrics,
            }

            # Optional categorical health information
            state = row.get("campaign_state")
            if isinstance(state, str) and state:
                payload["campaign_state"] = state

            for i in range(1, 4):
                col = f"top_action_{i}"
                if col in df.columns:
                    val = row.get(col)
                    if isinstance(val, str) and val:
                        payload[col] = val

            campaign_platforms_data.append(payload)

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
