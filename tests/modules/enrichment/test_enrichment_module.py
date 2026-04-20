import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from src.modules.enrichment.enrichment_module import EnrichmentModule
from src.core.execution_context import ExecutionContext

@pytest.fixture
def enrichment_module():
    return EnrichmentModule()

def test_enrichment_module_run_success(enrichment_module):
    """Verify that EnrichmentModule builds the summary and extracts features."""
    ctx = ExecutionContext()
    ctx.processed_df = pd.DataFrame({
        "platform": ["Google"],
        "campaign_name": ["C1"],
        "date": ["2024-01-01"],
        "spend": [100],
        "impressions": [1000],
        "clicks": [50],
        "conversions": [5],
        "conversion_value": [500]
    })
    
    updated_ctx = enrichment_module.run(ctx)
    
    assert updated_ctx.enriched_data is not None
    payload = updated_ctx.enriched_data["campaign_data"]
    assert payload["campaign_identity"]["platform"] == "Google"
    assert payload["performance_metrics"]["spend"] == 100.0
    assert "automated_diagnostics" in payload

def test_enrichment_module_missing_data(enrichment_module):
    """Verify error when processed_df is missing."""
    ctx = ExecutionContext()
    with pytest.raises(ValueError, match="Row data not found"):
        enrichment_module.run(ctx)

def test_enrichment_module_save(enrichment_module):
    """Verify that EnrichmentModule saves enriched data."""
    ctx = ExecutionContext()
    ctx.enriched_data = {
        "campaign_data": {"id": 1},
        "processed_df": pd.DataFrame({"a": [1]})
    }
    ctx.runtime_output_path = "test_enrich_dir"
    
    with patch("os.makedirs") as mock_makedirs:
        with patch("builtins.open", MagicMock()):
            with patch("pandas.DataFrame.to_csv") as mock_to_csv:
                enrichment_module.save(ctx)
                mock_makedirs.assert_called_once()
                mock_to_csv.assert_called_once()
