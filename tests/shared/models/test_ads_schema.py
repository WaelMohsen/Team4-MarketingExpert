import pytest
import pandas as pd
from src.shared.models.ads_schema import UnifiedAdsSchema
from src.core.exceptions import SchemaValidationError

def test_schema_canonicalize_columns():
    """Verify that columns are renamed correctly based on aliases."""
    schema = UnifiedAdsSchema()
    df = pd.DataFrame({
        "Day": ["2024-01-01"],
        "Cost": [10.5],
        "Impr.": [100],
        "Unknown": ["val"]
    })
    
    canonical_df = schema.canonicalize_columns(df)
    
    assert "date" in canonical_df.columns
    assert "spend" in canonical_df.columns
    assert "impressions" in canonical_df.columns
    assert "Unknown" in canonical_df.columns # Stays as is (but stripped)

def test_schema_validate_required_success():
    """Verify validation passes when all required columns exist."""
    schema = UnifiedAdsSchema()
    df = pd.DataFrame({
        "date": ["2024-01-01"],
        "platform": ["FB"],
        "campaign_type": ["Awareness"],
        "impressions": [100],
        "clicks": [10],
        "spend": [5.0]
    })
    # Should not raise
    schema.validate_required(df)

def test_schema_validate_required_missing():
    """Verify validation fails when required columns are missing."""
    schema = UnifiedAdsSchema()
    df = pd.DataFrame({"date": ["2024-01-01"]})
    with pytest.raises(SchemaValidationError, match="Missing required unified columns"):
        schema.validate_required(df)

def test_schema_validate_numeric_types_failure():
    """Verify validation fails when numeric columns have non-numeric values."""
    schema = UnifiedAdsSchema()
    df = pd.DataFrame({
        "date": ["2024-01-01"],
        "platform": ["FB"],
        "campaign_type": ["Awareness"],
        "impressions": ["not a number"], # Invalid
        "clicks": [10],
        "spend": [5.0]
    })
    with pytest.raises(SchemaValidationError, match="Numeric validation failed"):
        schema.validate_required(df)
