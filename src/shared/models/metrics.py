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
            "aov": self._calculate_aov,  # Average Order Value
            "brand_awareness_metric": lambda df: self._calculate_brand_awareness_metric(df, "cpm"),  # Example for brand awareness metric
            "revenue_efficiency_metric": lambda df: self._calculate_revenue_efficiency_metric(df, "mer"),  # Example for revenue efficiency metric  
            "increase_sales_metric": lambda df: self.calculate_increase_sales_metric(df, "roas"),  # Example for increase sales metric
            "traffic_metric": lambda df: self.calculate_traffic_metric(df, "ctr"),
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
    

    def _calculate_brand_awareness_metric(self, df: pd.DataFrame, metric_name: str) -> Optional[pd.Series]:
        """
        Calculate brand awareness metrics.

        Formulas:
        - reach       : unique users reached (direct column)
        - impressions : total ad views (direct column)
        - cpm         : (spend / impressions) * 1000
        - frequency   : impressions / reach
        """
        if metric_name == "reach":
            return df.get("reach")
        elif metric_name == "impressions":
            return df.get("impressions")
        elif metric_name == "cpm":
            return self._safe_div(df.get("spend"), df.get("impressions")) * 1000
        elif metric_name == "frequency":
            return self._safe_div(df.get("impressions"), df.get("reach"))
        else:
            return None
        
    def _calculate_revenue_efficiency_metric(self, df: pd.DataFrame, metric_name: str) -> Optional[pd.Series]:
        """
        Calculate revenue efficiency metrics.

        Formulas:
        - mer                : total_revenue / total_marketing_spend
        - ltv_to_cac         : lifetime_value / cac
        - cac_payback_period : cac / monthly_gross_profit_per_customer
        - roas               : revenue / spend
        - aov                : revenue / orders
        - refund_rate        : refunds / orders
        """
        if metric_name == "mer":
            return self._safe_div(df.get("total_revenue"), df.get("total_marketing_spend"))
        elif metric_name == "ltv_to_cac":
            return self._safe_div(df.get("lifetime_value"), df.get("cac"))
        elif metric_name == "cac_payback_period":
            return self._safe_div(df.get("cac"), df.get("monthly_gross_profit_per_customer"))
        elif metric_name == "roas":
            return self._safe_div(df.get("revenue"), df.get("spend"))
        elif metric_name == "aov":
            return self._safe_div(df.get("revenue"), df.get("orders"))
        elif metric_name == "refund_rate":
            return self._safe_div(df.get("refunds"), df.get("orders"))
        else:
            return None
    def calculate_increase_sales_metric(self, df: pd.DataFrame, metric_name: str) -> Optional[pd.Series]:
        """
        Calculate increase sales metrics.

        Formulas:
        - purchases                 : total completed purchases (direct column)
        - roas                      : revenue / spend
        - cpa                       : spend / conversions
        - revenue                   : sum of purchase value (direct column)
        - purchase_conversion_rate  : (purchases / landing_page_views) * 100
        - ctr                       : (clicks / impressions) * 100
        - cpc                       : spend / clicks
        - aov                       : revenue / orders
        """
        if metric_name == "purchases":
            return df.get("purchases")
        elif metric_name == "roas":
            return self._safe_div(df.get("revenue"), df.get("spend"))
        elif metric_name == "cpa":
            return self._safe_div(df.get("spend"), df.get("conversions"))
        elif metric_name == "revenue":
            return df.get("revenue")
        elif metric_name == "purchase_conversion_rate":
            return self._safe_div(df.get("purchases"), df.get("landing_page_views")) * 100
        elif metric_name == "ctr":
            return self._safe_div(df.get("clicks"), df.get("impressions")) * 100
        elif metric_name == "cpc":
            return self._safe_div(df.get("spend"), df.get("clicks"))
        elif metric_name == "aov":
            return self._safe_div(df.get("revenue"), df.get("orders"))
        else:
            return None
    def calculate_traffic_metric(self, df: pd.DataFrame, metric_name: str) -> Optional[pd.Series]:
        """
        Calculate traffic metrics.

        Formulas:
        - clicks                : total clicks (direct column)
        - ctr                   : (clicks / impressions) * 100
        - cpc                   : spend / clicks
        - landing_page_views    : total LPVs (direct column)
        - cpm                   : (spend / impressions) * 1000
        - bounce_proxy_rate     : 1 - (landing_page_views / clicks)
        - session_quality_score : landing_page_views / sessions
        """
        if metric_name == "clicks":
            return df.get("clicks")
        elif metric_name == "ctr":
            return self._safe_div(df.get("clicks"), df.get("impressions")) * 100
        elif metric_name == "cpc":
            return self._safe_div(df.get("spend"), df.get("clicks"))
        elif metric_name == "landing_page_views":
            return df.get("landing_page_views")
        elif metric_name == "cpm":
            return self._safe_div(df.get("spend"), df.get("impressions")) * 1000
        elif metric_name == "bounce_proxy_rate":
            return 1 - self._safe_div(df.get("landing_page_views"), df.get("clicks"))
        elif metric_name == "session_quality_score":
            return self._safe_div(df.get("landing_page_views"), df.get("sessions"))
        else:
            return None
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