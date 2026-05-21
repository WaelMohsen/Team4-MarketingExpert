import logging
from typing import List
from src.core.base_module import BaseModule
from src.core.execution_context import ExecutionContext

logger = logging.getLogger(__name__)

class PipelineEngine:
    """
    Orchestrator that executes a sequence of modules linearly.
    """

    def __init__(self):
        self.modules: List[BaseModule] = []

    def add_module(self, module: BaseModule):
        """
        Register a module to the pipeline.
        """
        self.modules.append(module)
        logger.info(f"Registered module: {module.name}")

    def run(self, context: ExecutionContext) -> ExecutionContext:
        """
        Execute all registered modules in sequence.
        """
        logger.info("Starting pipeline execution...")
        
        for module in self.modules:
            logger.info(f"Running module: {module.name}")
            try:
                context = module.run(context)
                module.save(context)
            except Exception as e:
                logger.error(f"Error in module {module.name}: {str(e)}")
                context.errors.append(f"{module.name}: {str(e)}")
                # Depending on requirements, we might want to stop or continue
                # For now, we stop on error to avoid inconsistent states
                break
                
        logger.info("Pipeline execution finished.")
        return context
