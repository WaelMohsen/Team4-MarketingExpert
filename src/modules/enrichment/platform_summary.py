import pandas as pd
from typing import Dict, Any
from src.shared.models.metrics import metrics_calculator


def build_platform_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Build a flat, high-density summary for a single campaign row.
    Includes identity, metrics, and metadata.
    """
    if df.empty:
        return {}

    # Ensure all KPIs are computed
    df = metrics_calculator.compute_all(df)
    row = df.iloc[0]

    # 1. Identity & Metadata
    # We pull everything that isn't a core numeric metric to provide context
    identity = {
        "platform": str(row.get("platform", "Unknown")),
        "campaign_name": str(row.get("campaign_name", "Unknown")),
        "date": str(row.get("date", "Unknown")),
        "industry": str(row.get("industry", "Unknown")),
        "offering": str(row.get("offering", "Unknown")),
        "audience": str(row.get("audience", "Unknown")),
        "funnel_stage": str(row.get("funnel_stage", "Unknown")),
    }

    # 2. Performance Metrics
    metrics = {
        "spend": _round(row.get("spend")),
        "revenue": _round(row.get("conversion_value")),
        "impressions": _to_int(row.get("impressions")),
        "clicks": _to_int(row.get("clicks")),
        "conversions": _to_int(row.get("conversions")),
        "roas": _round(row.get("roas")),
        "cpa": _round(row.get("cpa")),
        "cvr": _round(row.get("cvr")),
        "ctr": _round(row.get("ctr")),
    }
    # if df.campaign_type== "Increase Sales":
    #     metrics.appeend(metrics_calculator.calculate_increase_sales_metric(df))
    # elif df.campaign_type== "Brand Awareness":
    #     metrics.appeend(metrics_calculator.calculate_brand_awareness_metric(df))
    # elif df.campaign_type== "Traffic":
    #     metrics.appeend(metrics_calculator.calculate_traffic_metric(df))    
    # elif df.campaign_type== "Revenue Efficiency":
    #     metrics.appeend(metrics_calculator.calculate_revenue_efficiency_metric(df))    
    
    # We can add more campaign-type specific metrics here as needed
    campaign_type = row.get("campaign_type")
    if campaign_type == "Increase Sales" :

        metrics.update(metrics_calculator.calculate_increase_sales_metric(row))
    elif campaign_type == "Brand Awareness":
        metrics.update(metrics_calculator.calculate_brand_awareness_metric(row))
    elif campaign_type == "Traffic":
        metrics.update(metrics_calculator.calculate_traffic_metric(row))
    elif campaign_type == "Revenue Efficiency":
        metrics.update(metrics_calculator.calculate_revenue_efficiency_metric(row))    

    return {
        "campaign_identity": identity,
        "performance_metrics": metrics
    }


def _round(value: Any, ndigits: int = 2) -> float | None:
    try:
        v = float(value)
        if v != v or v in (float("inf"), float("-inf")):
            return None
        return round(v, ndigits)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
