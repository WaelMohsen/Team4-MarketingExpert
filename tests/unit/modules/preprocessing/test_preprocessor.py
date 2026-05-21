import pytest
import pandas as pd
from src.modules.preprocessing.preprocessor import Preprocessor
from src.shared.models.ads_schema import UnifiedAdsSchema

@pytest.fixture
def preprocessor():
    return Preprocessor(schema=UnifiedAdsSchema())

def test_EnforceTypes_ShouldHandleDataCorrectly_WhenSchemaProvided(preprocessor):
    """Verify that types are enforced and handled according to schema."""
    # Arrange
    df = pd.DataFrame({
        "date": ["2024-01-01", "invalid-date"],
        "impressions": ["100", "invalid"],
        "spend": [10.5, None]
    })
    
    # Act
    result = preprocessor.enforce_types(df)
    
    # Assert
    # Check date parsing
    assert pd.api.types.is_datetime64_any_dtype(result["date"])
    assert pd.isna(result["date"][1])

    # Check numeric conversion
    assert pd.api.types.is_numeric_dtype(result["impressions"])
    assert result["impressions"][0] == 100
    assert result["impressions"][1] == 0 # Filled with zero by default for metrics

    # Check fillna with zero
    assert result["spend"][0] == 10.5
    assert result["spend"][1] == 0

def test_RemoveDuplicates_ShouldConsolidateRows_WhenKeysOverlap(preprocessor):
    """Verify that duplicates are removed based on keys."""
    # Arrange
    df = pd.DataFrame({
        "date": ["2024-01-01", "2024-01-01", "2024-01-02"],
        "platform": ["FB", "FB", "FB"],
        "spend": [10, 20, 30]
    })
    
    # Act
    result = preprocessor.remove_duplicates(df)
    
    # Assert
    # Only 2 rows should remain (last one for FB on 2024-01-01, and 2024-01-02)
    assert len(result) == 2
    assert result.loc[result["date"] == "2024-01-01", "spend"].values[0] == 20
