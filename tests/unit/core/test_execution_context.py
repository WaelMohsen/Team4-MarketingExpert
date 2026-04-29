import pytest
import pandas as pd
from src.core.execution_context import ExecutionContext

def test_Initialization_ShouldSetDefaultValues_WhenContextIsCreated():
    """Verify that ExecutionContext initializes with default values."""
    # Act
    ctx = ExecutionContext()
    
    # Assert
    assert ctx.raw_df is None
    assert ctx.processed_df is None
    assert ctx.enriched_data == {}
    assert ctx.analysis_results == {}
    assert ctx.recommendation_results == {}
    assert ctx.evaluations == {}
    assert ctx.metadata == {}
    assert ctx.runtime_output_path is None
    assert ctx.errors == []

def test_Metadata_ShouldStoreAndRetrieveValues_WhenCalled():
    """Verify metadata storage and retrieval."""
    # Arrange
    ctx = ExecutionContext()
    
    # Act
    ctx.set_metadata("key", "value")
    
    # Assert
    assert ctx.get_metadata("key") == "value"
    assert ctx.get_metadata("missing", "default") == "default"

def test_DataFrameStorage_ShouldMaintainDataIntegrity_WhenStoredInContext():
    """Verify that DataFrames can be stored and retrieved."""
    # Arrange
    ctx = ExecutionContext()
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    
    # Act
    ctx.raw_df = df
    
    # Assert
    pd.testing.assert_frame_equal(ctx.raw_df, df)
