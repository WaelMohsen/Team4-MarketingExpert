from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Union

import pandas as pd

from data_model import Metrics, PlatformMetrics, PlatformMetricsList


RowLike = Mapping[str, Any]
InputLike = Union[pd.DataFrame, Sequence[RowLike]]


def compute_roas(spend: Optional[float], revenue: Optional[float]) -> Optional[float]:
    if spend is None or revenue is None:
        return None
    if spend <= 0:
        return None
    try:
        return float(revenue) / float(spend)
    except ZeroDivisionError:
        return None


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    if "cost" in df.columns and "spend" not in df.columns:
        df = df.rename(columns={"cost": "spend"})
    return df


def _to_dataframe(data: InputLike) -> pd.DataFrame:
    if isinstance(data, pd.DataFrame):
        return _normalise_columns(data)
    if isinstance(data, Iterable):
        df = pd.DataFrame(list(data))
        return _normalise_columns(df)
    raise TypeError("Unsupported input type for campaign data")


def build_platform_metrics(data: InputLike) -> PlatformMetricsList:
    df = _to_dataframe(data)

    required_cols = {"platform"}
    missing_required = required_cols - set(df.columns)
    if missing_required:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing_required))}")

    metric_cols = [
        "spend",
        "impressions",
        "clicks",
        "conversions",
        "revenue",
    ]

    group_cols = ["platform"]
    if "objective" in df.columns:
        group_cols.append("objective")

    agg_spec: Dict[str, str] = {}
    for col in metric_cols:
        if col in df.columns:
            agg_spec[col] = "sum"

    if not agg_spec:
        grouped = df.drop_duplicates(subset=group_cols)
    else:
        grouped = df.groupby(group_cols, as_index=False).agg(agg_spec)

    results: List[PlatformMetrics] = []
    for _, row in grouped.iterrows():
        platform = str(row["platform"])
        objective = str(row["objective"]) if "objective" in row and pd.notna(row["objective"]) else None

        spend_val = float(row["spend"]) if "spend" in row and pd.notna(row["spend"]) else None
        revenue_val = float(row["revenue"]) if "revenue" in row and pd.notna(row["revenue"]) else None

        metrics_kwargs: Dict[str, Optional[float]] = {}
        for col in metric_cols:
            if col in row and pd.notna(row[col]):
                metrics_kwargs[col] = float(row[col])
            else:
                metrics_kwargs[col] = None

        metrics_kwargs["roas"] = compute_roas(spend_val, revenue_val)

        metrics = Metrics(**metrics_kwargs)
        results.append(
            PlatformMetrics(
                platform=platform,
                objective=objective,
                metrics=metrics,
            )
        )

    return results

