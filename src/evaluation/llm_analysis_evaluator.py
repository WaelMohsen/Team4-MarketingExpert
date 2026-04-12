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
from pathlib import Path
from datetime import datetime
import argparse
from dotenv import load_dotenv


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
                "campaign_data": campaign_data,
                "analysis_context": analysis_context,
                "campaign_target": campaign_target,
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


def print_analysis_summary(report: Dict[str, Any], file_name: str = "Sample"):
    """
    Prints a pretty summary of the analysis evaluation.
    """
    scores = report.get("scores", {})
    reasoning = report.get("reasoning", {})
    
    print("\n" + "="*60)
    print(f"           ANALYSIS EVALUATION: {file_name}")
    print("="*60)
    print(f"Overall Score            : {scores.get('overall', 0):.2f}")
    print(f"Clarity                  : {scores.get('clarity', 0):.2f}")
    print(f"Relevance                : {scores.get('relevance', 0):.2f}")
    print(f"Following Structure      : {scores.get('following_structure', 0):.2f}")
    print(f"Hallucination Detected   : {'YES' if report.get('hallucination_flag') is True else 'NO'}")
    
    print("\n" + "-"*30 + " TOP REASONING " + "-"*30)
    
    # Show first point of each reasoning if exists
    for key in ["clarity", "relevance", "structure", "hallucination"]:
        r_list = reasoning.get(key, [])
        if r_list:
            # Handle list of strings or single string
            point = r_list[0] if isinstance(r_list, list) else r_list
            print(f"{key.capitalize():15}: {point[:150]}{'...' if len(point) > 150 else ''}")
            
    print("="*60 + "\n")


def main():
    # 1. CLI Setup
    load_dotenv()
    parser = argparse.ArgumentParser(description="Evaluate Marketing Analysis Results")
    parser.add_argument("--files", nargs="+", help="Specific JSON files to evaluate (e.g. data/outputs/campaign_1_result.json)")
    args = parser.parse_args()

    # 2. Path Setup
    BASE_DIR = Path(__file__).resolve().parent.parent
    LOG_DIR = BASE_DIR / "logs"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create run directory for the session
    run_dir = LOG_DIR / datetime.now().strftime("%Y-%m-%d")
    run_dir.mkdir(parents=True, exist_ok=True)

    # 3. DSPy Setup: Requires a language model (LM) configuration
    try:
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        logger.info(f"Configuring DSPy LM with model: openai/{model}")
        lm = dspy.LM(f"openai/{model}")
        dspy.settings.configure(lm=lm)
    except Exception as e:
        logger.error(f"Failed to configure DSPy LM: {e}")
        raise

    # 4. Instantiate the Evaluator
    evaluator = LLMAnalysisEvaluator()

    if args.files:
        # 5. Process Files
        for file_path in args.files:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                logger.error(f"File not found: {file_path}")
                continue
                
            logger.info(f"--- Evaluating Analysis Product: {file_path_obj.name} ---")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Mapping project JSON structure to Evaluator inputs
                campaign_data = data.get("input_data")
                analysis_context = data.get("analysis_response")
                campaign_target = data.get("campaign_target")

                if not all([campaign_data, analysis_context, campaign_target]):
                    logger.warning(f"Skipping {file_path_obj.name}: missing required fields (input_data, analysis_response, or campaign_target).")
                    continue

                report = evaluator.run_evaluation_pipeline(
                    campaign_data=campaign_data,
                    analysis_context=analysis_context,
                    campaign_target=campaign_target,
                )

                # Pretty Print Summary
                print_analysis_summary(report, file_path_obj.name)

                # Save individual evaluation result
                output_name = f"analysis_evaluation_result_{file_path_obj.stem}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
                output_path = run_dir / output_name
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
                
                logger.info(f"Evaluation for {file_path_obj.name} saved to: {output_path}")

            except Exception as e:
                logger.error(f"Failed to process {file_path_obj.name}: {e}")
                continue

    else:
        # 6. Fallback to Sample Run
        logger.info("No files provided. Running sample evaluation...\n")
        
        sample_campaign_data = [
            {
                "platform": "Google Ads",
                "objective": "Leads",
                "spend": 5000,
                "conversions": 320,
            }
        ]

        sample_campaign_target = {
            "primary_goal": "Maximize ROAS",
            "kpis": ["ROAS", "CPL"],
        }

        sample_analysis_context = {
            "analysis": {
                "executive_summary": "High spend on Google Ads, but efficient conversions.",
                "budget_and_efficiency": [{"insight": "Good ROAS", "evidence": "1.8", "business_impact": "Scale"}]
            }
        }

        try:
            report = evaluator.run_evaluation_pipeline(
                campaign_data=sample_campaign_data,
                analysis_context=sample_analysis_context,
                campaign_target=sample_campaign_target,
            )
            
            print_analysis_summary(report, "Sample Execution")
            
            # Save Sample Result
            output_path = run_dir / "sample_analysis_evaluation.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Sample evaluation results saved to: {output_path}")

        except Exception as e:
            logger.error(f"Sample execution failed: {e}")


if __name__ == "__main__":
    main()
