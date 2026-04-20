import pytest
import pandas as pd
from src.core.execution_context import ExecutionContext

def test_execution_context_initialization():
    """Verify that ExecutionContext initializes with default values."""
    ctx = ExecutionContext()
    assert ctx.metadata == {}
    assert ctx.raw_df is None
    assert ctx.processed_df is None
    assert ctx.enriched_data == {}
    assert ctx.analysis_results == {}
    assert ctx.recommendation_results == {}
    assert ctx.evaluations == {}
    assert ctx.runtime_output_path is None
    assert ctx.errors == []

def test_execution_context_metadata_methods():
    """Verify set_metadata and get_metadata methods."""
    ctx = ExecutionContext()
    ctx.set_metadata("campaign_id", "456")
    assert ctx.get_metadata("campaign_id") == "456"
    assert ctx.get_metadata("non_existent", "default") == "default"

def test_execution_context_dataframe_storage():
    """Verify that DataFrames can be stored and retrieved."""
    ctx = ExecutionContext()
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    ctx.raw_df = df
    pd.testing.assert_frame_equal(ctx.raw_df, df)
