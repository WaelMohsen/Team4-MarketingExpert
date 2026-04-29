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
    }.get(path, "Unknown Prompt")
    return loader

def test_build_analysis_prompt(mock_loader):
    """Verify that analysis prompt is built with correct replacements."""
    builder = PromptBuilder(loader=mock_loader)
    campaign_data = {"id": 1}
    business_domain = {"domain": "tech"}
    campaign_target = {"goal": "clicks"}
    
    messages = builder.build_analysis_prompt(
        campaign_data=campaign_data,
        business_domain=business_domain,
        campaign_target=campaign_target
    )
    
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "System Analysis"
    assert messages[1]["role"] == "user"
    assert builder._to_json(campaign_data) in messages[1]["content"]
    assert builder._to_json(business_domain) in messages[1]["content"]
    assert builder._to_json(campaign_target) in messages[1]["content"]

def test_build_analysis_prompt_strict_failure(mock_loader):
    """Verify that strict mode raises ValueError if placeholders remain."""
    builder = PromptBuilder(loader=mock_loader)
    # Passing the placeholder as data should trigger failure in strict mode
    # because the placeholder string will end up in the final prompt.
    with pytest.raises(ValueError, match="unreplaced placeholder"):
        builder.build_analysis_prompt(
            campaign_data="{{CAMPAIGN_DATA}}",
            business_domain={},
            campaign_target={}
        )

def test_build_recommendation_prompt(mock_loader):
    """Verify that recommendation prompt is built with correct replacements."""
    builder = PromptBuilder(loader=mock_loader)
    campaign_target = {"target": 1}
    business_domain = {"domain": 2}
    campaign_data = {"data": 3}
    analysis_json = {"analysis": 4}
    
    messages = builder.build_recommendation_prompt(
        campaign_target=campaign_target,
        business_domain=business_domain,
        campaign_data=campaign_data,
        analysis_json=analysis_json
    )
    
    assert len(messages) == 2
    assert messages[0]["content"] == "System Recommendation"
    assert builder._to_json(analysis_json) in messages[1]["content"]
