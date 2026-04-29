import pytest
import pandas as pd
from unittest.mock import patch
from src.modules.preprocessing.preprocessing_module import PreprocessingModule
from src.core.execution_context import ExecutionContext

@pytest.fixture
def preprocessing_module():
    return PreprocessingModule()

def test_Run_ShouldCleanDataAndComputeKpis_WhenValidDataProvided(preprocessing_module):
    """Verify that PreprocessingModule cleaned the data and computed KPIs."""
    # Arrange
    ctx = ExecutionContext()
    ctx.raw_df = pd.DataFrame({
        "date": ["2024-01-01"],
        "impressions": [1000],
        "clicks": [100],
        "spend": [50.0],
        "conversions": [10],
        "conversion_value": [500.0]
    })
    
    # Act
    updated_ctx = preprocessing_module.run(ctx)
    
    # Assert
    assert updated_ctx.processed_df is not None
    # Preprocessing does not compute KPIs by default, that's done in Enrichment
    assert "date" in updated_ctx.processed_df.columns

def test_Run_ShouldRaiseValueError_WhenRawDfIsMissing(preprocessing_module):
    """Verify error when raw_df is missing."""
    # Arrange
    ctx = ExecutionContext()
    
    # Act & Assert
    with pytest.raises(ValueError, match="Raw DataFrame not found"):
        preprocessing_module.run(ctx)

def test_Save_ShouldPersistProcessedCsv_WhenOutputDirectoryExists(preprocessing_module):
    """Verify that PreprocessingModule saves the processed CSV."""
    # Arrange
    ctx = ExecutionContext()
    ctx.processed_df = pd.DataFrame({"a": [1]})
    ctx.set_metadata("output_json_dir", "test_output")
    
    # Act
    with patch("os.makedirs") as mock_makedirs:
        with patch.object(pd.DataFrame, "to_csv") as mock_to_csv:
            preprocessing_module.save(ctx)
            
            # Assert
            mock_makedirs.assert_called_once()
            mock_to_csv.assert_called_once()
            # Verify path logic
            args, _ = mock_to_csv.call_args
            assert "processed_data.csv" in args[0]
