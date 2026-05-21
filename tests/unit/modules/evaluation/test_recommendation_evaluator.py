import pytest
from unittest.mock import patch, MagicMock
from src.modules.evaluation.recommendation_evaluator import RecommendationEvaluator

@pytest.fixture
def mock_llm_client():
    with patch("src.modules.evaluation.recommendation_evaluator.LLMApiClient") as mock:
        yield mock

def test_Evaluate_ShouldReturnScoresIncludingFeasibility_WhenValidReportProvided(mock_llm_client):
    """Verify that evaluate method returns correct scores including feasibility."""
    # Arrange
    evaluator = RecommendationEvaluator()
    mock_instance = mock_llm_client.return_value
    mock_instance.generate_json.return_value = {
        "evaluation": {
            "clarity_score": 3,
            "clarity_reasoning": "Clear rec",
            "accuracy_score": 3,
            "accuracy_reasoning": "Accurate",
            "structure_score": 2,
            "structure_reasoning": "Okay structure",
            "feasibility_score": 3,
            "feasibility_reasoning": "Highly feasible",
            "verdict": "accept",
            "key_issues": [],
            "improvement_suggestions": []
        }
    }
    
    # Act
    result = evaluator.evaluate(
        business_context={},
        campaign_target={},
        campaign_data={},
        analysis_context={},
        recommendation={}
    )
    
    # Assert
    assert result["scores"]["clarity"] == 3
    assert result["scores"]["feasibility"] == 3
    assert result["scores"]["overall"] == 2.75
    assert result["reasoning"]["feasibility"] == "Highly feasible"
    mock_instance.generate_json.assert_called_once()

def test_Evaluate_ShouldHandleMissingFeasibility_WhenLLMOmitsIt(mock_llm_client):
    """Verify that evaluate handles missing feasibility score (optional in schema)."""
    # Arrange
    evaluator = RecommendationEvaluator()
    mock_instance = mock_llm_client.return_value
    mock_instance.generate_json.return_value = {
        "evaluation": {
            "clarity_score": 3,
            "accuracy_score": 3,
            "structure_score": 2,
            # feasibility omitted
        }
    }
    
    # Act
    result = evaluator.evaluate({}, {}, {}, {}, {})
    
    # Assert
    assert result["scores"]["feasibility"] == 0
    # (3+3+2+0)/4 = 2.0
    assert result["scores"]["overall"] == 2.0
