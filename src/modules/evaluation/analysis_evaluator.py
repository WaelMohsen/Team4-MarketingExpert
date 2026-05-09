import json
import logging
import os
import re
from typing import List, Dict, Any, Optional

from ...shared.utils.prompt_loader import PromptLoader
from src.shared.utils.prompt_builder import PromptBuilder
from src.shared.utils.llm_client import LLMApiClient
from src.shared.models.llm_responses import AnalysisEvaluationResponse
from src.shared.utils.prompt_registry import PromptRegistry

# Configure logging using shared structure
try:
    from src.shared.utils.logger import setup_logging
    logger = setup_logging(module_name="llm_analysis_evaluator_v2")
    from src.shared.utils.json_saver import save_results_to_json
except ImportError:
    logger = logging.getLogger(__name__)


class AnalysisEvaluator:
    """
    Evaluates campaign analysis reports using manual prompts and structured outputs.
    Criteria: Clarity, Accuracy, Hallucination, Structure, KPI Alignment.
    """

    def __init__(self):
        self.loader = PromptLoader.from_module_dir()
        self.builder = PromptBuilder(loader=self.loader)
        self.client = LLMApiClient(
            model=os.getenv("EVALUATION_MODEL", "gpt-4.1-nano-2025-04-14"),
            max_output_tokens=2000,
        )

    def evaluate(
        self,
        campaign_data: Any,
        analysis_report: Any,
        campaign_target: Any,
        business_domain: Any,
        save_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Runs the analysis evaluation using LLMApiClient."""

        if not campaign_target:
            raise ValueError("campaign_target is required for analysis evaluation")

        primary_goal = campaign_target.get("primary_goal")
        kpis_list = campaign_target.get("kpis")

        if not primary_goal:
            raise ValueError("Missing campaign_target.primary_goal")

        if not kpis_list:
            raise ValueError("Missing campaign_target.kpis")

        context = {
            "target": campaign_target,
            "business_domain": business_domain,
        }

        sys_text = self.loader.load_prompt_text(
            PromptRegistry.EVAL_ANALYSIS_SYSTEM.value
        )
        user_text = self.loader.load_prompt_text(
            PromptRegistry.EVAL_ANALYSIS_USER.value
        )

        kpis = ", ".join(kpis_list)

        user_text = (
            user_text
            .replace("{{PRIMARY_GOAL}}", primary_goal)
            .replace("{{KPIS}}", kpis)
            .replace("{{CAMPAIGN_CONTEXT}}", json.dumps(context, indent=2))
            .replace("{{RAW_DATA}}", json.dumps(campaign_data, indent=2))
            .replace("{{ANALYSIS_REPORT}}", json.dumps(analysis_report, indent=2))
        )

        unresolved = re.findall(r"\{\{.*?\}\}", user_text)
        if unresolved:
            raise ValueError(f"Unresolved prompt placeholders found: {unresolved}")

        messages = [
            {"role": "system", "content": sys_text},
            {"role": "user", "content": user_text},
        ]

        logger.info("Executing Analysis Evaluation...")

        result = self.client.generate_json(
            messages,
            response_format=AnalysisEvaluationResponse,
            save_dir=save_dir,
            prompt_name="evaluation_analysis_prompt",
        )

        eval_data = result.get("evaluation", {})

        clarity_score = eval_data.get("clarity_score", 0)
        accuracy_score = eval_data.get("accuracy_score", 0)
        hallucination_score = eval_data.get("hallucination_score", 0)
        structure_score = eval_data.get("structure_score", 0)
        kpi_alignment_score = eval_data.get("kpi_alignment_score", 0)

        total_score = (
            clarity_score
            + accuracy_score
            + hallucination_score
            + structure_score
            + kpi_alignment_score
        )

        overall_avg = round(total_score / 5, 2)

        return {
            "scores": {
                "clarity": clarity_score,
                "accuracy": accuracy_score,
                "hallucination": hallucination_score,
                "structure": structure_score,
                "kpi_alignment": kpi_alignment_score,
                "total": total_score,
                "overall": overall_avg,
            },
            "reasoning": {
                "clarity": eval_data.get("clarity_reasoning"),
                "accuracy": eval_data.get("accuracy_reasoning"),
                "hallucination": eval_data.get("hallucination_reasoning"),
                "structure": eval_data.get("structure_reasoning"),
                "kpi_alignment": eval_data.get("kpi_alignment_reasoning"),
            },
            "hallucination_checklist": eval_data.get("hallucination_checklist", {}),
            "verdict": eval_data.get("verdict"),
            "key_issues": eval_data.get("key_issues"),
            "improvement_suggestions": eval_data.get("improvement_suggestions"),
        }


def run_evaluation_pipeline(
    files: List[str],
    output_dir: str = "data/outputs/_independent_run",
):
    """Main execution loop for analysis evaluation."""

    evaluator = AnalysisEvaluator()
    os.makedirs(output_dir, exist_ok=True)

    for file_path in files:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            continue

        logger.info(f"Processing File: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        campaign_data = data.get("input_data") or data.get("campaign_data")
        analysis_report = data.get("analysis_response")
        campaign_target = data.get("campaign_target")
        business_domain = data.get("business_domain")

        if not campaign_data:
            logger.warning(f"Skipping {file_path}: missing campaign data.")
            continue

        if not analysis_report:
            logger.warning(f"Skipping {file_path}: missing analysis_response.")
            continue

        try:
            comparison_results = evaluator.evaluate(
                campaign_data=campaign_data,
                analysis_report=analysis_report,
                campaign_target=campaign_target,
                business_domain=business_domain,
                save_dir=output_dir,
            )

            save_path = save_results_to_json(
                comparison_results,
                filename="analysis_evaluation_results.json",
                output_dir=output_dir,
            )

            logger.info(f"Evaluation results saved to: {save_path}")

            print("\nEvaluation Summary:")
            print(json.dumps(comparison_results["scores"], indent=2))
            print(f"Verdict: {comparison_results['verdict']}")
            print(f"Saved to: {save_path}")

        except Exception as e:
            logger.error(f"Failed to evaluate {file_path}: {e}")


if __name__ == "__main__":
    import argparse
    from dotenv import load_dotenv

    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("--files", nargs="+", required=True)
    parser.add_argument(
        "--output-dir",
        default="data/outputs/_global",
        help="Directory where analysis evaluation results should be saved.",
    )

    args = parser.parse_args()

    run_evaluation_pipeline(
        files=args.files,
        output_dir=args.output_dir,
    )