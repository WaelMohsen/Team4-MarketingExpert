import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from src.modules.ingestion.loader import DataLoader

def test_Load_ShouldReturnCleanDataFrame_WhenDataFrameIsProvided():
    """Verify loading from an existing DataFrame."""
    # Arrange
    df = pd.DataFrame({" col1 ": [1], "col2": [None]})
    loader = DataLoader(strip_column_whitespace=True, drop_all_null_columns=True)
    
    # Act
    result = loader.load(df)
    
    # Assert
    # Check that it was copied
    assert result is not df
    # Check column stripping
    assert "col1" in result.columns
    # Check null column dropping
    assert "col2" not in result.columns

def test_Load_ShouldReturnDataFrame_WhenCsvFileIsProvided():
    """Verify loading from a CSV file."""
    # Arrange
    loader = DataLoader()
    mock_df = pd.DataFrame({"a": [1]})
    
    # Act & Assert
    with patch("pathlib.Path.exists", return_value=True):
        with patch("pandas.read_csv", return_value=mock_df) as mock_read:
            result = loader.load("test.csv", read_keyword_arguments={"sep": ";"})
            
            mock_read.assert_called_once()
            args, kwargs = mock_read.call_args
            assert kwargs["sep"] == ";"
            pd.testing.assert_frame_equal(result, mock_df)

def test_Load_ShouldRaiseValueError_WhenUnsupportedFormatProvided():
    """Verify error on unsupported file extension."""
    # Arrange
    loader = DataLoader()
    
    # Act & Assert
    with patch("pathlib.Path.exists", return_value=True):
        with pytest.raises(ValueError, match="Unsupported file type"):
            loader.load("test.txt")

def test_StripColumnNames_ShouldCleanWhitespace_WhenCalled():
    """Verify column names are stripped of whitespace."""
    # Arrange
    df = pd.DataFrame({"  a  ": [1], "b\t": [2]})
    loader = DataLoader()
    
    # Act
    result = loader.strip_column_names(df)
    
    # Assert
    assert list(result.columns) == ["a", "b"]

def test_DropFullyNullColumns_ShouldRemoveEmptyColumns_WhenCalled():
    """Verify fully null columns are dropped."""
    # Arrange
    df = pd.DataFrame({
        "full": [1, 2],
        "partial": [3, None],
        "empty": [None, None]
    })
    loader = DataLoader()
    
    # Act
    result = loader.drop_fully_null_columns(df)
    
    # Assert
    assert "full" in result.columns
    assert "partial" in result.columns
    assert "empty" not in result.columns
