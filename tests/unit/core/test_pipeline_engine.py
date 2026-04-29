import pytest
from unittest.mock import MagicMock
from src.core.pipeline_engine import PipelineEngine
from src.core.base_module import BaseModule
from src.core.execution_context import ExecutionContext

@pytest.fixture
def pipeline_engine():
    return PipelineEngine()

class MockModule(BaseModule):
    def __init__(self, name, should_fail=False):
        super().__init__(name)
        self.should_fail = should_fail
        self.run_called = False
        self.save_called = False

    def run(self, context: ExecutionContext) -> ExecutionContext:
        self.run_called = True
        if self.should_fail:
            raise ValueError(f"Forced failure in {self.name}")
        context.set_metadata(self.name, "executed")
        return context

    def save(self, context: ExecutionContext):
        self.save_called = True

def test_Run_ShouldExecuteAllModulesInOrder_WhenPipelineIsStarted(pipeline_engine):
    """Verify that the pipeline engine runs all modules in order."""
    # Arrange
    mock_module = MockModule("TestModule")
    pipeline_engine.add_module(mock_module)
    
    ctx = ExecutionContext()
    ctx.set_metadata("input_csv", "test.csv")
    
    # Act
    pipeline_engine.run(ctx)
    
    # Assert
    assert mock_module.run_called is True
    assert mock_module.save_called is True

def test_Run_ShouldStopExecution_WhenModuleFails(pipeline_engine):
    """Verify that the pipeline stops if a module raises an error."""
    # Arrange
    mock_module1 = MockModule("M1", should_fail=True)
    mock_module2 = MockModule("M2")
    
    pipeline_engine.add_module(mock_module1)
    pipeline_engine.add_module(mock_module2)
    
    ctx = ExecutionContext()
    
    # Act
    ctx = pipeline_engine.run(ctx)
    
    # Assert
    assert mock_module1.run_called is True
    assert mock_module2.run_called is False
    assert len(ctx.errors) == 1
    assert "M1: Forced failure in M1" in ctx.errors[0]
