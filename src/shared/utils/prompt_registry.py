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
    EVAL_ANALYSIS_SYSTEM = "evaluation/analysis_system.md"
    EVAL_ANALYSIS_USER = "evaluation/analysis_user.md"

    # Evaluation: Recommendation
    EVAL_RECOMMENDATION_SYSTEM = "evaluation/recommendation_system.txt"
    EVAL_RECOMMENDATION_USER = "evaluation/recommendation_user.txt"
    #objectives 
    BRAND_AWARENESS= "objectives/brand_awareness.txt"
    REVENUE_EFFICIENCY="objectives/revenue_efficiency.txt"
    SALES_BOOST="objectives/sales_boost.txt"
    TRAFFIC="objectives/traffic.txt"

    @classmethod
    def get_objective_prompt(cls, goal: str) -> str:
        """
        Maps a primary_goal string to its corresponding prompt file path.
        """
        mapping = {
            "Increase Sales": cls.SALES_BOOST.value,
            "Brand Awareness": cls.BRAND_AWARENESS.value,
            "Revenue Efficiency": cls.REVENUE_EFFICIENCY.value,
            "Traffic": cls.TRAFFIC.value
        }
        return mapping.get(goal, "") # Return empty if no specific goal prompt exists

