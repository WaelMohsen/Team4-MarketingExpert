from __future__ import annotations

import pandas as pd

from campaign_pipeline.transform import compute_roas, build_platform_metrics
from campaign_pipeline.prompt_payload import build_prompt_payload


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"platform": "Google Ads", "objective": "Leads", "spend": 100.0, "revenue": 500.0},
            {"platform": "Google Ads", "objective": "Leads", "spend": 50.0, "revenue": 250.0},
        ]
    )


def test_compute_roas():
    assert compute_roas(100, 500) == 5.0
    assert compute_roas(0, 500) is None
    assert compute_roas(None, 500) is None
    assert compute_roas(100, None) is None


def test_build_platform_metrics_and_payload():
    df = _sample_df()
    platform_metrics = build_platform_metrics(df)
    assert len(platform_metrics) == 1
    pm = platform_metrics[0]
    assert pm.platform == "Google Ads"
    assert pm.metrics.roas == 5.0

    campaign_target = {
        "primary_goal": "increase qualified leads",
        "kpis": ["leads", "roas"],
    }
    business_domain = {
        "industry": "SaaS",
        "offering": "B2B software subscription",
        "audience": "Marketing decision-makers in mid-market companies",
        "funnel_stage": "conversion",
    }

    payload = build_prompt_payload(campaign_target, business_domain, platform_metrics)
    assert "campaign_target" in payload
    assert "business_domain" in payload
    assert "campaign_platforms_data" in payload
    assert len(payload["campaign_platforms_data"]) == 1

