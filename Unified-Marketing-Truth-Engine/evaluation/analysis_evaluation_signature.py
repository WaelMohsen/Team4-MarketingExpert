import json
import logging
import os
from typing import List, Dict, Any
import dspy
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
    campaign_data     = dspy.InputField(desc="The campaign information include platform, objective, and metrics" )
    analysis_context  = dspy.InputField(desc="The analysis insights to evaluate (usually structured JSON).")
    campaign_target   = dspy.InputField(desc="The campaign target" )

    #output (Clarity (1-3), Follow output structure (1-3), Relevance (1–3), Hallucination (Yes/No)) 

    # --- Clarity ---
    clarity_reasoning = dspy.OutputField(
        desc = "Explain whether the analysis insights are clear, specific, or vague."
        )

    clarity_score = dspy.OutputField(
        desc = "Integer score (1-3): 1=very vague, 2=partially clear, 3=very clear and complete."
    )

    # --- Follow Output Structure ---

    following_structure_reasoning = dspy.OutputField(
        desc = "Explain whether the analysis follows the required structure and includes include executive_summary, budget_and_efficiency, results_and_value, cross_channel_patterns_and_risks, channel_notes, and missing_info ")  


            
    following_structure_score = dspy.OutputField(
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
        desc = "-1/+1: -1 if hallucination exists, +1 if all insights are based on the provided data."
    )
