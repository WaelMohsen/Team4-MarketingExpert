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
    Evaluate a marketing recommendation based on clarity, accuracy, and non-redundancy.
    """
    
    recommendation = dspy.InputField(desc="The recommendation response/card to evaluate, typically in JSON format.")
    
    clarity_reasoning = dspy.OutputField(desc="Reasoning about the clarity and actionability of the recommendation.")
    clarity_score = dspy.OutputField(desc="A score between 1 and 5 indicating how clear, understandable, and actionable the recommendation is.")
    
    accuracy_reasoning = dspy.OutputField(desc="Reasoning about whether the recommendation is logically valid, given the context.")
    accuracy_score = dspy.OutputField(desc="A score between 1 and 5 indicating logical accuracy and validity.")
    
    redundancy_reasoning = dspy.OutputField(desc="Reasoning about whether this recommendation is unique and avoids repeating generic tropes.")
    non_redundancy_score = dspy.OutputField(desc="A score between 1 and 5 indicating how unique and non-redundant the recommendation is.")


class RecommendationEvaluator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.evaluate = dspy.ChainOfThought(EvaluateRecommendation)

    def forward(self, recommendation: str) -> Dict[str, Any]:
        """
        Evaluate a given recommendation card/text.
        """
        # Call the DSPy Module
        result = self.evaluate(recommendation=recommendation)
        
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


def evaluate_recommendations(recommendations_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Helper function to iterate through a list of recommendations and evaluate each one.
    """
    evaluator = RecommendationEvaluator()
    results = []
    
    for idx, rec in enumerate(recommendations_data):
        logger.info(f"Evaluating Recommendation {idx + 1}...")
        
        # Convert dictionary to string for DSPy to evaluate
        rec_str = json.dumps(rec, indent=2)
        
        eval_result = evaluator(recommendation=rec_str)
        
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

    # Example Test Payload replicating RecommendationCard
    sample_recommendations = [
        {
            "title": "Reallocate Budget from TikTok to Meta",
            "whats_happening": "TikTok CAC is 200% higher than Meta.",
            "what_you_should_do": ["Pause TikTok campaigns", "Shift 20% budget to Meta Lookalikes"],
            "why_this_matters": "Improves overall acquisition cost and profitability.",
            "priority": "High",
            "expected_impact": "Lower blended CAC",
            "owner_suggestion": "Media buyer"
        },
        {
            "title": "Optimize Meta Campaigns",
            "whats_happening": "Meta is doing well.",
            "what_you_should_do": ["Continue monitoring Meta"],
            "why_this_matters": "Because Meta helps.",
            "priority": "Low",
            "expected_impact": "Stay the same",
            "owner_suggestion": "Media buyer"
        }
    ]
    
    logger.info("Executing sample evaluation on 2 recommendations...\n")
    eval_output = evaluate_recommendations(sample_recommendations)
    
    print("\n" + "="*50)
    print("              EVALUATION SUMMARY")
    print("="*50)
    print(json.dumps(eval_output, indent=2))
