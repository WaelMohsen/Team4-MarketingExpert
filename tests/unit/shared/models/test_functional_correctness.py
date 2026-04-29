import pytest
from src.shared.models.llm_responses import validate_recommendation_output, validate_analysis_output

def get_valid_recommendation_item():
    return {
        "title": "Boost Ad Spend",
        "whats_happening": "CTR is dropping",
        "what_you_should_do": ["Increase budget", "Change creative"],
        "why_this_matters": "To get more clicks",
        "priority": "High",
        "expected_impact": "Higher CTR",
        "owner_suggestion": "Marketing Team"
    }

def get_valid_recommendation_output():
    return {
        "recommendations": [get_valid_recommendation_item() for _ in range(5)]
    }

def test_ValidateRecommendationOutput_ShouldReturnTrue_WhenOutputIsValid():
    # Act & Assert
    assert validate_recommendation_output(get_valid_recommendation_output()) is True

def test_ValidateRecommendationOutput_ShouldReturnFalse_WhenLessThan5ItemsProvided():
    # Arrange
    data = get_valid_recommendation_output()
    data["recommendations"].pop() # Now 4 items
    
    # Act & Assert
    assert validate_recommendation_output(data) is False

def test_ValidateRecommendationOutput_ShouldReturnFalse_WhenFieldsAreMissing():
    # Arrange
    data = get_valid_recommendation_output()
    del data["recommendations"][0]["title"]
    
    # Act & Assert
    assert validate_recommendation_output(data) is False

def test_ValidateRecommendationOutput_ShouldReturnFalse_WhenPriorityIsInvalid():
    # Arrange
    data = get_valid_recommendation_output()
    data["recommendations"][0]["priority"] = "Urgent" # Valid are High, Medium, Low
    
    # Act & Assert
    assert validate_recommendation_output(data) is False

def test_ValidateRecommendationOutput_ShouldReturnFalse_WhenActionsListIsEmpty():
    # Arrange
    data = get_valid_recommendation_output()
    data["recommendations"][0]["what_you_should_do"] = []
    
    # Act & Assert
    assert validate_recommendation_output(data) is False

def get_valid_analysis_output():
    return {
        "analysis": {
            "executive_summary": "This is a sufficiently long summary for testing.",
            "budget_and_efficiency": [],
            "results_and_value": [],
            "cross_channel_patterns_and_risks": [],
            "channel_notes": [
                {
                    "platform": "Google Ads",
                    "what_we_see": ["High CPC"],
                    "what_it_likely_means": ["Increased competition"],
                    "risks_or_watchouts": []
                }
            ],
            "missing_info": []
        }
    }

def test_ValidateAnalysisOutput_ShouldReturnTrue_WhenOutputIsValid():
    # Act & Assert
    assert validate_analysis_output(get_valid_analysis_output()) is True

def test_ValidateAnalysisOutput_ShouldReturnFalse_WhenSummaryIsTooShort():
    # Arrange
    data = get_valid_analysis_output()
    data["analysis"]["executive_summary"] = "Too short"
    
    # Act & Assert
    assert validate_analysis_output(data) is False

def test_ValidateAnalysisOutput_ShouldReturnFalse_WhenChannelNotesAreEmpty():
    # Arrange
    data = get_valid_analysis_output()
    data["analysis"]["channel_notes"] = []
    
    # Act & Assert
    assert validate_analysis_output(data) is False

def test_ValidateAnalysisOutput_ShouldReturnFalse_WhenObservationsAreEmpty():
    # Arrange
    data = get_valid_analysis_output()
    data["analysis"]["channel_notes"][0]["what_we_see"] = []
    
    # Act & Assert
    assert validate_analysis_output(data) is False

def test_ValidateAnalysisOutput_ShouldReturnFalse_WhenFieldIsMissing():
    # Arrange
    data = get_valid_analysis_output()
    del data["analysis"]["executive_summary"]
    
    # Act & Assert
    assert validate_analysis_output(data) is False
