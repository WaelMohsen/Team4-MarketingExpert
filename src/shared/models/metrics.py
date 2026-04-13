import numpy as np
import pandas as pd
from typing import Dict, Optional, Callable, List


class MetricsCalculator:
    """
    Standardized calculator for marketing metrics and KPIs.
    Follows the Open/Closed principle by allowing registration of new metrics.
    """

    def __init__(self):
        # Default registry of metric functions
        # Each function takes a DataFrame and returns a Series or None
        self._registry: Dict[str, Callable[[pd.DataFrame], Optional[pd.Series]]] = {
            "ctr": self._calculate_ctr,
            "cpc": self._calculate_cpc,
            "cpm": self._calculate_cpm,
            "cvr": self._calculate_cvr,
            "cpa": self._calculate_cpa,
            "roas": self._calculate_roas,
            "aov": self._calculate_aov, # Average Order Value
        }

    def register_metric(self, name: str, func: Callable[[pd.DataFrame], Optional[pd.Series]]):
        """Register a new metric calculation function."""
        self._registry[name] = func

    def compute_all(self, df: pd.DataFrame, *, overwrite: bool = False) -> pd.DataFrame:
        """
        Compute all registered metrics and add them to the DataFrame.
        """
        df = df.copy()
        
        for name, func in self._registry.items():
            if overwrite or name not in df.columns:
                result = func(df)
                if result is not None:
                    df[name] = result
        
        return df

    # ---------- Metric Calculation Implementations ----------

    def _calculate_ctr(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """CTR = clicks / impressions"""
        return self._safe_div(df, "clicks", "impressions")

    def _calculate_cpc(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """CPC = spend / clicks"""
        return self._safe_div(df, "spend", "clicks")

    def _calculate_cpm(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """CPM = (spend / impressions) * 1000"""
        s = self._safe_div(df, "spend", "impressions")
        return s * 1000.0 if s is not None else None

    def _calculate_cvr(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """CVR = conversions / clicks"""
        return self._safe_div(df, "conversions", "clicks")

    def _calculate_cpa(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """CPA = spend / conversions"""
        return self._safe_div(df, "spend", "conversions")

    def _calculate_roas(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """ROAS = conversion_value / spend"""
        return self._safe_div(df, "conversion_value", "spend")

    def _calculate_aov(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """AOV = conversion_value / conversions"""
        return self._safe_div(df, "conversion_value", "conversions")

    # ---------- Helpers ----------

    @staticmethod
    def _safe_div(df: pd.DataFrame, numerator: str, denominator: str) -> Optional[pd.Series]:
        """
        Calculates numerator / denominator safely (vectorized).
        Returns None if columns are missing. Returns NaN for division by zero.
        """
        if numerator not in df.columns or denominator not in df.columns:
            return None
            
        n = pd.to_numeric(df[numerator], errors="coerce")
        d = pd.to_numeric(df[denominator], errors="coerce")
        
        # Protect against division by zero
        return n.divide(d.replace(0, np.nan))

# Global instance for easy access
metrics_calculator = MetricsCalculator()