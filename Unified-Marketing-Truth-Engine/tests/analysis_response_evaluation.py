import json
import logging
import os
from typing import List, Dict, Any
try:
    import dspy
except ImportError:
    raise ImportError("DSPy is not installed. Please install it with `pip install dspy-ai` or `uv pip install dspy-ai`.")
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, "analysis_evaluation.log")
logging.basicConfig(
    level=logging.INFO,   # Define log message format: timestamp | level | logger name | message
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",  # Define log message format: timestamp | level | logger name | message
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8") ,   # Write logs to a file with UTF-8 encoding
        logging.StreamHandler()  # Also print logs to the console 
    ]
)
logger = logging.getLogger(__name__) # Create a logger instance named after the current module (for organized logging)

# Define a DSPy Signature class named "EvaluateAnalysis"
 
class EvaluateAnalysis(dspy.Signature):
 '''  Describes the input/output schema for evaluation the anlysis insigts by LLM
 '''


#input
 analysis_context = dspy.InputField(desc="The analysis insights to evaluate (usually structured JSON).")
 analysis_strucure= dspy.InputField(desc="The structure of anlysis insights include executive_summary, budget_and_efficiency, results_and_value, cross_channel_patterns_and_risks, channel_notes, and missing_info ")  

#output (Clarity, Follow output structure, Hallucination) 

 clarity_reasoning = dspy.OutputField(
        desc=(
            "Explain whether the analysis insights are clear, specific, or vague. "
            
        )
    )
 clarity_score = dspy.OutputField(
        desc=(
            "Integer score (1-3): "
            "1=very vague/unclear, 2=somewhat clear but incomplete, 3=very clear and specific."
        )
    )
