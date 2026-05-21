import os
import pytest

# Set dummy API key for tests before importing app
os.environ["OPENAI_API_KEY"] = "sk-dummy"

from fastapi.testclient import TestClient
from src.api.app import app

client = TestClient(app)

def test_Root_ShouldReturnWelcomeMessage_WhenCalled():
    # Act
    response = client.get("/")
    
    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Marketing Intelligence API"}

@pytest.fixture
def mock_enrichment_module(mocker):
    return mocker.patch("src.api.app.enrichment_module.run")

@pytest.fixture
def mock_analysis_module(mocker):
    return mocker.patch("src.api.app.analysis_module.run")

@pytest.fixture
def mock_recommendation_module(mocker):
    return mocker.patch("src.api.app.recommendation_module.run")

def test_AnalysisEndpoint_ShouldReturnResults_WhenValidPayloadProvided(mock_enrichment_module, mock_analysis_module):
    # Arrange
    # Mock enrichment return value
    from src.core.execution_context import ExecutionContext
    mock_context = ExecutionContext()
    mock_context.enriched_data = {"campaign_data": {"enriched": True}}
    mock_enrichment_module.return_value = mock_context
    
    # Mock analysis return value
    mock_context_final = ExecutionContext()
    mock_context_final.analysis_results = {"analysis": {"executive_summary": "Test summary"}}
    mock_analysis_module.return_value = mock_context_final

    payload = {
        "campaign_data": {"spend": 100},
        "business_domain": {"industry": "Retail"},
        "campaign_target": {"primary_goal": "growth"}
    }
    
    # Act
    response = client.post("/api/v1/analysis", json=payload)
    
    # Assert
    assert response.status_code == 200
    assert response.json() == {"analysis": {"executive_summary": "Test summary"}}
    
    # Verify modules were called
    mock_enrichment_module.assert_called_once()
    mock_analysis_module.assert_called_once()

def test_RecommendationEndpoint_ShouldRunAnalysis_WhenAnalysisNotProvided(mock_enrichment_module, mock_analysis_module, mock_recommendation_module):
    # Arrange
    # Mock enrichment return value
    from src.core.execution_context import ExecutionContext
    mock_context_enriched = ExecutionContext()
    mock_context_enriched.enriched_data = {"campaign_data": {"enriched": True}}
    mock_enrichment_module.return_value = mock_context_enriched

    # Mock analysis return value
    mock_context_analysis = ExecutionContext()
    mock_context_analysis.analysis_results = {"analysis": {"executive_summary": "Auto analysis"}}
    mock_analysis_module.return_value = mock_context_analysis

    # Mock recommendation return value
    # Ensure it includes the analysis_results so the response contains them
    mock_context_final = ExecutionContext()
    mock_context_final.analysis_results = {"analysis": {"executive_summary": "Auto analysis"}}
    mock_context_final.recommendation_results = {"recommendations": []}
    mock_recommendation_module.return_value = mock_context_final

    payload = {
        "campaign_data": {"spend": 100},
        "business_domain": {"industry": "Retail"},
        "campaign_target": {"primary_goal": "growth"}
    }
    
    # Act
    response = client.post("/api/v1/recommendation", json=payload)
    
    # Assert
    assert response.status_code == 200
    assert response.json()["analysis_used"] == {"analysis": {"executive_summary": "Auto analysis"}}
    assert response.json()["recommendations"] == {"recommendations": []}
    
    # Verify all modules were called in sequence
    mock_enrichment_module.assert_called_once()
    mock_analysis_module.assert_called_once()
    mock_recommendation_module.assert_called_once()

def test_RecommendationEndpoint_ShouldSkipAnalysis_WhenAnalysisProvided(mock_enrichment_module, mock_analysis_module, mock_recommendation_module):
    # Arrange
    # Mock enrichment return value
    from src.core.execution_context import ExecutionContext
    mock_context_enriched = ExecutionContext()
    mock_context_enriched.enriched_data = {"campaign_data": {"enriched": True}}
    mock_enrichment_module.return_value = mock_context_enriched

    # Mock recommendation return value
    mock_context_final = ExecutionContext()
    mock_context_final.analysis_results = {"analysis": {"executive_summary": "Provided analysis"}}
    mock_context_final.recommendation_results = {"recommendations": []}
    mock_recommendation_module.return_value = mock_context_final

    payload = {
        "analysis_results": {"analysis": {"executive_summary": "Provided analysis"}},
        "campaign_data": {"spend": 100},
        "business_domain": {"industry": "Retail"},
        "campaign_target": {"primary_goal": "growth"}
    }
    
    # Act
    response = client.post("/api/v1/recommendation", json=payload)
    
    # Assert
    assert response.status_code == 200
    assert response.json()["analysis_used"] == {"analysis": {"executive_summary": "Provided analysis"}}
    
    # Verify analysis_module was NOT called because analysis was provided
    mock_enrichment_module.assert_called_once()
    mock_analysis_module.assert_not_called()
    mock_recommendation_module.assert_called_once()

def test_AnalysisEndpoint_ShouldReturn500_WhenModuleFails(mock_analysis_module):
    # Arrange
    mock_analysis_module.side_effect = Exception("API Error")
    
    payload = {
        "campaign_data": {"spend": 100}
    }
    
    # Act
    response = client.post("/api/v1/analysis", json=payload)
    
    # Assert
    assert response.status_code == 500
    assert "API Error" in response.json()["detail"]
