import pytest
import json
from unittest.mock import MagicMock
from src.shared.utils.prompt_builder import PromptBuilder

@pytest.fixture
def mock_loader():
    loader = MagicMock()
    # Mock system prompt
    loader.load_prompt_text.side_effect = lambda path: {
        "analysis/system.txt": "System Analysis",
        "analysis/user.txt": "User {{CAMPAIGN_DATA}} {{BUSINESS_DOMAIN}} {{CAMPAIGN_TARGET}}",
        "recommendation/system.txt": "System Recommendation",
        "recommendation/user.txt": "User {{CAMPAIGN_TARGET}} {{BUSINESS_DOMAIN}} {{CAMPAIGN_DATA}} {{ANALYSIS_JSON}}",
        "evaluation/analysis_system.txt": "Eval Analysis System",
        "evaluation/analysis_user.txt": "Eval User {{CAMPAIGN_CONTEXT}} {{RAW_DATA}} {{ANALYSIS_REPORT}}",
        "evaluation/recommendation_system.txt": "Eval Rec System",
        "evaluation/recommendation_user.txt": "Eval User {{BUSINESS_CONTEXT}} {{RAW_DATA}} {{ANALYSIS_CONTEXT}} {{RECOMMENDATION}}",
    }.get(path, "Unknown Prompt")
    return loader

def test_BuildAnalysisPrompt_ShouldReplacePlaceholders_WhenValidDataProvided(mock_loader):
    """Verify that analysis prompt is built with correct replacements."""
    # Arrange
    builder = PromptBuilder(loader=mock_loader)
    campaign_data = {"id": 1}
    business_domain = {"domain": "tech"}
    campaign_target = {"goal": "clicks"}
    
    # Act
    messages = builder.build_analysis_prompt(
        campaign_data=campaign_data,
        business_domain=business_domain,
        campaign_target=campaign_target
    )
    
    # Assert
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "System Analysis"
    assert messages[1]["role"] == "user"
    assert builder._to_json(campaign_data) in messages[1]["content"]
    assert builder._to_json(business_domain) in messages[1]["content"]
    assert builder._to_json(campaign_target) in messages[1]["content"]

def test_BuildAnalysisPrompt_ShouldRaiseValueError_WhenPlaceholdersRemainInStrict(mock_loader):
    """Verify that strict mode raises ValueError if placeholders remain."""
    # Arrange
    builder = PromptBuilder(loader=mock_loader)
    
    # Act & Assert
    # Passing the placeholder as data should trigger failure in strict mode
    # because the placeholder string will end up in the final prompt.
    with pytest.raises(ValueError, match="unreplaced placeholder"):
        builder.build_analysis_prompt(
            campaign_data="{{CAMPAIGN_DATA}}",
            business_domain={},
            campaign_target={}
        )

def test_BuildRecommendationPrompt_ShouldReplacePlaceholders_WhenValidDataProvided(mock_loader):
    """Verify that recommendation prompt is built with correct replacements."""
    # Arrange
    builder = PromptBuilder(loader=mock_loader)
    campaign_target = {"target": 1}
    business_domain = {"domain": 2}
    campaign_data = {"data": 3}
    analysis_json = {"analysis": 4}
    
    # Act
    messages = builder.build_recommendation_prompt(
        campaign_target=campaign_target,
        business_domain=business_domain,
        campaign_data=campaign_data,
        analysis_json=analysis_json
    )
    
    # Assert
    assert len(messages) == 2
    assert messages[0]["content"] == "System Recommendation"
    assert builder._to_json(analysis_json) in messages[1]["content"]

def test_BuildAnalysisEvaluationPrompt_ShouldReplacePlaceholders_WhenValidDataProvided(mock_loader):
    """Verify that analysis evaluation prompt is built with correct replacements."""
    # Arrange
    builder = PromptBuilder(loader=mock_loader)
    campaign_data = {"data": 1}
    analysis_report = {"report": 2}
    campaign_target = {"target": 3}
    business_domain = {"domain": 4}
    
    # Act
    messages = builder.build_analysis_evaluation_prompt(
        campaign_data=campaign_data,
        analysis_report=analysis_report,
        campaign_target=campaign_target,
        business_domain=business_domain
    )
    
    # Assert
    assert len(messages) == 2
    assert messages[0]["content"] == "Eval Analysis System"
    assert builder._to_json(campaign_data) in messages[1]["content"]
    assert builder._to_json(analysis_report) in messages[1]["content"]

def test_BuildRecommendationEvaluationPrompt_ShouldReplacePlaceholders_WhenValidDataProvided(mock_loader):
    """Verify that recommendation evaluation prompt is built with correct replacements."""
    # Arrange
    builder = PromptBuilder(loader=mock_loader)
    business_domain = {"domain": 1}
    campaign_target = {"target": 2}
    campaign_data = {"data": 3}
    analysis_context = {"analysis": 4}
    recommendation = {"rec": 5}
    
    # Act
    messages = builder.build_recommendation_evaluation_prompt(
        business_domain=business_domain,
        campaign_target=campaign_target,
        campaign_data=campaign_data,
        analysis_context=analysis_context,
        recommendation=recommendation
    )
    
    # Assert
    assert len(messages) == 2
    assert messages[0]["content"] == "Eval Rec System"
    assert builder._to_json(campaign_data) in messages[1]["content"]
    assert builder._to_json(recommendation) in messages[1]["content"]
