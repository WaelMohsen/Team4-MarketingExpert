import pytest
from src.core.base_module import BaseModule
from src.core.execution_context import ExecutionContext

def test_Instantiation_ShouldRaiseTypeError_WhenBaseModuleIsAbstract():
    """Ensure BaseModule is abstract."""
    # Act & Assert
    with pytest.raises(TypeError):
        BaseModule("test")

class ConcreteModule(BaseModule):
    def run(self, context: ExecutionContext) -> ExecutionContext:
        context.set_metadata("test_key", "test_value")
        return context

def test_Run_ShouldUpdateContext_WhenConcreteModuleIsExecuted(empty_context):
    """Ensure a concrete implementation of BaseModule works."""
    # Arrange
    module = ConcreteModule("TestModule")
    
    # Act
    updated_context = module.run(empty_context)
    
    # Assert
    assert module.name == "TestModule"
    assert updated_context.get_metadata("test_key") == "test_value"

def test_Save_ShouldDoNothing_WhenDefaultSaveIsCalled(empty_context):
    """Ensure the default save method is a no-op and doesn't crash."""
    # Arrange
    module = ConcreteModule("TestModule")
    
    # Act & Assert
    # This should not raise any exception
    module.save(empty_context)
