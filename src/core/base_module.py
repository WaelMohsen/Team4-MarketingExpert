from abc import ABC, abstractmethod
from typing import Any
from langchain_core.runnables import Runnable
from src.core.execution_context import ExecutionContext

class BaseModule(Runnable[ExecutionContext, ExecutionContext], ABC):
    """
    Abstract base class for all pipeline modules.
    Each module is responsible for a specific logic and its own persistence.
    """

    def __init__(self, name: str):
        super().__init__()
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

    def invoke(self, input: ExecutionContext, config: Any = None) -> ExecutionContext:
        """
        Invokes the module as a LangChain Runnable node in the LCEL sequence.
        """
        try:
            context = self.run(input)
            self.save(context)
            return context
        except Exception as e:
            input.errors.append(f"{self.name}: {str(e)}")
            raise e
