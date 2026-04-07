from typing import Any, Dict
# This class acts as:
# an evaluation layer
# a post-processing + validation layer
# a normalization layer for LLM output
# Inherits from dspy.Module → this is part of the DSPy framework (used for structured LLM pipelines).

from .analysis_evaluation_signature  import AnalysisEvaluationSignature


try:
    import dspy
except ImportError:
    raise ImportError("DSPy is not installed. Please install it with `pip install dspy-ai` or `uv pip install dspy-ai`.")

class AnalysisEvaluator(dspy.Module):
    """
    An evaluation and normalization layer for LLM-generated analysis using the DSPy framework.

    This class serves as a structured post-processing and validation module. It uses 
    Chain-of-Thought reasoning to evaluate campaign data against specific contexts 
    and structures, providing normalized scores and reasoning.

    Attributes:
        evaluate (dspy.ChainOfThought): The DSPy program configured with 
            AnalysisEvaluationSignature to perform structured evaluations.
    """
    # Initialization
    def __init__(self):
        """
        Initializes the AnalysisEvaluator by setting up the dspy.ChainOfThought 
        pipeline with the required evaluation signature.
        """
        super().__init__()
        # Call the LLM and get structured evaluation fields back
        self.evaluate = dspy.ChainOfThought(AnalysisEvaluationSignature)

    def _cast_to_float(self, value, default=0.0):
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
    
    #Main Entry Point:
    def forward(
        self,
        campaign_data: str,
        analysis_context: str,
        analysis_structure: str
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
            campaign_data (str): The raw campaign information to be analyzed.
            analysis_context (str): The background or objectives for the evaluation.
            analysis_structure (str): The specific format or requirements to check against.

        Returns:
            Dict[str, Any]: A structured dictionary containing:
                - scores (dict): clarity, accuracy, relevance, and overall_weighted_score.
                - hallucination_flag (bool): Whether a hallucination was detected.
                - reasoning (dict): Lists of feedback for clarity, structure, relevance, and hallucinations.
        """
        
        # Call the LLM
        result = self.evaluate(
            campaign_data = campaign_data,
            analysis_context = analysis_context,
            analysis_structure = analysis_structure
        )
        # --- Parse scores safely ---
        clarity_score = self._cast_to_float(getattr(result, "clarity_score", None))
        accuracy_score = self._cast_to_float(getattr(result, "accuracy_score", None))
        relevance_score = self._cast_to_float(getattr(result, "relevance_score", None))

        # --- Weighted overall (accuracy > clarity > relevance_score) ---
        overall_weighted_score = (
            (0.5 * accuracy_score) +
            (0.25 * clarity_score) +
            (0.25 * relevance_score)
        )
        # --- Safe extraction of optional reasoning fields ---
        # Normalize reasoning fields to lists when needed.

        clarity_reasoning = getattr(result, "clarity_reasoning", [])
        if isinstance(clarity_reasoning, str):
            clarity_reasoning = [clarity_reasoning]

        structure_reasoning = getattr(result, "structure_reasoning", [])
        if isinstance(structure_reasoning, str):
            structure_reasoning = [structure_reasoning]
        
        relevance_reasoning = getattr(result, "relevance_reasoning", [])
        if isinstance(relevance_reasoning, str):
            relevance_reasoning = [relevance_reasoning]
        
        hallucination_reasoning = getattr(result, "hallucination_reasoning", [])
        if isinstance(hallucination_reasoning, str):
            hallucination_reasoning = [hallucination_reasoning]
        
        hallucination_flag = getattr(result, "hallucination_flag", False)
        
        # Final Output Structure
        return {
            "scores": {
                "clarity": clarity_score,
                "accuracy": accuracy_score,
                "relevance": relevance_score,
                "overall":   overall_weighted_score,
            },
            "hallucination_flag": hallucination_flag,
            "reasoning": {
                "clarity": clarity_reasoning,
                "structure": structure_reasoning,
                "relevance": relevance_reasoning,
                "hallucination": hallucination_reasoning
            }

        }




