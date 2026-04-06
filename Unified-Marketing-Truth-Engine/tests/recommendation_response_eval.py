import json
import logging
import os
from typing import List, Dict, Any

try:
    import dspy
except ImportError:
    raise ImportError("DSPy is not installed. Please install it with `pip install dspy-ai` or `uv pip install dspy-ai`.")

# Set up logging for the evaluator
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class EvaluateRecommendation(dspy.Signature):
    """
    Evaluate a marketing recommendation based on clarity, accuracy, and non-redundancy, For non-marketeer end users.
    """
    
    campaign_target = dspy.InputField(desc="The high-level goal and KPIs for the campaign.")
    business_domain = dspy.InputField(desc="The industry, offering, target audience, and funnel stage.")
    analysis_context = dspy.InputField(desc="The detailed analysis insights derived from the data.")
    recommendation = dspy.InputField(desc="The recommendation response/card to evaluate, typically in JSON format.")
    
    clarity_reasoning = dspy.OutputField(desc="Reasoning about the clarity and actionability of the recommendation.")
    clarity_score = dspy.OutputField(desc="A score between 1 and 5 indicating how clear, understandable, and actionable the recommendation is.")
    
    accuracy_reasoning = dspy.OutputField(desc="Reasoning about whether the recommendation is logically valid and grounded in the provided analysis context.")
    accuracy_score = dspy.OutputField(desc="A score between 1 and 5 indicating logical accuracy and validity based on the context.")
    
    redundancy_reasoning = dspy.OutputField(desc="Reasoning about whether this recommendation is unique and avoids repeating generic tropes.")
    non_redundancy_score = dspy.OutputField(desc="A score between 1 and 5 indicating how unique and non-redundant the recommendation is.")


class RecommendationEvaluator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.evaluate = dspy.ChainOfThought(EvaluateRecommendation)

    def forward(self, campaign_target: str, business_domain: str, analysis_context: str, recommendation: str) -> Dict[str, Any]:
        """
        Evaluate a given recommendation card/text using the context of the campaign, business domain, and stage 1 analysis.
        """
        # Call the DSPy Module with all context inputs
        result = self.evaluate(
            campaign_target=campaign_target,
            business_domain=business_domain,
            analysis_context=analysis_context,
            recommendation=recommendation
        )
        
        # Safely parse numeric scores
        try:
            clarity_score = float(result.clarity_score)
        except ValueError:
            clarity_score = 0.0
            
        try:
            accuracy_score = float(result.accuracy_score)
        except ValueError:
            accuracy_score = 0.0
            
        try:
            non_redundancy_score = float(result.non_redundancy_score)
        except ValueError:
            non_redundancy_score = 0.0
            
        overall_score = (clarity_score + accuracy_score + non_redundancy_score) / 3.0
            
        return {
            "clarity_score": clarity_score,
            "clarity_reasoning": result.clarity_reasoning,
            "accuracy_score": accuracy_score,
            "accuracy_reasoning": result.accuracy_reasoning,
            "non_redundancy_score": non_redundancy_score,
            "redundancy_reasoning": result.redundancy_reasoning,
            "overall_score": overall_score
        }


def evaluate_recommendations(
    recommendations_data: List[Dict[str, Any]], 
    campaign_target: Dict[str, Any], 
    business_domain: Dict[str, Any], 
    analysis_context: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Helper function to iterate through a list of recommendations and evaluate each one in context.
    """
    evaluator = RecommendationEvaluator()
    results = []
    
    # Convert structures to string once for all evaluations
    campaign_target_str = json.dumps(campaign_target, indent=2)
    business_domain_str = json.dumps(business_domain, indent=2)
    analysis_context_str = json.dumps(analysis_context, indent=2)
    
    for idx, rec in enumerate(recommendations_data):
        logger.info(f"Evaluating Recommendation {idx + 1}...")
        
        # Convert dictionary to string for DSPy to evaluate
        rec_str = json.dumps(rec, indent=2)
        
        eval_result = evaluator(
            campaign_target=campaign_target_str,
            business_domain=business_domain_str,
            analysis_context=analysis_context_str,
            recommendation=rec_str
        )
        
        # Merge original with evaluation results
        eval_result["recommendation_index"] = idx
        results.append(eval_result)
        
        logger.info(f"Scores for Rec {idx + 1} - Clarity: {eval_result['clarity_score']}, "
                    f"Accuracy: {eval_result['accuracy_score']}, "
                    f"Non-Redundancy: {eval_result['non_redundancy_score']}, "
                    f"Overall: {eval_result['overall_score']:.2f}\n")
                    
    return results

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    # Configure the DSPy LM Client Backend
    try:
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        logger.info(f"Configuring DSPy LM with model: openai/{model}")
        lm = dspy.LM(f"openai/{model}")
        dspy.settings.configure(lm=lm)
    except Exception as e:
        logger.error(f"Failed to configure DSPy LM: {e}")

    # Example Context Payloads: Real E-commerce Holiday Sale Scenario
    sample_campaign_target = {
        "primary_goal": "Maximize ROAS during the Winter Holiday Sale",
        "kpis": ["ROAS", "CPA", "Conversion Volume"]
    }

    sample_business_domain = {
        "industry": "E-Commerce",
        "offering": "Winter clothing and outerwear",
        "audience": "High-intent seasonal shoppers",
        "funnel_stage": "conversion"
    }
    
    sample_analysis_context = {
        "analysis": {
            "executive_summary": "Google Ads is driving a high ROAS of 4.5x but has a limited impression share due to budget caps. Meanwhile, Meta is consuming 70% of the budget but its ROAS has dropped to 1.8x over the last two weeks, strongly indicating ad fatigue on the current creative sets.",
            "budget_and_efficiency": [
                {
                    "insight": "Google Ads budget is capping out daily.",
                    "evidence": "Search impression share lost due to budget is at 45%.",
                    "business_impact": "Leaving highly profitable conversions on the table."
                }
            ],
            "results_and_value": [],
            "cross_channel_patterns_and_risks": [
                {
                    "pattern_or_risk": "Meta creative fatigue is dragging down blended return.",
                    "evidence": "Frequency on Meta is over 8, and CTR dropped from 1.5% to 0.6%.",
                    "why_it_matters": "The largest budget pool is becoming increasingly inefficient."
                }
            ],
            "channel_notes": [],
            "missing_info": []
        }
    }

    # Example Test Payload replicating RecommendationCard
    sample_recommendations = [
        {
            "title": "Shift Meta Budget to fully fund Google Ads",
            "whats_happening": "Google Ads has a 4.5x ROAS but is budget-capped, while Meta's ROAS has dropped to 1.8x.",
            "what_you_should_do": ["Reduce Meta daily budgets by 30%", "Reallocate that 30% to the top performing Google Search campaigns"],
            "why_this_matters": "This allows you to capture all existing high-intent demand on Google, immediately lifting overall return.",
            "priority": "High",
            "expected_impact": "Improved blended ROAS and higher conversion volume.",
            "owner_suggestion": "Media buyer"
        },
        {
            "title": "Optimize Meta Targeting Mechanism",
            "whats_happening": "Performance on Meta is dropping.",
            "what_you_should_do": ["Go into Ads Manager", "Change the algorithm to look for better users"],
            "why_this_matters": "It will fix the performance issue.",
            "priority": "Medium",
            "expected_impact": "Things should get better.",
            "owner_suggestion": "Media buyer"
        },
        {
            "title": "Refresh Meta Creatives to Combat Ad Fatigue",
            "whats_happening": "Meta frequency is high (>8) and CTR has dropped by over half, indicating audience fatigue.",
            "what_you_should_do": ["Launch 3-5 new video assets highlighting holiday discounts", "Rotate out existing underperforming creatives"],
            "why_this_matters": "Fresh creatives reset the algorithm and re-engage the audience, recovering Meta's efficiency.",
            "priority": "High",
            "expected_impact": "Increased CTR and stabilized CPA on Meta.",
            "owner_suggestion": "Creative team / Media buyer"
        }
    ]
    
    logger.info("Executing sample evaluation on 3 recommendations with real-world E-commerce context...\n")
    eval_output = evaluate_recommendations(
        sample_recommendations,
        campaign_target=sample_campaign_target,
        business_domain=sample_business_domain,
        analysis_context=sample_analysis_context
    )
    
    print("\n" + "="*50)
    print("              EVALUATION SUMMARY")
    print("="*50)
    print(json.dumps(eval_output, indent=2))
