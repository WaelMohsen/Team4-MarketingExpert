from abc import ABC, abstractmethod
from src.core.execution_context import ExecutionContext

class BaseModule(ABC):
    """
    Abstract base class for all pipeline modules.
    Each module is responsible for a specific logic and its own persistence.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def run(self, context: ExecutionContext) -> ExecutionContext:
        """
        Execute the module's logic and return the updated context.
        """
        pass

    def save(self, context: ExecutionContext):
        """
        Optional method to persist module-specific results.
        """
        pass
