import os
import json
import dspy
import sys
from typing import Any, Dict, Union
StructuredInput = Union[str, list, dict]

from analysis_evaluation_signature import AnalysisEvaluationSignature
from analysis_evaluator_error_handling import (
    InvalidInputError,
    EvaluationExecutionError,
    InvalidEvaluationResultError,
)
from validation_utils import ValidationUtils

# Find the absolute path to the project root (Unified-Marketing-Truth-Engine)
# '..' goes up one level from 'evaluation' to the root.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Add the project root to the Python path
sys.path.append(PROJECT_ROOT)
# Configger logging 
from logs.logging_config import setup_logging
logger = setup_logging(module_name ='llm_analysis_evaluator')
from logs.save_llm_results_to_json import save_results_to_json


class LLMAnalysisEvaluator(dspy.Module):
    """
    An evaluation and normalization layer for LLM-generated analysis using the DSPy framework.

    This class serves as a structured post-processing and validation module. It uses
    Chain-of-Thought reasoning to evaluate campaign data against specific contexts
    and structures, providing normalized scores and reasoning.

    Attributes:
        evaluate (dspy.ChainOfThought): The DSPy program configured with
            AnalysisEvaluationSignature to perform structured evaluations.
    """

    # Define constants representing weights of each evaluation factor
    CLARITY_WEIGHT = 0.2
    RELEVANCE_WEIGHT = 0.3
    STRUCTURE_WEIGHT = 0.2
    hallucination_WEIGHT = 0.3

    # Initialization
    def __init__(self):
        """
        Initializes the LLMAnalysisEvaluator by setting up the dspy.ChainOfThought
        pipeline with the required evaluation signature.
        """
        super().__init__()
        # Call the LLM and get structured evaluation fields back
        self.evaluate = dspy.ChainOfThought(AnalysisEvaluationSignature)

    def _compute_weighted_score(
        self, clarity: float, follow_output_structure: float, relevance: float, hallucination: int
    ) -> float:
        """
        Encapsulated business logic for scoring.
        """
        return (
            (self.CLARITY_WEIGHT * clarity)
            + (self.STRUCTURE_WEIGHT * follow_output_structure)
            + (self.RELEVANCE_WEIGHT * relevance)
            + (self.hallucination_WEIGHT * relevance)
        )

    # Main Entry Point:
    def run_evaluation_pipeline(
        self,
        campaign_data: StructuredInput,
        analysis_context: StructuredInput,
        #analysis_structure: str,
        campaign_target: StructuredInput,
    ) -> Dict[str, Any]:
        """
        Processes the input data through the LLM and normalizes the resulting evaluation.

        Execution Flow:
        1. Executes the LLM evaluation via Chain-of-Thought.
        2. Safely extracts and casts scores (Clarity, Accuracy, Relevance).
        3. Calculates a weighted 'Overall' score (50% Accuracy, 25% Clarity, 25% Relevance).
        4. Normalizes reasoning fields into lists for consistent downstream consumption.
        5. Extracts the hallucination flag.

        Args:
            campaign_data (str | list | dict): The raw campaign information to be analyzed.
            analysis_context (str | list | dict): The background or objectives for the evaluation.
            analysis_structure (str): The specific format or requirements to check against.
            campaign_target (str | list | dict): the target of the campaign

        Returns:
            Dict[str, Any]: A structured dictionary containing:
                - scores (dict): clarity, accuracy, relevance, and overall_weighted_score.
                - hallucination_flag (bool): Whether a hallucination was detected.
                - reasoning (dict): Lists of feedback for clarity, structure, relevance, and hallucinations.
        """
        
        logger.info("Starting evaluation pipeline")
        # Input Validation
        try:
            # Validate inputs to ensure all required strings are valid and non-empty
            validated_campaign_data = ValidationUtils.convert_structure_input_to_string(
                campaign_data,
                "campaign_data",
            )
            validated_analysis_context = ValidationUtils.convert_structure_input_to_string(
                analysis_context,
                "analysis_context",
            )
            #validated_analysis_structure = ValidationUtils.validate_text_input(
            #    analysis_structure,
            #    "analysis_structure",
            #)

            validated_campaign_target = ValidationUtils.convert_structure_input_to_string(
                campaign_target,
                "campaign_target",
            )
            logger.debug("input validated successfully")
        except Exception as exc:
            logger.exception("Input validation failed")
            raise InvalidInputError("Invalid input provided") from exc


        # Call the LLM
        try:
            logger.info("Calling DSPy evaluation")
            result = self.evaluate(
                campaign_data=validated_campaign_data,
                analysis_context=validated_analysis_context,
                #analysis_structure=validated_analysis_structure,
                campaign_target=validated_campaign_target,
            )
            logger.debug(f"Raw LLM result: {result}")

        except Exception as exc:
            logger.exception("DSPy/Analysis evaluation failed")
            raise EvaluationExecutionError(
            "Failed to execute DSPy/Analysis evaluation."
            ) from exc

        if result is None:
            logger.error("DSPy returned None result")
            raise InvalidEvaluationResultError("DSPy evaluation returned None.")

        # Extraction and Casting
        try:
            scores = {
                "clarity": ValidationUtils.clamp_score(
                    ValidationUtils.cast_to_float(getattr(result, "clarity_score", None))
                ),
                "relevance": ValidationUtils.clamp_score(
                    ValidationUtils.cast_to_float(getattr(result, "relevance_score", None))
                ),
                "following_structure": ValidationUtils.clamp_score(
                    ValidationUtils.cast_to_float(
                        getattr(result, "following_structure_score", None)
                    )
                ),
                "hallucination_flag": getattr(result, "hallucination_flag", None),
            }
            logger.debug(f"Extracted scores: {scores}")

        except Exception as exc:
            logger.exception("Failed to extract valida scores")
            raise InvalidEvaluationResultError("Invalid score structure") from exc

        # Compute weighted overall score (accuracy > clarity > relevance_score)
        try:
            overall_weighted_score = ValidationUtils.clamp_score(
                self._compute_weighted_score(
                    scores["clarity"],
                    scores["relevance"],
                    scores["following_structure"],
                    scores["hallucination_flag"],
                )
            )
            logger.debug(f"Overall weighted score: {overall_weighted_score}")
        except Exception as exc:
            logger.exception("Failed computing overall weighted score")
            raise InvalidEvaluationResultError(
            "Fail to compute overall_weighted_score."
            ) from exc

        # Final Output Structure
        try:
            structured_result = {
                "scores": {**scores, "overall": overall_weighted_score},
                "hallucination_flag": ValidationUtils.cast_to_bool(
                    getattr(result, "hallucination_flag", False)
                ),
                "reasoning": {
                    "clarity": ValidationUtils.ensure_list(
                        getattr(result, "clarity_reasoning", [])
                    ),
                    "structure": ValidationUtils.ensure_list(
                        getattr(result, "following_structure_reasoning", [])
                    ),
                    "relevance": ValidationUtils.ensure_list(
                        getattr(result, "relevance_reasoning", [])
                    ),
                    "hallucination": ValidationUtils.ensure_list(
                        getattr(result, "hallucination_reasoning", [])
                    ),
                },
            }
            logger.info("Evaluation pipeline completed successfully")
        except Exception as exc:
            logger.exception("Failed to normalize result")
            raise InvalidEvaluationResultError(
                "Fail to normalize/handle evaluation result."
            ) from exc
        return structured_result


def main():
    # 1. Setup: Usually requires a DSPy language model (LM) configuration
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    # TODO: check for OpenAI API key in env variables and raise warning if not found
    lm = dspy.LM(f"openai/{model}")
    dspy.settings.configure(lm=lm)

    # 2. Instantiate the Evaluator
    evaluator = LLMAnalysisEvaluator()

    # 3. Define sample input data
    # TODO: read data dynamically from a file or a mock data generator instead of hardcoding
    # TODO: Use the correct analysis json structure that the LLM expects, this is just a placeholder and may not align with the expected input format of the LLM.
    sample_campaign_data = [
        {
            "platform": "Google Ads",
            "objective": "Leads",
            "spend": 5000,
            "impressions": 200000,
            "clicks": 8000,
            "conversions": 320,
            "revenue": 15000,
        },
        {
            "platform": "Meta",
            "objective": "Leads",
            "spend": 3000,
            "impressions": 150000,
            "clicks": 6000,
            "conversions": 180,
            "revenue": 9000,
        },
    ]

    sample_campaign_target = {
        "primary_goal": "Maximize ROAS during the Winter Holiday Sale",
        "kpis": ["ROAS", "CPA", "Conversion Volume"],
    }

    sample_analysis_context = {
        "analysis": {
            "executive_summary": "Sample analysis summary",
            "budget_and_efficiency": [
            {
                "insight": "High spend on underperforming channel",
                "evidence": "Channel X has 2x higher CAC than benchmark",
                "business_impact": "Reallocating 20% budget could improve overall ROAS"
            }
            ],
            "results_and_value": [
            {
                "insight": "Strong lead generation volume",
                "evidence": "1,500 leads/month at $15 CAC",
                "business_impact": "Supports 30% MoM revenue growth"
            }
            ],
            "cross_channel_patterns_and_risks": [
            {
                "pattern_or_risk": "Attribution overlap between channels",
                "evidence": "30% of converters touched 2+ channels",
                "why_it_matters": "Multi-touch attribution needed for accurate ROI"
            }
            ],
            "channel_notes": [
            {
                "platform": "Google Ads",
                "what_we_see": [
                "$50K spend",
                "1,200 conversions"
                ],
                "what_it_likely_means": [
                "Strong brand search intent",
                "Mature campaign"
                ],
                "risks_or_watchouts": [
                "ROAS trending down YoY"
                ]
            }
            ],
            "missing_info": [
            "Customer lifetime value",
            "Competitor spend data"
            ]
        }
    }

    # 4. Run the evaluation
    # Note: This will call the LLM if DSPy is configured.
    try:
        print("--- Running Analysis Evaluation ---\n")
        logger.info("Executing evaluation...\n")    
        report = evaluator.run_evaluation_pipeline(
            campaign_data=sample_campaign_data,
            analysis_context=sample_analysis_context,
            #analysis_structure="Standard campaign analysis structure",
            campaign_target=sample_campaign_target,
        )
        print("type of report",type(report))
        # 5. Print formatted results
        print(json.dumps(report, indent=4))

        # Accessing specific fields
        final_score = report["scores"]["overall"]
        print(f"\nFinal Weighted Score: {final_score:.2f}")

    except Exception as e:
        print(f"Error during execution: {e}")
        print(
            "\nTip: Ensure you have configured a DSPy Language Model (LM) before running."
        )
    
    # 6. Save Output to File ---
    from pathlib import Path
    BASE_DIR = Path(__file__).resolve().parent.parent
    LOG_DIR = BASE_DIR / "logs"
    save_results_to_json(report, LOG_DIR)  

    logger.info(f"Evaluation results successfully saved to: {LOG_DIR}")


if __name__ == "__main__":
    main()
