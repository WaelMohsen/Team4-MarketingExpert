import pytest
import os
import json
from unittest.mock import patch, MagicMock
from src.modules.analysis.analysis_module import AnalysisModule
from src.core.execution_context import ExecutionContext

@pytest.fixture
def analysis_module():
    with patch("src.shared.utils.llm_client.OpenAI"): # Avoid OpenAI init
        return AnalysisModule()

def test_analysis_module_run_success(analysis_module):
    """Verify that AnalysisModule generates results when data is present."""
    ctx = ExecutionContext()
    ctx.enriched_data = {"campaign_data": {"clicks": 100}}
    ctx.set_metadata("business_domain", {"domain": "test"})
    
    mock_result = {"analysis": "good progress"}
    
    with patch.object(analysis_module.client, "generate_json", return_value=mock_result) as mock_gen:
        updated_ctx = analysis_module.run(ctx)
        
        assert updated_ctx.analysis_results == mock_result
        mock_gen.assert_called_once()

def test_analysis_module_missing_enriched_data(analysis_module):
    """Verify error when enriched_data is missing."""
    ctx = ExecutionContext()
    with pytest.raises(ValueError, match="Enriched data not found"):
        analysis_module.run(ctx)

def test_analysis_module_save(analysis_module):
    """Verify that AnalysisModule saves results to JSON."""
    ctx = ExecutionContext()
    ctx.analysis_results = {"key": "value"}
    ctx.runtime_output_path = "test_run_dir"
    
    with patch("os.makedirs") as mock_makedirs:
        with patch("builtins.open", MagicMock()) as mock_open:
            analysis_module.save(ctx)
            mock_makedirs.assert_called_once_with("test_run_dir", exist_ok=True)
            mock_open.assert_called_once()
            # Check filename
            args, _ = mock_open.call_args
            assert "analysis_result.json" in args[0]
