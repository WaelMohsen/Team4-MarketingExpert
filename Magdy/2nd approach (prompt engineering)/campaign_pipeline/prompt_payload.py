from __future__ import annotations

from typing import Any, Dict, List

from data_model import PlatformMetricsList


def build_prompt_payload(
    campaign_target: Dict[str, Any],
    business_domain: Dict[str, Any],
    platform_metrics: PlatformMetricsList,
) -> Dict[str, Any]:
    """
    Build the INPUT JSON payload matching the schema defined in the prompt.
    """
    platforms: List[Dict[str, Any]] = [pm.to_dict() for pm in platform_metrics]

    return {
        "campaign_target": {
            "primary_goal": campaign_target.get("primary_goal"),
            "kpis": campaign_target.get("kpis", []),
        },
        "business_domain": {
            "industry": business_domain.get("industry"),
            "offering": business_domain.get("offering"),
            "audience": business_domain.get("audience"),
            "funnel_stage": business_domain.get("funnel_stage"),
        },
        "campaign_platforms_data": platforms,
    }

