import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.api.app import app
from src.core.execution_context import ExecutionContext

client = TestClient(app)

def test_Root_ShouldReturnWelcomeMessage_WhenAccessed():
    """Verify that the root endpoint returns the welcome message."""
    # Act
    response = client.get("/")
    
    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Marketing Intelligence API"}

@patch("src.api.app.enrichment_module")
@patch("src.api.app.analysis_module")
def test_Analyze_ShouldReturnResults_WhenValidDataProvided(mock_analysis, mock_enrichment):
    """Verify that the analysis endpoint executes enrichment and analysis."""
    # Arrange
    mock_enrichment.run.side_effect = lambda ctx: ctx
    
    def mock_analysis_run(ctx):
        ctx.analysis_results = {"analysis": "result"}
        return ctx
    mock_analysis.run.side_effect = mock_analysis_run
    
    payload = {
        "campaign_data": {"platform": "Google", "spend": 100},
        "business_domain": {"domain": "tech"},
        "campaign_target": {"goal": "leads"}
    }
    
    # Act
    response = client.post("/api/v1/analysis", json=payload)
    
    # Assert
    assert response.status_code == 200
    assert response.json() == {"analysis": "result"}
    mock_enrichment.run.assert_called_once()
    mock_analysis.run.assert_called_once()

@patch("src.api.app.enrichment_module")
@patch("src.api.app.analysis_module")
@patch("src.api.app.recommendation_module")
def test_Recommend_ShouldReturnResults_WhenValidDataProvided(mock_rec, mock_analysis, mock_enrichment):
    """Verify that the recommendation endpoint executes correctly."""
    # Arrange
    mock_enrichment.run.side_effect = lambda ctx: ctx
    mock_analysis.run.side_effect = lambda ctx: ctx
    
    def mock_rec_run(ctx):
        ctx.recommendation_results = {"recommendations": []}
        return ctx
    mock_rec.run.side_effect = mock_rec_run
    
    payload = {
        "campaign_data": {"platform": "Google", "spend": 100},
        "analysis_results": {"analysis": "existing"}
    }
    
    # Act
    response = client.post("/api/v1/recommendation", json=payload)
    
    # Assert
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["analysis_used"] == {"analysis": "existing"}
    assert res_json["recommendations"] == {"recommendations": []}
    mock_enrichment.run.assert_called_once()
    mock_rec.run.assert_called_once()
    # Analysis should NOT be called because analysis_results were provided
    mock_analysis.run.assert_not_called()

def test_Analyze_ShouldReturn500_WhenModuleFails():
    """Verify that the analysis endpoint returns 500 when an error occurs."""
    # Arrange
    with patch("src.api.app.enrichment_module.run", side_effect=Exception("Crash")):
        payload = {"campaign_data": {}}
        
        # Act
        response = client.post("/api/v1/analysis", json=payload)
        
        # Assert
        assert response.status_code == 500
        assert "Crash" in response.json()["detail"]
