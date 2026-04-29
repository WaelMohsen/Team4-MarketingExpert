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
        business_domain: Dict[str, Any],
        campaign_target: Dict[str, Any],
        goal_instructions: str = "",
        strict: bool = True,
    ) -> List[Dict[str, str]]:
        system_prompt_template = self.loader.load_prompt_text(sysPromptPath)
        user_prompt_template = self.loader.load_prompt_text(userPromptPath)

        system_prompt = system_prompt_template.replace("{{GOAL_INSTRUCTIONS}}", goal_instructions)

        campaign_data_json = self._to_json(campaign_data)
        business_domain_json = self._to_json(business_domain)
        campaign_target_json = self._to_json(campaign_target)
        
        user_prompt = (
            user_prompt_template.replace("{{CAMPAIGN_DATA}}", campaign_data_json)
            .replace("{{BUSINESS_DOMAIN}}", business_domain_json)
            .replace("{{CAMPAIGN_TARGET}}", campaign_target_json)
        )

        if strict:
            required = ["{{CAMPAIGN_DATA}}", "{{BUSINESS_DOMAIN}}", "{{CAMPAIGN_TARGET}}"]
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
        campaign_data: Dict[str, Any],
        analysis_json: Dict[str, Any],
        goal_instructions: str = "",
        strict: bool = True,
    ) -> List[Dict[str, str]]:
        system_prompt_template = self.loader.load_prompt_text(sysPromptPath)
        user_prompt_template = self.loader.load_prompt_text(userPromptPath)

        system_prompt = system_prompt_template.replace("{{GOAL_INSTRUCTIONS}}", goal_instructions)

        campaign_target_json = self._to_json(campaign_target)
        business_domain_json = self._to_json(business_domain)
        campaign_data_json = self._to_json(campaign_data)
        analysis_json_str = self._to_json(analysis_json)
        
        user_prompt = (
            user_prompt_template.replace("{{CAMPAIGN_TARGET}}", campaign_target_json)
            .replace("{{BUSINESS_DOMAIN}}", business_domain_json)
            .replace("{{CAMPAIGN_DATA}}", campaign_data_json)
            .replace("{{ANALYSIS_JSON}}", analysis_json_str)
        )

        if strict:
            required = ["{{CAMPAIGN_TARGET}}", "{{BUSINESS_DOMAIN}}", "{{CAMPAIGN_DATA}}", "{{ANALYSIS_JSON}}"]
            still_present = [tok for tok in required if tok in user_prompt]
            if still_present:
                raise ValueError("User prompt still contains unreplaced placeholder(s): " + ", ".join(still_present))

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    def build_analysis_evaluation_prompt(
        self,
        sysPromptPath: str = PromptRegistry.EVAL_ANALYSIS_SYSTEM.value,
        userPromptPath: str = PromptRegistry.EVAL_ANALYSIS_USER.value,
        *,
        campaign_data: Dict[str, Any],
        analysis_report: Dict[str, Any],
        campaign_target: Dict[str, Any],
        business_domain: Dict[str, Any],
        strict: bool = True,
    ) -> List[Dict[str, str]]:
        system_prompt = self.loader.load_prompt_text(sysPromptPath)
        user_prompt_template = self.loader.load_prompt_text(userPromptPath)

        campaign_context = {
            "target": campaign_target,
            "business_domain": business_domain
        }
        
        user_prompt = (
            user_prompt_template.replace("{{CAMPAIGN_CONTEXT}}", self._to_json(campaign_context))
            .replace("{{RAW_DATA}}", self._to_json(campaign_data))
            .replace("{{ANALYSIS_REPORT}}", self._to_json(analysis_report))
        )

        if strict:
            required = ["{{CAMPAIGN_CONTEXT}}", "{{RAW_DATA}}", "{{ANALYSIS_REPORT}}"]
            still_present = [tok for tok in required if tok in user_prompt]
            if still_present:
                raise ValueError("User prompt still contains unreplaced placeholder(s): " + ", ".join(still_present))

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def build_recommendation_evaluation_prompt(
        self,
        sysPromptPath: str = PromptRegistry.EVAL_RECOMMENDATION_SYSTEM.value,
        userPromptPath: str = PromptRegistry.EVAL_RECOMMENDATION_USER.value,
        *,
        business_domain: Dict[str, Any],
        campaign_target: Dict[str, Any],
        campaign_data: Dict[str, Any],
        analysis_context: Dict[str, Any],
        recommendation: Dict[str, Any],
        strict: bool = True,
    ) -> List[Dict[str, str]]:
        system_prompt = self.loader.load_prompt_text(sysPromptPath)
        user_prompt_template = self.loader.load_prompt_text(userPromptPath)

        business_context = {
            "business_domain": business_domain,
            "campaign_target": campaign_target
        }
        
        user_prompt = (
            user_prompt_template.replace("{{BUSINESS_CONTEXT}}", self._to_json(business_context))
            .replace("{{RAW_DATA}}", self._to_json(campaign_data))
            .replace("{{ANALYSIS_CONTEXT}}", self._to_json(analysis_context))
            .replace("{{RECOMMENDATION}}", self._to_json(recommendation))
        )

        if strict:
            required = ["{{BUSINESS_CONTEXT}}", "{{RAW_DATA}}", "{{ANALYSIS_CONTEXT}}", "{{RECOMMENDATION}}"]
            still_present = [tok for tok in required if tok in user_prompt]
            if still_present:
                raise ValueError("User prompt still contains unreplaced placeholder(s): " + ", ".join(still_present))

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    #--------------------------------------------------
    # Helper methods
    #--------------------------------------------------
    @staticmethod
    def _to_json(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, default=str, indent=2)
