import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from src.modules.ingestion.loader import DataLoader

def test_data_loader_from_dataframe():
    """Verify loading from an existing DataFrame."""
    df = pd.DataFrame({" col1 ": [1], "col2": [None]})
    loader = DataLoader(strip_column_whitespace=True, drop_all_null_columns=True)
    
    result = loader.load(df)
    
    # Check that it was copied
    assert result is not df
    # Check column stripping
    assert "col1" in result.columns
    # Check null column dropping (col2 is NOT fully null in this test setup, wait...)
    # Actually, [None] is fully null.
    assert "col2" not in result.columns

def test_data_loader_from_csv():
    """Verify loading from a CSV file."""
    loader = DataLoader()
    mock_df = pd.DataFrame({"a": [1]})
    
    with patch("pathlib.Path.exists", return_value=True):
        with patch("pandas.read_csv", return_value=mock_df) as mock_read:
            result = loader.load("test.csv", read_keyword_arguments={"sep": ";"})
            
            mock_read.assert_called_once()
            args, kwargs = mock_read.call_args
            assert kwargs["sep"] == ";"
            pd.testing.assert_frame_equal(result, mock_df)

def test_data_loader_unsupported_format():
    """Verify error on unsupported file extension."""
    loader = DataLoader()
    with patch("pathlib.Path.exists", return_value=True):
        with pytest.raises(ValueError, match="Unsupported file type"):
            loader.load("test.txt")

def test_strip_column_names():
    """Verify column names are stripped of whitespace."""
    df = pd.DataFrame({"  a  ": [1], "b\t": [2]})
    loader = DataLoader()
    result = loader.strip_column_names(df)
    assert list(result.columns) == ["a", "b"]

def test_drop_fully_null_columns():
    """Verify fully null columns are dropped."""
    df = pd.DataFrame({
        "full": [1, 2],
        "partial": [3, None],
        "empty": [None, None]
    })
    loader = DataLoader()
    result = loader.drop_fully_null_columns(df)
    assert "full" in result.columns
    assert "partial" in result.columns
    assert "empty" not in result.columns
