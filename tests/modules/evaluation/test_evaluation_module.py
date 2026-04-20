import pytest
import os
import json
from unittest.mock import patch, MagicMock
from src.modules.evaluation.evaluation_module import EvaluationModule
from src.core.execution_context import ExecutionContext

@pytest.fixture
def evaluation_module():
    with patch("src.shared.utils.llm_client.OpenAI"): # Avoid OpenAI init
        return EvaluationModule()

def test_evaluation_module_run_success(evaluation_module):
    """Verify that EvaluationModule calls evaluators correctly."""
    ctx = ExecutionContext()
    ctx.analysis_results = {"finding": "abc"}
    ctx.recommendation_results = {"recommendations": [{"title": "Rec1"}]}
    ctx.enriched_data = {"campaign_data": {"id": 1}}
    
    with patch.object(evaluation_module.analysis_evaluator, "evaluate", return_value={"score": 5}) as mock_anal:
        with patch.object(evaluation_module.recommendation_evaluator, "evaluate", return_value={"score": 8}) as mock_rec:
            updated_ctx = evaluation_module.run(ctx)
            
            assert updated_ctx.evaluations["analysis"] == {"score": 5}
            assert len(updated_ctx.evaluations["recommendations"]) == 1
            assert updated_ctx.evaluations["recommendations"][0]["evaluation"] == {"score": 8}
            
            mock_anal.assert_called_once()
            mock_rec.assert_called_once()

def test_evaluation_module_save(evaluation_module):
    """Verify that EvaluationModule saves results."""
    ctx = ExecutionContext()
    ctx.evaluations = {
        "analysis": {"score": 5},
        "recommendations": [{"card_title": "R1", "evaluation": {"score": 8}}]
    }
    ctx.runtime_output_path = "test_eval_dir"
    
    with patch("os.makedirs") as mock_makedirs:
        with patch("builtins.open", MagicMock()) as mock_open:
            evaluation_module.save(ctx)
            assert mock_makedirs.call_count == 1
            assert mock_open.call_count == 2 # One for analysis, one for recommendations
