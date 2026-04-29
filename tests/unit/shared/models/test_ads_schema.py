import pytest
import pandas as pd
from src.shared.models.ads_schema import UnifiedAdsSchema
from src.core.exceptions import SchemaValidationError

def test_CanonicalizeColumns_ShouldRenameBasedOnAliases_WhenCalled():
    """Verify that columns are renamed correctly based on aliases."""
    # Arrange
    schema = UnifiedAdsSchema()
    df = pd.DataFrame({
        "Day": ["2024-01-01"],
        "Cost": [10.5],
        "Impr.": [100],
        "Unknown": ["val"]
    })
    
    # Act
    canonical_df = schema.canonicalize_columns(df)
    
    # Assert
    assert "date" in canonical_df.columns
    assert "spend" in canonical_df.columns
    assert "impressions" in canonical_df.columns
    assert "Unknown" in canonical_df.columns # Stays as is (but stripped)

def test_ValidateRequired_ShouldPass_WhenAllColumnsExist():
    """Verify validation passes when all required columns exist."""
    # Arrange
    schema = UnifiedAdsSchema()
    df = pd.DataFrame({
        "date": ["2024-01-01"],
        "platform": ["FB"],
        "campaign_type": ["Awareness"],
        "impressions": [100],
        "clicks": [10],
        "spend": [5.0]
    })
    
    # Act & Assert
    # Should not raise
    schema.validate_required(df)

def test_ValidateRequired_ShouldRaiseSchemaValidationError_WhenColumnsAreMissing():
    """Verify validation fails when required columns are missing."""
    # Arrange
    schema = UnifiedAdsSchema()
    df = pd.DataFrame({"date": ["2024-01-01"]})
    
    # Act & Assert
    with pytest.raises(SchemaValidationError, match="Missing required unified columns"):
        schema.validate_required(df)

def test_ValidateRequired_ShouldRaiseSchemaValidationError_WhenNumericValidationFails():
    """Verify validation fails when numeric columns have non-numeric values."""
    # Arrange
    schema = UnifiedAdsSchema()
    df = pd.DataFrame({
        "date": ["2024-01-01"],
        "platform": ["FB"],
        "campaign_type": ["Awareness"],
        "impressions": ["not a number"], # Invalid
        "clicks": [10],
        "spend": [5.0]
    })
    
    # Act & Assert
    with pytest.raises(SchemaValidationError, match="Numeric validation failed"):
        schema.validate_required(df)
