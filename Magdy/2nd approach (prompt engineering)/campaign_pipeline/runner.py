from __future__ import annotations

from typing import Any, Dict, Sequence

import pandas as pd

from prompt_payload import build_prompt_payload
from transform import build_platform_metrics
from openai_client import call_groq_with_payload, call_openai_with_payload


def run_campaign_analysis(
    campaign_data: pd.DataFrame | Sequence[Dict[str, Any]],
    campaign_target: Dict[str, Any],
    business_domain: Dict[str, Any],
    provider: str = "groq",
    model: str | None = None,
) -> str:
    platform_metrics = build_platform_metrics(campaign_data)
    payload = build_prompt_payload(
        campaign_target=campaign_target,
        business_domain=business_domain,
        platform_metrics=platform_metrics,
    )

    provider_lower = provider.lower()
    if provider_lower == "groq":
        return call_groq_with_payload(payload, model=model)
    if provider_lower == "openai":
        return call_openai_with_payload(payload, model=model)

    raise ValueError(f"Unsupported provider: {provider}")

