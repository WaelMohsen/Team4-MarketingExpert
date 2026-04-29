import pytest
import pandas as pd
import numpy as np
from src.shared.models.metrics import MetricsCalculator

@pytest.fixture
def calculator():
    return MetricsCalculator()

def test_SafeDiv_ShouldHandleZeroAndNa_WhenDividing(calculator):
    """Verify safe division logic."""
    # Arrange
    df = pd.DataFrame({
        "n": [10, 0, 5],
        "d": [2, 5, 0]
    })
    
    # Act
    result = calculator._safe_div(df, "n", "d")
    
    # Assert
    assert result[0] == 5.0
    assert result[1] == 0.0
    assert np.isnan(result[2]) # 5/0 should be NaN

def test_ComputeMetrics_ShouldCalculateStandardMetrics_WhenValidDataProvided(calculator):
    """Verify that all standard metrics are computed."""
    # Arrange
    df = pd.DataFrame({
        "impressions": [1000],
        "clicks": [100],
        "spend": [50.0],
        "conversions": [10],
        "conversion_value": [500.0]
    })
    
    # Act
    result = calculator.compute_metrics(df)
    
    # Assert
    assert result["ctr"][0] == 0.1
    assert result["cpc"][0] == 0.5
    assert result["cpm"][0] == 50.0
    assert result["cvr"][0] == 0.1
    assert result["roas"][0] == 10.0
    assert result["aov"][0] == 50.0

def test_ComputeMetrics_ShouldSkipMissingMetrics_WhenColumnsAreMissing(calculator):
    """Verify that missing columns handled gracefully (returns None/skips)."""
    # Arrange
    df = pd.DataFrame({"impressions": [1000]})
    
    # Act
    result = calculator.compute_metrics(df)
    
    # Assert
    # CTR should not be there because 'clicks' is missing
    assert "ctr" not in result.columns
