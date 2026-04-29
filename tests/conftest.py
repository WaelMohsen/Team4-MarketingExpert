import pytest
from src.core.execution_context import ExecutionContext

@pytest.fixture
def empty_context():
    return ExecutionContext()

@pytest.fixture
def mock_campaign_data():
    return {
        "campaign_id": "123",
        "name": "Test Campaign",
        "raw_data": {"clicks": 100, "spend": 10}
    }
