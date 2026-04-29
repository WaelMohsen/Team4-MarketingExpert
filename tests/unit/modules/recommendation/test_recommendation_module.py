import pytest
import os
import json
from unittest.mock import patch, MagicMock
from src.modules.recommendation.recommendation_module import RecommendationModule
from src.core.execution_context import ExecutionContext

@pytest.fixture
def recommendation_module():
    with patch("src.shared.utils.llm_client.OpenAI"): # Avoid OpenAI init
        return RecommendationModule()

def test_Run_ShouldGenerateResults_WhenAnalysisIsPresent(recommendation_module):
    """Verify that RecommendationModule generates results when analysis is present."""
    # Arrange
    ctx = ExecutionContext()
    ctx.analysis_results = {"analysis": "some finding"}
    ctx.enriched_data = {"campaign_data": {"id": 1}}
    
    mock_result = {"recommendations": ["do this", "do that"]}
    
    # Act
    with patch.object(recommendation_module.client, "generate_json", return_value=mock_result) as mock_gen:
        updated_ctx = recommendation_module.run(ctx)
        
        # Assert
        assert updated_ctx.recommendation_results == mock_result
        mock_gen.assert_called_once()

def test_Run_ShouldRaiseValueError_WhenAnalysisResultsIsMissing(recommendation_module):
    """Verify error when analysis_results is missing."""
    # Arrange
    ctx = ExecutionContext()
    
    # Act & Assert
    with pytest.raises(ValueError, match="Analysis results not found"):
        recommendation_module.run(ctx)

def test_Save_ShouldPersistRecommendationsToJson_WhenOutputDirectoryExists(recommendation_module):
    """Verify that RecommendationModule saves results to JSON."""
    # Arrange
    ctx = ExecutionContext()
    ctx.recommendation_results = {"rec": "123"}
    ctx.runtime_output_path = "test_run_dir_rec"
    
    # Act
    with patch("os.makedirs") as mock_makedirs:
        with patch("builtins.open", MagicMock()) as mock_open:
            recommendation_module.save(ctx)
            
            # Assert
            mock_makedirs.assert_called_once_with("test_run_dir_rec", exist_ok=True)
            mock_open.assert_called_once()
            # Check filename
            args, _ = mock_open.call_args
            assert "recommendation_result.json" in args[0]
