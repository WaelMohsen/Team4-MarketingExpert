import pytest
import pandas as pd
from src.shared.models.metrics import MetricsCalculator
from src.shared.utils.prompt_registry import PromptRegistry
from src.shared.utils.prompt_builder import PromptBuilder
from src.shared.utils.prompt_loader import PromptLoader

def test_metrics_calculator_goal_specific_keys():
    """Verify that get_goal_metrics returns the correct keys for a specific goal."""
    calc = MetricsCalculator()
    
    # Mock data with enough columns to satisfy all goal metrics
    data = {
        "spend": [100],
        "clicks": [10],
        "impressions": [1000],
        "conversions": [1],
        "revenue": [500],
        "conversion_value": [500],
        "reach": [500],
        "landing_page_views": [8],
        "sessions": [10],
        "purchases": [1],
        "total_revenue": [1000],
        "total_marketing_spend": [200],
        "lifetime_value": [300],
        "cac": [50],
        "monthly_gross_profit_per_customer": [10],
        "refunds": [0],
        "orders": [1]
    }
    df = pd.DataFrame(data)
    
    # Test Traffic
    traffic_metrics = calc.get_goal_metrics(df.iloc[0], "Traffic")
    assert "clicks" in traffic_metrics
    assert "ctr" in traffic_metrics
    assert "bounce_proxy_rate" in traffic_metrics
    assert "roas" not in traffic_metrics # Should be excluded for Traffic
    
    # Test Increase Sales
    sales_metrics = calc.get_goal_metrics(df.iloc[0], "Increase Sales")
    assert "roas" in sales_metrics
    assert "purchases" in sales_metrics
    assert "bounce_proxy_rate" not in sales_metrics # Should be excluded for Sales

def test_prompt_registry_mapping():
    """Verify that goal strings map to the correct prompt file paths."""
    assert PromptRegistry.get_objective_prompt("Traffic") == "objectives/traffic.txt"
    assert PromptRegistry.get_objective_prompt("Increase Sales") == "objectives/sales_boost.txt"
    assert PromptRegistry.get_objective_prompt("Unknown Goal") == ""

def test_prompt_builder_goal_injection():
    """Verify that the PromptBuilder correctly injects goal instructions."""
    loader = PromptLoader.from_module_dir()
    builder = PromptBuilder(loader=loader)
    
    campaign_data = {"test": "data"}
    business_domain = {"industry": "Test"}
    campaign_target = {"primary_goal": "Traffic"}
    goal_instructions = "FOCUS ON CLICKS"
    
    messages = builder.build_analysis_prompt(
        campaign_data=campaign_data,
        business_domain=business_domain,
        campaign_target=campaign_target,
        goal_instructions=goal_instructions,
        strict=False # Disable strict for test to avoid needing all placeholders
    )
    
    system_message = messages[0]["content"]
    assert "FOCUS ON CLICKS" in system_message
    assert "{{GOAL_INSTRUCTIONS}}" not in system_message
