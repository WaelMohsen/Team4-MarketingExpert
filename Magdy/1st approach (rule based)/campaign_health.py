"""
Campaign Health Score & Recommendation Pipeline
Steps 1–10: Validate → Percentiles → Trends → Confidence → Health → State → Diagnostics → Actions → Output
"""
import pandas as pd
import numpy as np


# --- STEP 1: Load & Validate Data ---
def validate_and_recompute(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure no negatives, no div-by-zero; recompute ROAS, CVR, CTR, CPA from base fields."""
    df = df.copy()
    # Clamp base metrics to non-negative
    for col in ["impressions_30d", "clicks_30d", "conversions_30d", "cost_30d", "revenue_30d"]:
        if col in df.columns:
            df[col] = df[col].clip(lower=0)
    # Recompute from base fields (avoid division by zero)
    safe_cost = df["cost_30d"].replace(0, np.nan)
    safe_clicks = df["clicks_30d"].replace(0, np.nan)
    safe_impressions = df["impressions_30d"].replace(0, np.nan)
    safe_conversions = df["conversions_30d"].replace(0, np.nan)
    df["roas_30d"] = (df["revenue_30d"] / safe_cost).fillna(0)
    df["cvr_30d"] = (df["conversions_30d"] / safe_clicks).fillna(0)
    df["ctr_30d"] = (df["clicks_30d"] / safe_impressions).fillna(0)
    df["cpa_30d"] = (df["cost_30d"] / safe_conversions).fillna(0)
    # AOV: revenue / conversions
    df["aov_30d"] = (df["revenue_30d"] / safe_conversions).fillna(0)
    return df


# --- STEP 2: Percentiles ---
def add_percentiles(df: pd.DataFrame) -> pd.DataFrame:
    """roas_p, cvr_p, cpa_p, aov_p, ctr_p, qs_p (CPA inverted in health formula)."""
    df = df.copy()
    df["roas_p"] = df["roas_30d"].rank(pct=True)
    df["cvr_p"] = df["cvr_30d"].rank(pct=True)
    df["cpa_p"] = df["cpa_30d"].rank(pct=True)
    df["aov_p"] = df["aov_30d"].rank(pct=True)
    df["ctr_p"] = df["ctr_30d"].rank(pct=True)
    df["qs_p"] = df["quality_score"].rank(pct=True)
    return df


# --- STEP 3: Trend signals ---
def add_trends(df: pd.DataFrame, low: float = 0.5, high: float = 1.5) -> pd.DataFrame:
    """roas_trend, conversion_trend, spend_trend; clip between low and high."""
    df = df.copy()
    safe_roas_30 = df["roas_30d"].replace(0, np.nan)
    df["roas_trend"] = (df["roas_7d"] / safe_roas_30).fillna(1).clip(low, high)
    # Conversion trend: (conv_7d/7) / (conv_30d/30) = conv_7d*30/(7*conv_30d)
    safe_conv_30 = df["conversions_30d"].replace(0, np.nan)
    conv_trend = (df["conversions_7d"] * 30 / (7 * safe_conv_30)).fillna(1).clip(low, high)
    df["conversion_trend"] = conv_trend
    safe_cost_30 = df["cost_30d"].replace(0, np.nan)
    spend_trend = (df["cost_7d"] * 30 / (7 * safe_cost_30)).fillna(1).clip(low, high)
    df["spend_trend"] = spend_trend
    return df


# --- STEP 4: Confidence ---
def add_confidence(df: pd.DataFrame, cap_at: float = 30) -> pd.DataFrame:
    """confidence = min(1, conversions_30d / cap_at)."""
    df = df.copy()
    df["confidence"] = np.minimum(1, df["conversions_30d"] / cap_at)
    return df


# --- STEP 5: Health score ---
def add_health_scores(df: pd.DataFrame) -> pd.DataFrame:
    """HealthScore then AdjustedScore = Health * (0.9 + 0.2*roas_trend), scale 0-100."""
    df = df.copy()
    health = (
        0.40 * df["roas_p"]
        + 0.20 * df["cvr_p"]
        + 0.15 * (1 - df["cpa_p"])
        + 0.10 * df["aov_p"]
        + 0.10 * df["ctr_p"]
        + 0.05 * df["qs_p"]
    )
    df["health_score"] = health * 100
    df["adjusted_health_score"] = (health * (0.9 + 0.2 * df["roas_trend"])).clip(0, 1) * 100
    return df


# --- STEP 6: Campaign state ---
def add_campaign_state(df: pd.DataFrame) -> pd.DataFrame:
    """Scale: >75; Optimize: 50-75; Fix: <50."""
    df = df.copy()
    def state(adj):
        if adj > 75:
            return "Scale"
        if adj >= 50:
            return "Optimize"
        return "Fix"
    df["campaign_state"] = df["adjusted_health_score"].map(state)
    return df


# --- STEP 7: Diagnostic signals ---
def add_diagnostic_signals(df: pd.DataFrame, budget_util_threshold: float = 0.8) -> pd.DataFrame:
    """Scaling, Efficiency, Creative, Landing Page signals."""
    df = df.copy()
    budget_util = (df["cost_30d"] / df["budget"].replace(0, np.nan)).fillna(0).clip(upper=1)
    df["budget_utilization"] = budget_util
    df["scaling_signal"] = (
        (df["roas_p"] > 0.7) & (df["roas_trend"] > 1.05) & (budget_util >= budget_util_threshold)
    )
    df["efficiency_problem_signal"] = (df["roas_p"] < 0.4) & (df["cpa_p"] > 0.6) & (df["cvr_p"] < 0.4)
    df["creative_problem_signal"] = (df["ctr_p"] < 0.3) & (df["impressions_30d"].rank(pct=True) > 0.5)
    df["landing_page_signal"] = (df["ctr_p"] > 0.6) & (df["cvr_p"] < 0.4)
    return df


# --- STEP 8: Action scoring ---
ACTION_DEFS = [
    {
        "id": "increase_budget",
        "name": "Increase Budget",
        "score_expr": lambda d: d["roas_p"] * 0.5 + np.clip(d["roas_trend"], 0, 2) * 0.3 + d["confidence"] * 0.2,
        "eligible": lambda d: d["roas_p"] > 0.6,
    },
    {
        "id": "improve_ad_copy",
        "name": "Improve Ad Copy",
        "score_expr": lambda d: (1 - d["ctr_p"]) * 0.6 + d["impressions_p"] * 0.4,
        "eligible": lambda d: True,
    },
    {
        "id": "improve_landing_page",
        "name": "Improve Landing Page",
        "score_expr": lambda d: (1 - d["cvr_p"]) * 0.6 + d["ctr_p"] * 0.4,
        "eligible": lambda d: True,
    },
    {
        "id": "reduce_budget_or_pause",
        "name": "Reduce Budget / Pause",
        "score_expr": lambda d: (1 - d["roas_p"]) * 0.5 + (1 - d["cvr_p"]) * 0.3 + (1 - d["confidence"]) * 0.2,
        "eligible": lambda d: d["roas_p"] < 0.4,
    },
    {
        "id": "optimize_bidding",
        "name": "Optimize Bidding",
        "score_expr": lambda d: (1 - d["cpa_p"]) * 0.4 + d["roas_p"] * 0.3 + d["confidence"] * 0.3,
        "eligible": lambda d: True,
    },
    {
        "id": "scale_campaign",
        "name": "Scale Campaign",
        "score_expr": lambda d: d["roas_p"] * 0.4 + d["roas_trend"] * 0.3 + d["scaling_signal"].astype(float) * 0.3,
        "eligible": lambda d: d["adjusted_health_score"] > 70,
    },
    {
        "id": "fix_creative_and_landing",
        "name": "Fix Creative & Landing",
        "score_expr": lambda d: (1 - d["ctr_p"]) * 0.5 + (1 - d["cvr_p"]) * 0.5,
        "eligible": lambda d: d["creative_problem_signal"] | d["landing_page_signal"],
    },
]


def add_action_scores_and_top_actions(df: pd.DataFrame, top_n: int = 3) -> pd.DataFrame:
    """Score each action, rank, and attach top_n action names per campaign."""
    df = df.copy()
    if "impressions_p" not in df.columns:
        df["impressions_p"] = df["impressions_30d"].rank(pct=True)
    action_scores = {}
    for adef in ACTION_DEFS:
        eligible = adef["eligible"](df)
        score = adef["score_expr"](df)
        action_scores[adef["id"]] = np.where(eligible, score, -1)
    score_df = pd.DataFrame(action_scores, index=df.index)
    # Top N action names per row
    top_actions = score_df.apply(
        lambda row: list(
            row[row >= 0].sort_values(ascending=False).head(top_n).index
        ),
        axis=1
    )
    action_names = {adef["id"]: adef["name"] for adef in ACTION_DEFS}
    df["top_action_ids"] = top_actions
    df["top_actions"] = top_actions.map(lambda ids: [action_names.get(i, i) for i in ids])
    for i in range(top_n):
        df[f"top_action_{i+1}"] = df["top_actions"].str[i]
    return df


# --- STEP 9: Final output table ---
def build_final_table(df: pd.DataFrame) -> pd.DataFrame:
    """| Campaign | Health | Trend | Confidence | State | Top Action 1 | Top Action 2 | Top Action 3 |"""
    cols = [
        "campaign_name",
        "adjusted_health_score",
        "roas_trend",
        "confidence",
        "campaign_state",
        "top_action_1",
        "top_action_2",
        "top_action_3",
    ]
    return df[[c for c in cols if c in df.columns]].copy()


def run_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """Run steps 1–8 and return enriched dataframe; then use build_final_table for output."""
    df = validate_and_recompute(df)
    df = add_percentiles(df)
    df = add_trends(df)
    df = add_confidence(df)
    df = add_health_scores(df)
    df = add_campaign_state(df)
    df = add_diagnostic_signals(df)
    df = add_action_scores_and_top_actions(df, top_n=3)
    return df


def load_data(source: str = "global") -> pd.DataFrame:
    """Load dataset: 'global' -> global_ads_performance_dataset.csv, 'campaign' -> campaign_data.csv."""
    if source == "global":
        from data_loader import load_global_ads_data
        return load_global_ads_data()
    return pd.read_csv("campaign_data.csv")


if __name__ == "__main__":
    df = load_data("global")
    df = run_pipeline(df)
    final = build_final_table(df)
    print(final.head(10).to_string())
