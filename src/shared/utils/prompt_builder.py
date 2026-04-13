from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Dict, List
import json
import pandas as pd

from .prompt_loader import PromptLoader
from .prompt_registry import PromptRegistry


@dataclass
class PromptBuilder:
    """
    Build runtime (system + user) messages by replacing placeholders in user template.
    """

    loader: PromptLoader

    def build_analysis_prompt(
        self,
        sysPromptPath: str = PromptRegistry.ANALYSIS_SYSTEM.value,
        userPromptPath: str = PromptRegistry.ANALYSIS_USER.value,
        *,
        campaign_data: Dict[str, Any],
        strict: bool = True,
    ) -> List[Dict[str, str]]:
        system_prompt = self.loader.load_prompt_text(sysPromptPath)
        user_prompt_template = self.loader.load_prompt_text(userPromptPath)

        campaign_data_json = self._to_json(campaign_data)
        user_prompt = user_prompt_template.replace("{{CAMPAIGN_DATA}}", campaign_data_json)
        user_prompt = user_prompt.replace("{{CAMPAIGN_PLATFORMS_DATA}}", campaign_data_json)

        if strict:
            required = ["{{CAMPAIGN_DATA}}"] if "{{CAMPAIGN_DATA}}" in user_prompt_template else []
            still_present = [tok for tok in required if tok in user_prompt]
            if still_present:
                raise ValueError("User prompt still contains unreplaced placeholder(s): " + ", ".join(still_present))

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def build_recommendation_prompt(
        self,
        sysPromptPath: str = PromptRegistry.RECOMMENDATION_SYSTEM.value,
        userPromptPath: str = PromptRegistry.RECOMMENDATION_USER.value,
        *,
        campaign_target: Dict[str, Any],
        business_domain: Dict[str, Any],
        analysis_json: Dict[str, Any],
        strict: bool = True,
    ) -> List[Dict[str, str]]:
        system_prompt = self.loader.load_prompt_text(sysPromptPath)
        user_prompt_template = self.loader.load_prompt_text(userPromptPath)

        campaign_target_json = self._to_json(campaign_target)
        business_domain_json = self._to_json(business_domain)
        analysis_json_str = self._to_json(analysis_json)
        
        user_prompt = (
            user_prompt_template.replace("{{CAMPAIGN_TARGET}}", campaign_target_json)
            .replace("{{BUSINESS_DOMAIN}}", business_domain_json)
            .replace("{{ANALYSIS_JSON}}", analysis_json_str)
        )

        if strict:
            required = ["{{CAMPAIGN_TARGET}}", "{{BUSINESS_DOMAIN}}", "{{ANALYSIS_JSON}}"]
            still_present = [tok for tok in required if tok in user_prompt]
            if still_present:
                raise ValueError("User prompt still contains unreplaced placeholder(s): " + ", ".join(still_present))

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    #--------------------------------------------------
    # Hepler methods
    #--------------------------------------------------
    @staticmethod
    def _to_json(value: Any) -> str:
        return  json.dumps(value, ensure_ascii=False, default=str, indent=2)
        #return json.dumps(value, ensure_ascii=False, default=str)
    
    
