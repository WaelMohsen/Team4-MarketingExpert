class MarketingExpertError(Exception):
    """Base exception for the Marketing Expert system."""
    pass

class SchemaValidationError(MarketingExpertError):
    """Raised when data does not conform to the expected schema."""
    pass

class ModuleExecutionError(MarketingExpertError):
    """Raised when a pipeline module fails during execution."""
    pass

class ConfigurationError(MarketingExpertError):
    """Raised when there is an issue with the system configuration or environment variables."""
    pass

class TransformationError(MarketingExpertError):
    """Raised when a data transformation step fails."""
    pass
