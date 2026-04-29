import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from src.modules.ingestion.ingestion_module import IngestionModule
from src.core.execution_context import ExecutionContext

@pytest.fixture
def ingestion_module():
    return IngestionModule()

def test_ingestion_module_run_success(ingestion_module):
    """Verify that IngestionModule loads and validates data correctly."""
    ctx = ExecutionContext()
    ctx.set_metadata("input_csv", "path/to/data.csv")
    
    # Mock DataLoader to return a valid DataFrame
    valid_df = pd.DataFrame({
        "Day": ["2024-01-01"],
        "Platform": ["Google"],
        "Campaign Type": ["Search"],
        "Impr": [1000],
        "Clicks": [50],
        "Cost": [100.0]
    })
    
    with patch.object(ingestion_module.loader, "load", return_value=valid_df):
        updated_ctx = ingestion_module.run(ctx)
        
        # Verify raw_df is in context and canonicalized
        assert updated_ctx.raw_df is not None
        assert "date" in updated_ctx.raw_df.columns
        assert "spend" in updated_ctx.raw_df.columns
        assert updated_ctx.raw_df.iloc[0]["spend"] == 100.0

def test_ingestion_module_run_missing_source(ingestion_module):
    """Verify error when input_csv is missing in metadata."""
    ctx = ExecutionContext()
    with pytest.raises(ValueError, match="Input CSV source not found"):
        ingestion_module.run(ctx)

def test_ingestion_module_save(ingestion_module):
    """Verify that IngestionModule saves the audit CSV."""
    ctx = ExecutionContext()
    ctx.raw_df = pd.DataFrame({"a": [1]})
    ctx.set_metadata("output_json_dir", "test_output")
    
    with patch("os.makedirs") as mock_makedirs:
        with patch.object(pd.DataFrame, "to_csv") as mock_to_csv:
            ingestion_module.save(ctx)
            mock_makedirs.assert_called_once()
            mock_to_csv.assert_called_once()
            # Verify path logic (audit/ingested_data.csv)
            args, _ = mock_to_csv.call_args
            assert "audit" in args[0]
            assert "ingested_data.csv" in args[0]
            assert "test_output" in args[0]
