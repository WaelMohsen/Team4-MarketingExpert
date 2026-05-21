import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from src.modules.enrichment.enrichment_module import EnrichmentModule
from src.core.execution_context import ExecutionContext

@pytest.fixture
def enrichment_module():
    return EnrichmentModule()

def test_Run_ShouldBuildSummaryAndExtractFeatures_WhenValidDataProvided(enrichment_module):
    """Verify that EnrichmentModule builds the summary and extracts features."""
    # Arrange
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
    
    # Act
    updated_ctx = enrichment_module.run(ctx)
    
    # Assert
    assert updated_ctx.enriched_data is not None
    payload = updated_ctx.enriched_data["campaign_data"]
    assert payload[0]["campaign_identity"]["platform"] == "Google"
    assert payload[0]["performance_metrics"]["spend"] == 100.0

def test_Run_ShouldRaiseValueError_WhenProcessedDfIsMissing(enrichment_module):
    """Verify error when processed_df is missing."""
    # Arrange
    ctx = ExecutionContext()
    
    # Act & Assert
    with pytest.raises(ValueError, match="Row data not found"):
        enrichment_module.run(ctx)

def test_Save_ShouldPersistEnrichedData_WhenOutputDirectoryExists(enrichment_module):
    """Verify that EnrichmentModule saves enriched data."""
    # Arrange
    ctx = ExecutionContext()
    ctx.enriched_data = {
        "campaign_data": [{"id": 1}],
        "processed_df": pd.DataFrame({"a": [1]})
    }
    ctx.runtime_output_path = "test_enrich_dir"
    
    # Act
    with patch("os.makedirs") as mock_makedirs:
        with patch("builtins.open", MagicMock()):
            with patch("pandas.DataFrame.to_csv") as mock_to_csv:
                enrichment_module.save(ctx)
                
                # Assert
                mock_makedirs.assert_called_once()
                mock_to_csv.assert_called_once()
