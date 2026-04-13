from enum import Enum


class PromptRegistry(Enum):
    """
    Centralized registry for all LLM prompt file paths.
    All paths are relative to the 'src/shared/prompts' directory.
    """

    # Stage 1: Analysis
    ANALYSIS_SYSTEM = "analysis/system.txt"
    ANALYSIS_USER = "analysis/user.txt"

    # Stage 2: Recommendation
    RECOMMENDATION_SYSTEM = "recommendation/system.txt"
    RECOMMENDATION_USER = "recommendation/user.txt"

    # Evaluation: Analysis
    EVAL_ANALYSIS_SYSTEM = "evaluation/analysis_system.txt"
    EVAL_ANALYSIS_USER = "evaluation/analysis_user.txt"

    # Evaluation: Recommendation
    EVAL_RECOMMENDATION_SYSTEM = "evaluation/recommendation_system.txt"
    EVAL_RECOMMENDATION_USER = "evaluation/recommendation_user.txt"
