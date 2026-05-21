import os
import json
import logging
from typing import Dict, Any, List
from src.core.base_module import BaseModule
from src.core.execution_context import ExecutionContext
from src.shared.utils.prompt_loader import PromptLoader
from src.shared.utils.prompt_builder import PromptBuilder
from src.shared.utils.llm_client import LLMApiClient
from src.shared.models.llm_responses import AnalysisResponse
from src.shared.utils.prompt_registry import PromptRegistry

logger = logging.getLogger(__name__)


class AnalysisModule(BaseModule):
    """
    Module for performing Stage 1 Analysis using an LLM.
    """

    def __init__(self, name: str = "Analysis"):
        super().__init__(name)
        self.loader = PromptLoader.from_module_dir()
        self.builder = PromptBuilder(loader=self.loader)
        self.client = LLMApiClient(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            max_output_tokens=4000,
        )

    def run(self, context: ExecutionContext) -> ExecutionContext:
        if not context.enriched_data:
            raise ValueError(
                "Enriched data not found in context. Ensure EnrichmentModule ran first."
            )

        # Prepare input data for the LLM
        campaign_data = context.enriched_data.get("campaign_data")
        business_domain = context.get_metadata("business_domain", {})
        campaign_target = context.get_metadata("campaign_target", {})

        if not campaign_data:
            logger.warning("No campaign data found. Skipping analysis.")
            return context

        # Load goal-specific instructions
        primary_goal = campaign_target.get("primary_goal")
        goal_prompt_path = PromptRegistry.get_objective_prompt(primary_goal)
        goal_instructions = ""
        if goal_prompt_path:
            try:
                goal_instructions = self.loader.load_prompt_text(goal_prompt_path)
            except Exception as e:
                logger.warning(
                    f"Could not load goal-specific prompt for '{primary_goal}': {e}"
                )

        # Build prompt
        messages = self.builder.build_analysis_prompt(
            sysPromptPath=PromptRegistry.ANALYSIS_SYSTEM.value,
            userPromptPath=PromptRegistry.ANALYSIS_USER.value,
            campaign_data=campaign_data,
            business_domain=business_domain,
            campaign_target=campaign_target,
            goal_instructions=goal_instructions,
        )

        # Generate Analysis
        logger.info("Executing Stage 1: Analysis...")
        analysis_result = self.client.generate_json(
            messages,
            response_format=AnalysisResponse,
            save_dir=(
                os.path.join(context.runtime_output_path, "prompts")
                if context.runtime_output_path
                else None
            ),
            prompt_name="analysis_prompt",
        )

        context.analysis_results = analysis_result
        return context

    def save(self, context: ExecutionContext):
        # Use row-specific subdirectory if provided
        output_dir = context.runtime_output_path or os.path.join(
            context.get_metadata("output_json_dir", "data/outputs/"), "analysis"
        )
        os.makedirs(output_dir, exist_ok=True)

        if context.analysis_results:
            output_path = os.path.join(output_dir, "analysis_result.json")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(context.analysis_results, f, ensure_ascii=False, indent=2)
            logger.info(f"Analysis result saved to: {output_path}")
