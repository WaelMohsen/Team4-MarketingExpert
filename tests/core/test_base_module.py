import pytest
from src.core.base_module import BaseModule
from src.core.execution_context import ExecutionContext

def test_base_module_cannot_be_instantiated():
    """Ensure BaseModule is abstract."""
    with pytest.raises(TypeError):
        BaseModule("test")

class ConcreteModule(BaseModule):
    def run(self, context: ExecutionContext) -> ExecutionContext:
        context.set_metadata("test_key", "test_value")
        return context

def test_concrete_module_execution(empty_context):
    """Ensure a concrete implementation of BaseModule works."""
    module = ConcreteModule("TestModule")
    assert module.name == "TestModule"
    
    updated_context = module.run(empty_context)
    assert updated_context.get_metadata("test_key") == "test_value"

def test_concrete_module_save_no_op(empty_context):
    """Ensure the default save method is a no-op and doesn't crash."""
    module = ConcreteModule("TestModule")
    # This should not raise any exception
    module.save(empty_context)
