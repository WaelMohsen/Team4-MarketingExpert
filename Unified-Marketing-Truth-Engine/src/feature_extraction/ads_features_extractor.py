from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, List
import numpy as np
import pandas as pd


@dataclass
class AdsFeatureExtractor:
    """
    Extracts recommendation-focused features from a unified ads analytics DataFrame.

    Assumptions:
      - DataFrame columns are already unified (e.g., 'spend', 'clicks', 'impressions', etc.)
      - DataFrame can be at any grain (ad/adset/campaign/day). This class aggregates safely.

    Output:
      - A plain Python dict with totals, KPIs, and diagnostic signals suitable for rules/LLM prompting.
    """

    # Which column represents the "primary conversion" in your business context.
    # Example: "conversions" could mean purchases or registrations depending on mapping.
    primary_conversion_col: str = "conversions"

    # Optional: set if you want to interpret revenue/ROAS
    value_col: str = "conversion_value"

    def extract(
        self,
        df: pd.DataFrame,
        *,
        group_by: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Extract features from df.
        - If group_by is None: returns dataset-level features.
        - If group_by is provided (e.g. ["platform"] or ["campaign_name"]):
            returns {"groups": [ {group keys + features}, ... ], "overall": {...}}.
        """
        self._validate_minimum(df)

        if group_by:
            return {
                "overall": self._extract_one(df),
                "groups": self._extract_by_group(df, group_by),
            }

        return self._extract_one(df)

    # -------------------------
    # Core extraction
    # -------------------------
    def _extract_one(self, df: pd.DataFrame) -> Dict[str, Any]:
        dfa = self._aggregate(df)

        # Totals
        impressions = float(dfa.get("impressions", 0.0))
        clicks = float(dfa.get("clicks", 0.0))
        spend = float(dfa.get("spend", 0.0))
        conv = float(dfa.get(self.primary_conversion_col, 0.0))
        value = float(dfa.get(self.value_col, 0.0))
        reach = dfa.get("reach", np.nan)
        freq = dfa.get("frequency", np.nan)

        # Signals (for recommendations)
        # These help decide whether the problem is targeting/creative vs landing page/offer vs tracking.
        high_clicks_low_conv = (clicks >= 50) and (conv == 0)
        low_clicks_high_cvr = (clicks < 50) and (cvr is not None and cvr >= 0.05)
        spend_no_results = (spend > 0) and (clicks == 0)

        # Fatigue signal (if frequency exists)
        fatigue_risk = None
        if isinstance(freq, (int, float)) and not np.isnan(freq):
            fatigue_risk = bool(freq >= 4)

        # Coverage / data quality flags
        missing_core_cols = self._missing_core_columns(df)
        has_value_data = (self.value_col in df.columns) and (df[self.value_col].fillna(0).sum() > 0)

        # Simple time coverage
        date_min, date_max, n_days = self._date_coverage(df)

        return {
            "totals": {
                "impressions": impressions,
                "clicks": clicks,
                "spend": spend,
                self.primary_conversion_col: conv,
                self.value_col: value,
            },
            "diagnostics": {
                "high_clicks_low_conversions": high_clicks_low_conv,
                "low_clicks_high_cvr": low_clicks_high_cvr,
                "spend_with_zero_clicks": spend_no_results,
                "fatigue_risk": fatigue_risk,
            },
            "data_quality": {
                "missing_core_columns": missing_core_cols,
                "has_conversion_value": has_value_data,
            },
            "coverage": {
                "date_min": date_min,
                "date_max": date_max,
                "n_days": n_days,
                "row_count": int(len(df)),
                "unique_campaigns": int(df["campaign_name"].nunique()) if "campaign_name" in df.columns else None,
                "unique_platforms": int(df["platform"].nunique()) if "platform" in df.columns else None,
            },
            "available_fields": sorted(df.columns.tolist()),
        }

    def _extract_by_group(self, df: pd.DataFrame, group_by: List[str]) -> List[Dict[str, Any]]:
        missing = [g for g in group_by if g not in df.columns]
        if missing:
            raise ValueError(f"group_by columns not found in dataframe: {missing}")

        out: List[Dict[str, Any]] = []
        for keys, gdf in df.groupby(group_by, dropna=False):
            if not isinstance(keys, tuple):
                keys = (keys,)
            group_info = {group_by[i]: (None if pd.isna(keys[i]) else keys[i]) for i in range(len(group_by))}
            features = self._extract_one(gdf)
            out.append({**group_info, **features})
        return out

    # -------------------------
    # Helpers
    # -------------------------
    def _validate_minimum(self, df: pd.DataFrame) -> None:
        required = ["impressions", "clicks", "spend"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"DataFrame must have unified columns {required}. Missing: {missing}")

    def _aggregate(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Aggregates to a single row of totals / weighted values.
        For frequency: compute weighted average by impressions if possible.
        """
        agg: Dict[str, float] = {}

        for col in ["impressions", "clicks", "spend", self.primary_conversion_col, self.value_col, "reach"]:
            if col in df.columns:
                agg[col] = float(pd.to_numeric(df[col], errors="coerce").fillna(0).sum())
            else:
                agg[col] = 0.0

        # Frequency is not additive; use weighted average if available
        if "frequency" in df.columns:
            freq = pd.to_numeric(df["frequency"], errors="coerce")
            impr = pd.to_numeric(df.get("impressions", pd.Series([np.nan] * len(df))), errors="coerce")
            if freq.notna().any():
                if impr.notna().any() and impr.fillna(0).sum() > 0:
                    agg["frequency"] = float((freq.fillna(0) * impr.fillna(0)).sum() / impr.fillna(0).sum())
                else:
                    agg["frequency"] = float(freq.mean())
            else:
                agg["frequency"] = float("nan")
        else:
            agg["frequency"] = float("nan")

        return agg

    def _missing_core_columns(self, df: pd.DataFrame) -> List[str]:
        core = ["date", "platform", "campaign_name", "impressions", "clicks", "spend", self.primary_conversion_col]
        return [c for c in core if c not in df.columns]

    def _date_coverage(self, df: pd.DataFrame) -> (Optional[str], Optional[str], Optional[int]):
        if "date" not in df.columns:
            return None, None, None

        s = pd.to_datetime(df["date"], errors="coerce")
        s = s.dropna()
        if s.empty:
            return None, None, None

        dmin = s.min().date().isoformat()
        dmax = s.max().date().isoformat()
        n_days = int((s.max().date() - s.min().date()).days + 1)
        return dmin, dmax, n_days