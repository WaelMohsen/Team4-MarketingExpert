import os
import json
from typing import Any, Dict, Union

StructuredInput = Union[str, list, dict]

# This class acts as:
# an evaluation layer
# a post-processing + validation layer
# a normalization layer for LLM output
# Inherits from dspy.Module → this is part of the DSPy framework (used for structured LLM pipelines).

from analysis_evaluation_signature  import AnalysisEvaluationSignature
from analysis_evaluator_error_handling import InvalidInputError, EvaluationExecutionError, InvalidEvaluationResultError

try:
    import dspy
except ImportError:
    raise ImportError("DSPy is not installed. Please install it with `pip install dspy-ai` or `uv pip install dspy-ai`.")


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
    RELEVANCE_WEIGHT = 0.5
    STRUCTURE_WEIGHT = 0.3
   


    # Initialization
    def __init__(self):
        """
        Initializes the LLMAnalysisEvaluator by setting up the dspy.ChainOfThought 
        pipeline with the required evaluation signature.
        """
        super().__init__()
        # Call the LLM and get structured evaluation fields back
        self.evaluate = dspy.ChainOfThought(AnalysisEvaluationSignature)

    def _compute_weighted_score(self, clarity: float, follow_output_structure: float, relevance: float) -> float:

        """
        Encapsulated business logic for scoring.
        """
        return (
            
            (self.CLARITY_WEIGHT * clarity) +
            (self.STRUCTURE_WEIGHT * follow_output_structure) +
            (self.RELEVANCE_WEIGHT * relevance)
        )    
    # Validation Functions
    def _cast_to_float(self, value: Any, default: float = 0.0) -> float:
        """
        Converts a given input into a float, providing a fallback value on failure.

        This method attempts to cast various data types (strings, integers, etc.) 
        to a float. It is designed to handle "dirty" data or missing values 
        without raising an exception, ensuring the stability of the processing pipeline.

        Args:
            value (Any): The input value to be converted. Can be a string, 
                numeric type, or None.
            default (float, optional): The value to return if the conversion 
                fails due to a ValueError or TypeError. Defaults to 0.0.

        Returns:
            float: The converted float value if successful; otherwise, the default value.
        """
        try:
            return float(value)
        except (ValueError, TypeError):
            return default


    def _clamp_score(self, score: float, min_value: float = 1.0, max_value: float = 3.0) -> float:
        """
        Ensures a score stays within a defined range.

        Args:
            score (float): The score to validate.
            min_value (float): Minimum allowed value (default = 0.0).
            max_value (float): Maximum allowed value (default = 5.0).

        Returns:
            float: Clamped score within [min_value, max_value].
        """
        # Validate bounds
        if not isinstance(min_value, (int, float)) or not isinstance(max_value, (int, float)):
            raise ValueError("min_value and max_value must be numeric.")

        if min_value > max_value:
            raise ValueError(
                f"min_value ({min_value}) cannot be greater than max_value ({max_value})."
            )

        # Validate score
        if not isinstance(score, (int, float)):
            raise TypeError(
                f"score must be numeric, got {type(score).__name__}."
            )

        return min(max(score, min_value), max_value)

    def _ensure_list(self, value: Any) -> list:
        """ Helper to normalize reasoning fields."""

        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return [value]
        return [value]
    
    

    def _validate_text_input(self, value: Any, var_name: str) -> str:
        """
        Validates that an input field is a non-empty string.
        """
        if not isinstance(value, str):
            raise InvalidInputError(
                f"{var_name} must be a string, got {type(value).__name__}."
            )
        
        # remove leading and trailing whitespace (or specified characters) from a string.
        cleaned_value = value.strip()
        if not cleaned_value:
            raise InvalidInputError(f"{var_name} cannot be empty.")

        return cleaned_value


    def _convert_structure_input_to_string(self, data: Any,  var_name: str) -> str:
        """
        Convert structures input formats into a single string for LLM processing.

        This method ensures the LLM receives a clean string regardless of whether 
        the input is a raw string, a list, or a dictionary.
        """        
        if isinstance(data, str):
            cleaned_value = data.strip()
            if not cleaned_value:
                raise InvalidInputError(f"{var_name} cannot be empty.")
            return cleaned_value

        if isinstance(data, (list, dict)):
            try:
                return json.dumps(data, indent=2)
            except TypeError as exc:
                raise InvalidInputError(f"{var_name} contains non-serializable values.") from exc

        raise InvalidInputError(
            f"{var_name} must be a string, list, or dict, got {type(data).__name__}."
        ) 
    
    # Convert to bool data type
    def _cast_to_bool(self, value: Any, default: bool = False) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "1", "yes"}:
                return True
            if normalized in {"false", "0", "no", ""}:
                return False
            return default
        if isinstance(value, (int, float)):
            return bool(value)
        
        return default    
       
    #Main Entry Point:
    def forward(self, campaign_data: StructuredInput , analysis_context: StructuredInput , analysis_structure: str, campaign_target: StructuredInput ) -> Dict[str, Any]:
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
        # Validate inputs to ensure all required strings are valid and non-empty 
        validated_campaign_data = self._convert_structure_input_to_string(
            campaign_data,"campaign_data",
        )
        validated_analysis_context = self._convert_structure_input_to_string(
            analysis_context, "analysis_context",
        )
        validated_analysis_structure = self._validate_text_input(
            analysis_structure, "analysis_structure",
        )
        
        validated_campaign_target = self._convert_structure_input_to_string(
            campaign_target,"campaign_target",
        )
        
        # Call the LLM
        try:
            result = self.evaluate(
                campaign_data = validated_campaign_data,
                analysis_context = validated_analysis_context,
                analysis_structure = validated_analysis_structure,
                campaign_target = validated_campaign_target
            )
        except Exception as exc:
            raise EvaluationExecutionError(
                "Failed to execute DSPy evaluation."
            ) from exc

        if result is None:
            raise InvalidEvaluationResultError(
                "DSPy evaluation returned None."
            )
        


        # Extraction and Casting
        scores = {
                
                "clarity": self._clamp_score(
                    self._cast_to_float(getattr(result, "clarity_score", None))
                ),
                "relevance": self._clamp_score(
                    self._cast_to_float(getattr(result, "relevance_score", None))
                ),
                
                "following_structure": self._clamp_score(
                    self._cast_to_float(getattr(result, "following_structure_score", None))
                )
            }

        # Compute weighted overall score (accuracy > clarity > relevance_score) 
        try:
            overall_weighted_score = self._clamp_score(self._compute_weighted_score(
                scores["clarity"], scores["relevance"], scores["following_structure"]
            ))
        except Exception as exc:
            raise InvalidEvaluationResultError(
                "Fail to compute overall_weighted_score."
            ) from exc            

        # Final Output Structure
        try:
            structured_result = {
                "scores": {**scores, "overall": overall_weighted_score},
                "hallucination_flag": self._cast_to_bool(getattr(result, "hallucination_flag", False)),
                "reasoning": {
                    "clarity": self._ensure_list(getattr(result, "clarity_reasoning", [])),
                    "structure": self._ensure_list(getattr(result, "structure_reasoning", [])),
                    "relevance": self._ensure_list(getattr(result, "relevance_reasoning", [])),
                    "hallucination": self._ensure_list(getattr(result, "hallucination_reasoning", []))
                }
            }
        except Exception as exc:
            raise InvalidEvaluationResultError(
                "Fail to normalize/handle evaluation result."
            ) from exc               
        return   structured_result     


def main():

    # 1. Setup: Usually requires a DSPy language model (LM) configuration    
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    lm = dspy.LM(f"openai/{model}")
    dspy.settings.configure(lm=lm)


    # 2. Instantiate the Evaluator
    evaluator = LLMAnalysisEvaluator()

    # 3. Define sample input data
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
        "kpis": ["ROAS", "CPA", "Conversion Volume"]
    }

    sample_analysis_context = {
        "analysis": {
            "executive_summary": "Google Ads is driving a high ROAS of 4.5x but has a limited impression share due to budget caps. Meanwhile, Meta is consuming 70% of the budget but its ROAS has dropped to 1.8x over the last two weeks, strongly indicating ad fatigue on the current creative sets.",
            "budget_and_efficiency": [
                {
                    "insight": "Google Ads budget is capping out daily.",
                    "evidence": "Search impression share lost due to budget is at 45%.",
                    "business_impact": "Leaving highly profitable conversions on the table."
                }
            ],
            "results_and_value": [],
            "cross_channel_patterns_and_risks": [
                {
                    "pattern_or_risk": "Meta creative fatigue is dragging down blended return.",
                    "evidence": "Frequency on Meta is over 8, and CTR dropped from 1.5% to 0.6%.",
                    "why_it_matters": "The largest budget pool is becoming increasingly inefficient."
                }
            ],
            "channel_notes": [],
            "missing_info": []
        }
    }

    
   

    # 4. Run the evaluation
    # Note: This will call the LLM if DSPy is configured.
    try:
        print("--- Running Analysis Evaluation ---\n")
        report = evaluator.forward(
            campaign_data=sample_campaign_data,
            analysis_context=sample_analysis_context,
            campaign_target = sample_campaign_target,
        )

        # 5. Print formatted results
        print(json.dumps(report, indent=4))
        
        # Accessing specific fields
        final_score = report["scores"]["overall"]
        print(f"\nFinal Weighted Score: {final_score:.2f}")

    except Exception as e:
        print(f"Error during execution: {e}")
        print("\nTip: Ensure you have configured a DSPy Language Model (LM) before running.")


if __name__ == "__main__":
    main()



