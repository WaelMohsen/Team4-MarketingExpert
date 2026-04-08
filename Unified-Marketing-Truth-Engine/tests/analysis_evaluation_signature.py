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

# Define a DSPy Signature class 
 
class AnalysisEvaluationSignature(dspy.Signature):
 """
 Define the evaluation schema for LLM-generated campaign analysis insights.

 This signature standardizes how analysis insights are assessed across multiple criteria,
 including clarity, structural follow, relevance to campaign context, and hallucination detection.

 It takes structured campaign data and analysis insights as input, and produces both qualitative
 reasoning and quantitative scores. 
 """


#input
 campaign_data     = dspy.InputField(desc="The compaign information include platform, objective, and metrics" )
 analysis_context  = dspy.InputField(desc="The analysis insights to evaluate (usually structured JSON).")
 analysis_strucure = dspy.InputField(desc="The structure of anlysis insights include executive_summary, budget_and_efficiency, results_and_value, cross_channel_patterns_and_risks, channel_notes, and missing_info ")  
# New
 campaign_target    = dspy.InputField(desc="The compaign target" )

#output (Clarity (1-3), Follow output structure (1-3), Relevance (1–3), Hallucination (Yes/No)) 

# --- Clarity ---
 clarity_reasoning = dspy.OutputField(
        desc = "Explain whether the analysis insights are clear, specific, or vague."
     )
    
 clarity_score = dspy.OutputField(
        desc = "Integer score (1-3): 1=very vague, 2=partially clear, 3=very clear and complete."
    )

# --- Follow Output Structure ---
    
 structure_reasoning = dspy.OutputField(
        desc = "Explain whether the analysis follows the required structure and includes all expected sections."
    )
    
 structure_score = dspy.OutputField(
        desc = "Integer score (1-3): 1=missing most sections, 2=partially structured, 3=fully structured and well organized."
    )

# --- Relevance ---
 relevance_reasoning = dspy.OutputField(
        desc = "Explain whether the analysis is relevant to the campaign data, objectives, and KPIs."
    )
    
 relevance_score = dspy.OutputField(
        desc = "Integer score (1-3): 1=irrelevant, 2=partially relevant, 3=fully aligned with campaign context."
    )

# --- Hallucination ---
    
 hallucination_reasoning = dspy.OutputField(
        desc = "Explain whether the analysis contains unsupported claims or fabricated insights."
    )
    
 hallucination_flag = dspy.OutputField(
        desc = "Yes/No: Yes if hallucination exists, No if all insights are based on the provided data."
    )
  