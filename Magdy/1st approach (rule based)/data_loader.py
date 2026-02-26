"""
Load and normalize ad performance data for the campaign health pipeline.
Supports: global_ads_performance_dataset.csv — each row is one campaign (no grouping).
"""
import pandas as pd
import numpy as np

# Default path for the global dataset
GLOBAL_ADS_CSV = "global_ads_performance_dataset.csv"


def load_global_ads_data(
    path: str = GLOBAL_ADS_CSV,
    quality_score_default: float = 5.0,
    budget_ratio: float = 1.2,
) -> pd.DataFrame:
    """
    Load global_ads_performance_dataset.csv with one row = one campaign (no grouping).
    Returns pipeline-ready columns: campaign_id, campaign_name, impressions_30d, clicks_30d,
    conversions_30d, cost_30d, revenue_30d, quality_score, budget, roas_7d, conversions_7d, cost_7d.
    """
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"]).astype(str)

    # Each line is its own campaign: map CSV columns to pipeline names
    out = pd.DataFrame()
    out["impressions_30d"] = df["impressions"].values
    out["clicks_30d"] = df["clicks"].values
    out["conversions_30d"] = df["conversions"].values
    out["cost_30d"] = df["ad_spend"].values
    out["revenue_30d"] = df["revenue"].values

    # Single-day row: use same values for 7d so trend = 1 (no aggregation)
    out["cost_7d"] = out["cost_30d"].values
    out["conversions_7d"] = out["conversions_30d"].values
    safe_cost = np.where(out["cost_7d"] > 0, out["cost_7d"], np.nan)
    out["roas_7d"] = np.where(np.isfinite(safe_cost), out["revenue_30d"].values / safe_cost, 1.0)

    # Campaign id and name (one per row)
    out["campaign_id"] = np.arange(len(out))
    out["campaign_name"] = (
        df["platform"].astype(str) + "_"
        + df["campaign_type"].astype(str) + "_"
        + df["industry"].astype(str) + "_"
        + df["country"].astype(str) + "_"
        + df["date"].astype(str)
    )

    out["quality_score"] = quality_score_default
    out["budget"] = (out["cost_30d"] * budget_ratio).round(2)
    out["bidding_strategy"] = "Target ROAS"  # placeholder

    # Keep optional columns for filtering in app
    for col in ["platform", "campaign_type", "industry", "country", "date"]:
        if col in df.columns:
            out[col] = df[col].values

    return out
