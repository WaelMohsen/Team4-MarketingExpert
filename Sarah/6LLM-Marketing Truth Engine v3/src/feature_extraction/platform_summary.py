import pandas as pd
from typing import Dict, Any


def build_platform_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Build a Marwa-style summary structure from an aggregated
    per-platform dataframe.

    Expected columns (if present):
      - platform
      - spend
      - conversion_value (used as revenue)
      - impressions
      - clicks
      - conversions

    Returns:
        {
            "platform_summary": [ { per-platform record }, ... ],
            "totals": {
                "total_spend": float,
                "total_revenue": float,
                "total_conversions": int,
                "total_clicks": int,
                "total_impressions": int,
                "overall_roas": float | None
            }
        }
    """
    if df.empty:
        return {"platform_summary": [], "totals": {}}

    records = []
    for _, row in df.iterrows():
        records.append(
            {
                "platform": str(row.get("platform")),
                "total_spend": _to_float(row.get("spend")),
                "total_revenue": _to_float(row.get("conversion_value")),
                "total_impressions": _to_int(row.get("impressions")),
                "total_clicks": _to_int(row.get("clicks")),
                "total_conversions": _to_int(row.get("conversions")),
                "platform_roas": _to_float(row.get("roas")),
                "platform_cac": _to_float(row.get("cpa")),
                "platform_cvr": _to_float(row.get("cvr")),
                "platform_ctr": _to_float(row.get("ctr")),
            }
        )

    totals = _build_totals(df)
    return {"platform_summary": records, "totals": totals}


def _build_totals(df: pd.DataFrame) -> Dict[str, Any]:
    spend_series = pd.to_numeric(df.get("spend", 0), errors="coerce").fillna(0.0)
    revenue_series = pd.to_numeric(
        df.get("conversion_value", 0), errors="coerce"
    ).fillna(0.0)
    impressions_series = pd.to_numeric(
        df.get("impressions", 0), errors="coerce"
    ).fillna(0.0)
    clicks_series = pd.to_numeric(df.get("clicks", 0), errors="coerce").fillna(0.0)
    conversions_series = pd.to_numeric(
        df.get("conversions", 0), errors="coerce"
    ).fillna(0.0)

    total_spend = float(spend_series.sum())
    total_revenue = float(revenue_series.sum())

    overall_roas = None
    if total_spend > 0:
        overall_roas = round(total_revenue / total_spend, 2)

    return {
        "total_spend": round(total_spend, 2),
        "total_revenue": round(total_revenue, 2),
        "total_conversions": int(conversions_series.sum()),
        "total_clicks": int(clicks_series.sum()),
        "total_impressions": int(impressions_series.sum()),
        "overall_roas": overall_roas,
    }


def _to_float(value) -> float | None:
    try:
        v = float(value)
        if v != v or v in (float("inf"), float("-inf")):
            return None
        return round(v, 2)
    except (TypeError, ValueError):
        return None


def _to_int(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

