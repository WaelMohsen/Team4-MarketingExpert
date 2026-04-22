import pytest
from src.shared.models.llm_responses import validate_recommendation_output, validate_analysis_output

def get_valid_recommendation_item():
    return {
        "title": "Boost Ad Spend",
        "whats_happening": "CTR is dropping",
        "what_you_should_do": ["Increase budget", "Change creative"],
        "why_this_matters": "To get more clicks",
        "priority": "High",
        "expected_impact": "Higher CTR",
        "owner_suggestion": "Marketing Team"
    }

def get_valid_recommendation_output():
    return {
        "recommendations": [get_valid_recommendation_item() for _ in range(5)]
    }

def test_valid_recommendation_output():
    assert validate_recommendation_output(get_valid_recommendation_output()) is True

def test_invalid_less_than_5_recommendations():
    data = get_valid_recommendation_output()
    data["recommendations"].pop() # Now 4 items
    assert validate_recommendation_output(data) is False

def test_invalid_missing_fields_in_recommendation():
    data = get_valid_recommendation_output()
    del data["recommendations"][0]["title"]
    assert validate_recommendation_output(data) is False

def test_invalid_wrong_priority():
    data = get_valid_recommendation_output()
    data["recommendations"][0]["priority"] = "Urgent" # Valid are High, Medium, Low
    assert validate_recommendation_output(data) is False

def test_invalid_empty_what_you_should_do():
    data = get_valid_recommendation_output()
    data["recommendations"][0]["what_you_should_do"] = []
    assert validate_recommendation_output(data) is False

def get_valid_analysis_output():
    return {
        "analysis": {
            "executive_summary": "This is a sufficiently long summary for testing.",
            "budget_and_efficiency": [],
            "results_and_value": [],
            "cross_channel_patterns_and_risks": [],
            "channel_notes": [
                {
                    "platform": "Google Ads",
                    "what_we_see": ["High CPC"],
                    "what_it_likely_means": ["Increased competition"],
                    "risks_or_watchouts": []
                }
            ],
            "missing_info": []
        }
    }

def test_valid_analysis_output():
    assert validate_analysis_output(get_valid_analysis_output()) is True

def test_invalid_analysis_short_summary():
    data = get_valid_analysis_output()
    data["analysis"]["executive_summary"] = "Too short"
    assert validate_analysis_output(data) is False

def test_invalid_analysis_empty_channel_notes():
    data = get_valid_analysis_output()
    data["analysis"]["channel_notes"] = []
    assert validate_analysis_output(data) is False

def test_invalid_analysis_channel_note_missing_what_we_see():
    data = get_valid_analysis_output()
    data["analysis"]["channel_notes"][0]["what_we_see"] = []
    assert validate_analysis_output(data) is False

def test_invalid_analysis_missing_field():
    data = get_valid_analysis_output()
    del data["analysis"]["executive_summary"]
    assert validate_analysis_output(data) is False
