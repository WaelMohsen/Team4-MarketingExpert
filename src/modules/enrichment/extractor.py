from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, List
import numpy as np
import pandas as pd


@dataclass
class FeatureExtractor:
    """
    Extracts recommendation-focused features from a single unified ads row.
    Strictly granular: assumes it is processing one and only one record.
    """

    # Which column represents the "primary conversion"
    primary_conversion_col: str = "conversions"
    value_col: str = "conversion_value"

    def extract(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract features from a single-row DataFrame.
        """
        if df.empty:
            return {}

        row = df.iloc[0]
        
        # Totals
        impressions = float(row.get("impressions", 0.0))
        clicks = float(row.get("clicks", 0.0))
        spend = float(row.get("spend", 0.0))
        conv = float(row.get(self.primary_conversion_col, 0.0))
        value = float(row.get(self.value_col, 0.0))
        reach = row.get("reach", np.nan)
        freq = row.get("frequency", np.nan)

        # Derived metrics (safe division)
        cvr = conv / clicks if clicks > 0 else 0
        ctr = clicks / impressions if impressions > 0 else 0

        # Signals
        high_clicks_low_conv = (clicks >= 50) and (conv == 0)
        low_clicks_high_cvr = (clicks < 50) and (cvr >= 0.05)
        spend_no_results = (spend > 0) and (clicks == 0)

        # Fatigue signal
        fatigue_risk = None
        if isinstance(freq, (int, float)) and not np.isnan(freq):
            fatigue_risk = bool(freq >= 4)

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
                "ctr": round(float(ctr), 4),
                "cvr": round(float(cvr), 4)
            },
            "coverage": {
                "platform": str(row.get("platform", "Unknown")),
                "campaign_name": str(row.get("campaign_name", "Unknown")),
                "date": str(row.get("date", "Unknown"))
            },
            "available_fields": sorted(df.columns.tolist()),
        }