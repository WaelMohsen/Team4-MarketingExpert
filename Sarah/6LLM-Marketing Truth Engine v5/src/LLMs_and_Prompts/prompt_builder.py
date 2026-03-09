from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Dict, List
import json
import pandas as pd

from src.LLMs_and_Prompts import PromptLoader


@dataclass
class PromptBuilder:
    """
    Build runtime (system + user) messages by replacing placeholders in user template.
    """

    loader: PromptLoader

    def build_LLMs_prompt(
        self,
        sysPromptPath: str = "prompt_system.txt",
        userPromptPath: str = "prompt_user.txt",
        *,
        campaign_target: Dict[str, Any],
        business_domain: Dict[str, Any],
        campaign_platforms_data: List[Dict[str, Any]],
        strict: bool = True,
    ) -> List[Dict[str, str]]:
        #print('prompt_builder')
        # Load prompts (relative to loader.prompts_dir unless you pass absolute paths)
        system_prompt = self.loader.load_prompt_text(sysPromptPath)
        user_prompt_template = self.loader.load_prompt_text(userPromptPath)

        # Serialize dict/list -> JSON strings (so template stays valid JSON)
        campaign_target_json = self._to_json(campaign_target)
        business_domain_json = self._to_json(business_domain)
        campaign_platforms_data_json = self._to_json(campaign_platforms_data)
        user_prompt = (
            user_prompt_template.replace("{{CAMPAIGN_TARGET}}", campaign_target_json)
            .replace("{{BUSINESS_DOMAIN}}", business_domain_json)
            .replace("{{CAMPAIGN_PLATFORMS_DATA}}", campaign_platforms_data_json)
        )

        if strict:
            required = [
                "{{CAMPAIGN_TARGET}}",
                "{{BUSINESS_DOMAIN}}",
                "{{CAMPAIGN_PLATFORMS_DATA}}",
            ]
            still_present = [tok for tok in required if tok in user_prompt]
            if still_present:
                raise ValueError(
                    "User prompt still contains unreplaced placeholder(s): "
                    + ", ".join(still_present)
                )

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
    
    
