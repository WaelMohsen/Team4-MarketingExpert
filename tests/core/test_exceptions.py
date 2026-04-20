import pytest
from src.core.exceptions import (
    MarketingExpertError,
    SchemaValidationError,
    ModuleExecutionError,
    ConfigurationError,
    TransformationError
)

def test_exceptions_inheritance():
    """Verify that all custom exceptions inherit from MarketingExpertError."""
    assert issubclass(SchemaValidationError, MarketingExpertError)
    assert issubclass(ModuleExecutionError, MarketingExpertError)
    assert issubclass(ConfigurationError, MarketingExpertError)
    assert issubclass(TransformationError, MarketingExpertError)

def test_exception_messages():
    """Verify that exceptions can be raised with custom messages."""
    with pytest.raises(SchemaValidationError) as excinfo:
        raise SchemaValidationError("Invalid schema")
    assert str(excinfo.value) == "Invalid schema"

    with pytest.raises(ModuleExecutionError) as excinfo:
        raise ModuleExecutionError("Module failed")
    assert str(excinfo.value) == "Module failed"
