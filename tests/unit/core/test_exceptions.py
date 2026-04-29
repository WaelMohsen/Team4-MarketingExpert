import pytest
from src.core.exceptions import (
    MarketingExpertError,
    SchemaValidationError,
    ModuleExecutionError,
    ConfigurationError,
    TransformationError
)

def test_Inheritance_ShouldDeriveFromMarketingExpertError_WhenExceptionsAreCreated():
    """Verify that all custom exceptions inherit from MarketingExpertError."""
    # Assert
    assert issubclass(SchemaValidationError, MarketingExpertError)
    assert issubclass(ModuleExecutionError, MarketingExpertError)
    assert issubclass(ConfigurationError, MarketingExpertError)
    assert issubclass(TransformationError, MarketingExpertError)

def test_Message_ShouldReturnCustomMessage_WhenExceptionIsRaised():
    """Verify that exceptions can be raised with custom messages."""
    # Act & Assert
    with pytest.raises(SchemaValidationError) as excinfo:
        raise SchemaValidationError("Invalid schema")
    assert str(excinfo.value) == "Invalid schema"

    with pytest.raises(ModuleExecutionError) as excinfo:
        raise ModuleExecutionError("Module failed")
    assert str(excinfo.value) == "Module failed"
