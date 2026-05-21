import pandas as pd
from typing import Dict, Any
from src.shared.models.metrics import metrics_calculator


def build_platform_summary(df: pd.DataFrame, primary_goal: str = None) -> Dict[str, Any]:
    """
    Build a flat, high-density summary for a single campaign row.
    Includes identity, metrics, and metadata.
    """
    if df.empty:
        return {}

    # 0. Identify metrics to compute
    # Core standard metrics needed for the summary
    core_metrics = ["roas", "cpa", "cvr", "ctr", "cpc"]
    # Goal-specific metrics
    goal_metrics = metrics_calculator.get_goal_metric_names(primary_goal) if primary_goal else []
    
    # Combined list of metrics to calculate
    metrics_to_compute = list(set(core_metrics + goal_metrics))

    # 1. Compute only targeted KPIs
    df = metrics_calculator.compute_metrics(df, metrics_to_compute=metrics_to_compute)
    row = df.iloc[0]

    # 2. Identity & Metadata
    identity = {
        "platform": str(row.get("platform", "Unknown")),
        "campaign_name": str(row.get("campaign_name", "Unknown")),
        "date": str(row.get("date", "Unknown")),
        "industry": str(row.get("industry", "Unknown")),
        "offering": str(row.get("offering", "Unknown")),
        "audience": str(row.get("audience", "Unknown")),
        "funnel_stage": str(row.get("funnel_stage", "Unknown")),
        "primary_goal": primary_goal or str(row.get("primary_goal", "Unknown")),
    }

    # 3. Performance Metrics
    # Populate standard metrics dictionary
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
    
    # Add any additional goal-specific KPIs to the summary dictionary
    if primary_goal:
        goal_kpis = metrics_calculator.get_goal_metrics(row, primary_goal)
        metrics.update(goal_kpis)

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
