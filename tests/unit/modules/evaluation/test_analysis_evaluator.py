import pytest
from unittest.mock import patch, MagicMock
from src.modules.evaluation.analysis_evaluator import AnalysisEvaluator

@pytest.fixture
def mock_llm_client():
    with patch("src.modules.evaluation.analysis_evaluator.LLMApiClient") as mock:
        yield mock

def test_Evaluate_ShouldReturnScores_WhenValidReportProvided(mock_llm_client):
    """Verify that evaluate method returns correct scores and reasoning."""
    # Arrange
    evaluator = AnalysisEvaluator()
    mock_instance = mock_llm_client.return_value
    mock_instance.generate_json.return_value = {
        "evaluation": {
            "clarity_score": 3,
            "clarity_reasoning": "Clear report",
            "accuracy_score": 2,
            "accuracy_reasoning": "Mostly accurate",
            "structure_score": 3,
            "structure_reasoning": "Well structured",
            "verdict": "accept",
            "key_issues": [],
            "improvement_suggestions": ["More data"]
        }
    }
    
    # Act
    result = evaluator.evaluate(
        campaign_data={},
        analysis_report={},
        campaign_target={},
        business_domain={}
    )
    
    # Assert
    assert result["scores"]["clarity"] == 3
    assert result["scores"]["accuracy"] == 2
    assert result["scores"]["structure"] == 3
    assert result["scores"]["overall"] == pytest.approx(2.666, 0.001)
    assert result["verdict"] == "accept"
    assert result["reasoning"]["clarity"] == "Clear report"
    mock_instance.generate_json.assert_called_once()

def test_Evaluate_ShouldHandleMissingData_WhenLLMReturnsPartialData(mock_llm_client):
    """Verify that evaluate handles missing fields from LLM gracefully."""
    # Arrange
    evaluator = AnalysisEvaluator()
    mock_instance = mock_llm_client.return_value
    # LLM returns empty evaluation
    mock_instance.generate_json.return_value = {"evaluation": {}}
    
    # Act
    result = evaluator.evaluate(
        campaign_data={},
        analysis_report={},
        campaign_target={},
        business_domain={}
    )
    
    # Assert
    assert result["scores"]["clarity"] == 0
    assert result["scores"]["overall"] == 0
    assert result["reasoning"]["clarity"] is None

def test_Evaluate_ShouldRaiseError_WhenLLMFails(mock_llm_client):
    """Verify that evaluate propagates errors from LLM client."""
    # Arrange
    evaluator = AnalysisEvaluator()
    mock_instance = mock_llm_client.return_value
    mock_instance.generate_json.side_effect = RuntimeError("LLM Failure")
    
    # Act & Assert
    with pytest.raises(RuntimeError, match="LLM Failure"):
        evaluator.evaluate({}, {}, {}, {})
