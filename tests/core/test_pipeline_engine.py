import pytest
from src.core.pipeline_engine import PipelineEngine
from src.core.base_module import BaseModule
from src.core.execution_context import ExecutionContext

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

def test_pipeline_engine_sequential_execution(empty_context):
    """Verify that modules are executed in the order they were added."""
    engine = PipelineEngine()
    m1 = MockModule("M1")
    m2 = MockModule("M2")
    
    engine.add_module(m1)
    engine.add_module(m2)
    
    final_context = engine.run(empty_context)
    
    assert m1.run_called is True
    assert m1.save_called is True
    assert m2.run_called is True
    assert m2.save_called is True
    assert final_context.get_metadata("M1") == "executed"
    assert final_context.get_metadata("M2") == "executed"
    assert len(final_context.errors) == 0

def test_pipeline_engine_stops_on_error(empty_context):
    """Verify that pipeline execution stops when a module fails."""
    engine = PipelineEngine()
    m1 = MockModule("M1", should_fail=True)
    m2 = MockModule("M2")
    
    engine.add_module(m1)
    engine.add_module(m2)
    
    final_context = engine.run(empty_context)
    
    assert m1.run_called is True
    assert m2.run_called is False
    assert len(final_context.errors) == 1
    assert "M1: Forced failure in M1" in final_context.errors[0]
