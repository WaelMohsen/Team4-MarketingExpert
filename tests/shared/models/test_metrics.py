import pytest
import pandas as pd
import numpy as np
from src.shared.models.metrics import MetricsCalculator

@pytest.fixture
def calculator():
    return MetricsCalculator()

def test_metrics_calculator_safe_div(calculator):
    """Verify safe division logic."""
    df = pd.DataFrame({
        "n": [10, 0, 5],
        "d": [2, 5, 0]
    })
    result = calculator._safe_div(df, "n", "d")
    assert result[0] == 5.0
    assert result[1] == 0.0
    assert np.isnan(result[2]) # 5/0 should be NaN

def test_metrics_calculator_compute_all(calculator):
    """Verify that all standard metrics are computed."""
    df = pd.DataFrame({
        "impressions": [1000],
        "clicks": [100],
        "spend": [50.0],
        "conversions": [10],
        "conversion_value": [500.0]
    })
    
    result = calculator.compute_all(df)
    
    assert result["ctr"][0] == 0.1
    assert result["cpc"][0] == 0.5
    assert result["cpm"][0] == 50.0
    assert result["cvr"][0] == 0.1
    assert result["roas"][0] == 10.0
    assert result["aov"][0] == 50.0

def test_metrics_calculator_missing_columns(calculator):
    """Verify that missing columns handled gracefully (returns None/skips)."""
    df = pd.DataFrame({"impressions": [1000]})
    result = calculator.compute_all(df)
    # CTR should not be there because 'clicks' is missing
    assert "ctr" not in result.columns
