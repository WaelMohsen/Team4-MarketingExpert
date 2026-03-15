from __future__ import annotations

from typing import Tuple

import numpy as np
import pandas as pd


def add_health_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add campaign/platform health scores inspired by Magdy's rule-based pipeline.

    This version works on the unified per-platform dataframe produced by
    UnifiedAdsPipeline and uses percentiles over:
      - roas
      - cvr (conversion_rate)
      - cpa
      - aov (conversion_value / conversions)
      - ctr
    """
    if df.empty:
        return df

    df = df.copy()

    # Ensure required base metrics exist (compute best-effort where missing)
    if "cvr" not in df.columns and {"conversions", "clicks"}.issubset(df.columns):
        df["cvr"] = _safe_div(df["conversions"], df["clicks"])
    if "cpa" not in df.columns and {"spend", "conversions"}.issubset(df.columns):
        df["cpa"] = _safe_div(df["spend"], df["conversions"])
    if "ctr" not in df.columns and {"clicks", "impressions"}.issubset(df.columns):
        df["ctr"] = _safe_div(df["clicks"], df["impressions"])
    if "roas" not in df.columns and {"conversion_value", "spend"}.issubset(df.columns):
        df["roas"] = _safe_div(df["conversion_value"], df["spend"])

    # AOV: revenue / conversions
    if {"conversion_value", "conversions"}.issubset(df.columns):
        df["aov"] = _safe_div(df["conversion_value"], df["conversions"])

    # Percentiles
    df["roas_p"] = df["roas"].rank(pct=True) if "roas" in df.columns else 0.5
    df["cvr_p"] = df["cvr"].rank(pct=True) if "cvr" in df.columns else 0.5
    df["cpa_p"] = df["cpa"].rank(pct=True) if "cpa" in df.columns else 0.5
    df["aov_p"] = df["aov"].rank(pct=True) if "aov" in df.columns else 0.5
    df["ctr_p"] = df["ctr"].rank(pct=True) if "ctr" in df.columns else 0.5

    # If a quality_score column exists, respect it; otherwise fall back to neutral 0.5
    if "quality_score" in df.columns:
        df["qs_p"] = df["quality_score"].rank(pct=True)
    else:
        df["qs_p"] = 0.5

    # Health score on 0–100 scale (weights adapted from Magdy's pipeline)
    health = (
        0.40 * df["roas_p"]
        + 0.20 * df["cvr_p"]
        + 0.15 * (1.0 - df["cpa_p"])
        + 0.10 * df["aov_p"]
        + 0.10 * df["ctr_p"]
        + 0.05 * df["qs_p"]
    )

    df["health_score"] = (health * 100).clip(0, 100)
    df["campaign_state"] = df["health_score"].map(_state_from_score)

    return df


def _safe_div(a: pd.Series, b: pd.Series) -> pd.Series:
    b0 = (b == 0) | b.isna()
    return np.where(b0, np.nan, a / b)


def _state_from_score(score: float) -> str:
    if score > 75:
        return "Scale"
    if score >= 50:
        return "Optimize"
    return "Fix"

