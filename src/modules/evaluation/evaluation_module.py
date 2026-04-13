import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List

from src.core.base_module import BaseModule
from src.core.execution_context import ExecutionContext
from .analysis_evaluator import AnalysisEvaluator
from .recommendation_evaluator import RecommendationEvaluator

logger = logging.getLogger(__name__)

class EvaluationModule(BaseModule):
    """
    Module for evaluating LLM outputs (Analysis and Recommendation).
    Uses a unified prompt-based architecture.
    """

    def __init__(self, name: str = "Evaluation"):
        super().__init__(name)
        self.analysis_evaluator = AnalysisEvaluator()
        self.recommendation_evaluator = RecommendationEvaluator()

    def run(self, context: ExecutionContext) -> ExecutionContext:
        evaluations: Dict[str, Any] = {}

        # 1. Evaluate Analysis
        if context.analysis_results:
            logger.info("Evaluating Analysis results...")
            try:
                # Prepare data for evaluator
                campaign_data = context.enriched_data.get("processed_df")
                if campaign_data is not None:
                    # Convert to list of dicts for evaluation if it's a DataFrame
                    # Using records from platform summary is often cleaner for LLM context
                    campaign_data = context.enriched_data.get("platform_summary", {}).get("platform_summary", [])

                analysis_eval = self.analysis_evaluator.evaluate(
                    campaign_data=campaign_data,
                    analysis_report=context.analysis_results,
                    campaign_target=context.get_metadata("campaign_target"),
                )
                evaluations["analysis"] = analysis_eval
            except Exception as e:
                logger.error(f"Analysis evaluation failed: {e}")

        # 2. Evaluate Recommendations
        if context.recommendation_results:
            logger.info("Evaluating Recommendation cards...")
            try:
                recommendations = context.recommendation_results.get("recommendations", [])
                rec_evals = []
                
                business_context = context.get_metadata("business_domain")
                analysis_context = context.analysis_results

                for rec in recommendations:
                    rec_eval = self.recommendation_evaluator.evaluate(
                        business_context=business_context,
                        analysis_context=analysis_context,
                        recommendation=rec
                    )
                    rec_evals.append({
                        "card_title": rec.get("title"),
                        "evaluation": rec_eval
                    })
                evaluations["recommendations"] = rec_evals
            except Exception as e:
                logger.error(f"Recommendation evaluation failed: {e}")

        context.evaluations = evaluations
        return context

    def save(self, context: ExecutionContext):
        # Use row-specific subdirectory if provided
        output_dir = context.runtime_output_path or os.path.join(context.get_metadata("output_json_dir", "data/outputs/"), "evaluation")
        os.makedirs(output_dir, exist_ok=True)
        
        if context.evaluations:
            # 1. Save Analysis Evaluation
            analysis_eval = context.evaluations.get("analysis")
            if analysis_eval:
                path = os.path.join(output_dir, "analysis_evaluation_results.json")
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(analysis_eval, f, ensure_ascii=False, indent=2, default=str)
                logger.info(f"Analysis evaluation results saved to: {path}")

            # 2. Save Recommendation Evaluation
            rec_evals = context.evaluations.get("recommendations")
            if rec_evals:
                path = os.path.join(output_dir, "recommendation_evaluation_results.json")
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(rec_evals, f, ensure_ascii=False, indent=2, default=str)
                logger.info(f"Recommendation evaluation results saved to: {path}")
