import logging
from typing import List
from langchain_core.runnables import Runnable
from src.core.base_module import BaseModule
from src.core.execution_context import ExecutionContext

logger = logging.getLogger(__name__)

class PipelineEngine:
    """
    Orchestrator that executes a sequence of modules linearly using LangChain LCEL.
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
        Execute all registered modules in sequence using LangChain LCEL.
        """
        logger.info("Starting pipeline execution via LangChain LCEL...")
        
        if not self.modules:
            logger.info("No modules registered. Returning original context.")
            return context

        # Construct LCEL chain dynamically
        chain = self.modules[0]
        for module in self.modules[1:]:
            chain = chain | module

        try:
            context = chain.invoke(context)
        except Exception as e:
            logger.error(f"Error in LCEL pipeline execution: {str(e)}")
            if not context.errors:
                context.errors.append(f"PipelineLCEL: {str(e)}")
            
        logger.info("Pipeline execution finished.")
        return context
