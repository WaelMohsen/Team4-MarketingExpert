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
        # Unified Registry: Core KPIs + Raw Data Columns
        self._registry: Dict[str, Callable[[pd.DataFrame], Optional[pd.Series]]] = {
            # --- Calculated KPIs ---
            "ctr": self._calculate_ctr,
            "cpc": self._calculate_cpc,
            "cpm": self._calculate_cpm,
            "cvr": self._calculate_cvr,
            "cpa": self._calculate_cpa,
            "roas": self._calculate_roas,
            "aov": self._calculate_aov,
            "frequency": self._calculate_frequency,
            "mer": self._calculate_mer,
            "ltv_to_cac": self._calculate_ltv_to_cac,
            "cac_payback_period": self._calculate_cac_payback_period,
            "refund_rate": self._calculate_refund_rate,
            "purchase_conversion_rate": self._calculate_purchase_conversion_rate,
            "bounce_proxy_rate": self._calculate_bounce_proxy_rate,
            "session_quality_score": self._calculate_session_quality_score,

            # --- Raw Data Columns (Standardized Getters) ---
            "spend": lambda df: df.get("spend"),
            "revenue": lambda df: df.get("revenue") if "revenue" in df.columns else df.get("conversion_value"),
            "conversion_value": lambda df: df.get("conversion_value"),
            "impressions": lambda df: df.get("impressions"),
            "clicks": lambda df: df.get("clicks"),
            "conversions": lambda df: df.get("conversions"),
            "purchases": lambda df: df.get("purchases"),
            "reach": lambda df: df.get("reach"),
            "frequency_raw": lambda df: df.get("frequency"),
            "landing_page_views": lambda df: df.get("landing_page_views"),
            "sessions": lambda df: df.get("sessions"),
        }

    def register_metric(self, name: str, func: Callable[[pd.DataFrame], Optional[pd.Series]]):
        """Register a new metric calculation function."""
        self._registry[name] = func

    def compute_metrics(self, df: pd.DataFrame, *, metrics_to_compute: List[str] = None, overwrite: bool = False) -> pd.DataFrame:
        """
        Compute registered metrics and add them to the DataFrame.
        If metrics_to_compute is provided, only those metrics will be calculated.
        """
        df = df.copy()
        
        # Determine which metrics to run
        target_metrics = metrics_to_compute if metrics_to_compute is not None else self._registry.keys()
        
        for name in target_metrics:
            func = self._registry.get(name)
            if not func:
                continue
                
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
    def _calculate_frequency(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """Frequency = impressions / reach"""
        return self._safe_div(df, "impressions", "reach")
    def _calculate_mer(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """MER = total_revenue / total_marketing_spend"""
        return self._safe_div(df, "total_revenue", "total_marketing_spend")
    def _calculate_ltv_to_cac(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """LTV to CAC = lifetime_value / cac"""
        return self._safe_div(df, "lifetime_value", "cac")
    def _calculate_cac_payback_period(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """CAC Payback Period = cac / monthly_gross_profit_per_customer"""
        return self._safe_div(df, "cac", "monthly_gross_profit_per_customer")
    def _calculate_refund_rate(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """Refund Rate = refunds / orders"""
        return self._safe_div(df, "refunds", "orders")
    def _calculate_purchase_conversion_rate(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """Purchase Conversion Rate = (purchases / landing_page_views) * 100"""
        return self._safe_div(df, "purchases", "landing_page_views") * 100 if self._safe_div(df, "purchases", "landing_page_views") is not None else None
    def _calculate_bounce_proxy_rate(self, df: pd.DataFrame) -> Optional[pd.Series]:  
        """Bounce Proxy Rate = 1 - (landing_page_views / clicks)"""
        return 1 - self._safe_div(df, "landing_page_views", "clicks") if self._safe_div(df, "landing_page_views", "clicks") is not None else None
    def _calculate_session_quality_score(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """Session Quality Score = landing_page_views / sessions"""
        return self._safe_div(df, "landing_page_views", "sessions") if self._safe_div(df, "landing_page_views", "sessions") is not None else None

    # Map primary goals to their specific KPI keys
    GOAL_MAP = {
        "Increase Sales": ["roas", "cpa", "cvr", "ctr", "cpc", "aov", "revenue", "purchases"],
        "Brand Awareness": ["cpm", "reach", "impressions", "frequency"],
        "Revenue Efficiency": ["mer", "ltv_to_cac", "cac_payback_period", "roas", "aov", "refund_rate"],
        "Traffic": ["clicks", "ctr", "cpc", "landing_page_views", "cpm", "bounce_proxy_rate", "session_quality_score"]
    }

    def get_goal_metrics(self, df: pd.DataFrame, goal: str) -> Dict[str, float]:
        """
        Returns a dictionary of all relevant metrics for a given goal.
        """
        relevant_keys = self.get_goal_metric_names(goal)
        results = {}
        
        # Determine if we are handling a Series (single row) or DataFrame
        is_series = isinstance(df, pd.Series)
        
        for key in relevant_keys:
            func = self._registry.get(key)
            if not func:
                continue
                
            # Execute calculation
            val = func(df if not is_series else pd.DataFrame([df]))
            
            # Extract value from Series if needed
            if isinstance(val, pd.Series):
                val = val.iloc[0] if not val.empty else None
            
            # Clean up NaN/None
            if val is not None and not (isinstance(val, (float, int)) and pd.isna(val)):
                results[key] = float(val)
                
        return results

    def get_goal_metric_names(self, goal: str) -> List[str]:
        """
        Returns the list of KPI names relevant to a given goal.
        """
        return self.GOAL_MAP.get(goal, [])

    # ---------- Helpers ----------

    @staticmethod
    def _safe_div(df: pd.DataFrame, numerator: str, denominator: str) -> Optional[pd.Series]:
        """
        Calculates numerator / denominator safely (vectorized).
        Returns None if columns are missing. Returns NaN for division by zero.
        """
        # Handle both DataFrame and Series
        if hasattr(df, "columns"):
            if numerator not in df.columns or denominator not in df.columns:
                return None
        else:
            if numerator not in df.index or denominator not in df.index:
                return None
            
        n = pd.to_numeric(df[numerator], errors="coerce")
        d = pd.to_numeric(df[denominator], errors="coerce")
        
        if hasattr(n, "divide"):
            # Vectorized case (DataFrame)
            return n.divide(d.replace(0, np.nan)).round(2)
        else:
            # Scalar case (Series/Row)
            if d == 0 or pd.isna(d) or pd.isna(n):
                return None
            return round(float(n / d), 2)

# Global instance for easy access
metrics_calculator = MetricsCalculator()