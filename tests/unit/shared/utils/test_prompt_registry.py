from src.shared.utils.prompt_registry import PromptRegistry

def test_Members_ShouldHaveCorrectPaths_WhenAccessed():
    """Verify that PromptRegistry has all expected prompt paths."""
    # Act & Assert
    assert PromptRegistry.ANALYSIS_SYSTEM.value == "analysis/system.txt"
    assert PromptRegistry.ANALYSIS_USER.value == "analysis/user.txt"
    assert PromptRegistry.RECOMMENDATION_SYSTEM.value == "recommendation/system.txt"
    assert PromptRegistry.RECOMMENDATION_USER.value == "recommendation/user.txt"
    assert PromptRegistry.EVAL_ANALYSIS_SYSTEM.value == "evaluation/analysis_system.txt"
    assert PromptRegistry.EVAL_ANALYSIS_USER.value == "evaluation/analysis_user.txt"
    assert PromptRegistry.EVAL_RECOMMENDATION_SYSTEM.value == "evaluation/recommendation_system.txt"
    assert PromptRegistry.EVAL_RECOMMENDATION_USER.value == "evaluation/recommendation_user.txt"
