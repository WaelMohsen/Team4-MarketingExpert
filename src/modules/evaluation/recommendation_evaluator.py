import json
import logging
import os
from typing import List, Dict, Any, Optional

from src.shared.utils.prompt_loader import PromptLoader
from src.shared.utils.prompt_builder import PromptBuilder
from src.shared.utils.llm_client import LLMApiClient
from src.shared.models.llm_responses import RecommendationEvaluationResponse
from src.shared.utils.prompt_registry import PromptRegistry

# Setup logging
try:
    from src.shared.utils.logger import setup_logging
    logger = setup_logging(module_name ='recommendation_evaluator')
    from src.shared.utils.json_saver import save_results_to_json
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

class RecommendationEvaluator:
    """
    Evaluates recommendation cards using manual prompts and structured outputs.
    """
    def __init__(self):
        self.loader = PromptLoader.from_module_dir()
        self.builder = PromptBuilder(loader=self.loader)
        self.client = LLMApiClient(
            model=os.getenv("EVALUATION_MODEL", "gpt-4.1-nano-2025-04-14"),
            max_output_tokens=2000
        )

    def evaluate(self, business_context: Any, campaign_target: Any, campaign_data: Any, analysis_context: Any, recommendation: Any, save_dir: Optional[str] = None) -> Dict[str, Any]:
        """Runs the evaluation."""
        
        sys_text = self.loader.load_prompt_text(PromptRegistry.EVAL_RECOMMENDATION_SYSTEM.value)
        user_text = self.loader.load_prompt_text(PromptRegistry.EVAL_RECOMMENDATION_USER.value)
        
        combined_context = {
            "business_domain": business_context,
            "campaign_target": campaign_target
        }
        
        user_text = (
            user_text.replace("{{BUSINESS_CONTEXT}}", json.dumps(combined_context, indent=2))
            .replace("{{RAW_DATA}}", json.dumps(campaign_data, indent=2))
            .replace("{{ANALYSIS_CONTEXT}}", json.dumps(analysis_context, indent=2))
            .replace("{{RECOMMENDATION}}", json.dumps(recommendation, indent=2))
        )
        
        messages = [
            {"role": "system", "content": sys_text},
            {"role": "user", "content": user_text}
        ]
 
        logger.info("Executing Recommendation Evaluation...")
        result = self.client.generate_json(
            messages, 
            response_format=RecommendationEvaluationResponse,
            save_dir=save_dir,
            prompt_name="evaluation_recommendation_prompt"
        )
        
        eval_data = result.get("evaluation", {})
        
        return {
            "scores": {
                "Structure": eval_data.get("structure_score", 0),
                "Feasibility": eval_data.get("feasibility_score", 0),
                "Recommendation_Count": eval_data.get("Recommendation_Count_score", 0),
                "Analysis_Grounding": eval_data.get("Analysis_Grounding_score", 0),
                "Action_Step_Completeness": eval_data.get("Action_Step_Completeness_score", 0),
                "Priority_Alignment": eval_data.get("Priority_Alignment_score", 0),
                "Tone_&_Audience_Compliance": eval_data.get("Tone_&_Audience_Compliance_score", 0),
                "Expected_Impact_Quality": eval_data.get("Expected_Impact_Quality_score", 0),
                "Overall": (eval_data.get("structure_score", 0) + eval_data.get("feasibility_score", 0) + 
                           eval_data.get("Recommendation_Count_score", 0) + eval_data.get("Analysis_Grounding_score", 0)) +
                           (eval_data.get("Action_Step_Completeness_score", 0) + eval_data.get("Priority_Alignment_score", 0) + 
                            eval_data.get("Tone_&_Audience_Compliance_score", 0) + eval_data.get("Expected_Impact_Quality_score", 0)) / 8
            },
            "reasoning": {
                "Structure": eval_data.get("clarity_reasoning"),
                "Feasibility": eval_data.get("accuracy_reasoning"),
                "Recommendation_Count": eval_data.get("structure_reasoning"),
                "Analysis_Grounding": eval_data.get("feasibility_reasoning"),
                "Action_Step_Completeness": eval_data.get("Action_Step_Completeness_reasoning"),
                "Priority_Alignment": eval_data.get("Priority_Alignment_reasoning"),
                "Tone_&_Audience_Compliance": eval_data.get("Tone_&_Audience_Compliance_reasoning"),
                "Expected_Impact_Quality": eval_data.get("Expected_Impact_Quality_reasoning"),
            },
            "verdict": eval_data.get("verdict"),
            "key_issues": eval_data.get("key_issues"),
            "improvement_suggestions": eval_data.get("improvement_suggestions"),
        }

def run_recommendation_evaluation(file_path: str):
    """Main execution loop for recommendation evaluation."""
    evaluator = RecommendationEvaluator()
    
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Assuming the file contains recommendation results to evaluate
    business_context = data.get('business_domain')
    campaign_target = data.get('campaign_target')
    campaign_data = data.get('input_data') or data.get('campaign_data')
    analysis_context = data.get('analysis_response')
    recommendations = data.get('recommendation_response', {}).get('recommendations', [])

    results = []
    for rec in recommendations:
        try:
            eval_res = evaluator.evaluate(business_context, campaign_target, campaign_data, analysis_context, rec)
            results.append({
                "recommendation_title": rec.get("title"),
                "evaluation": eval_res
            })
        except Exception as e:
            logger.error(f"Failed to evaluate recommendation '{rec.get('title')}': {e}")

    if results:
        save_path = save_results_to_json(results, filename="recommendation_evaluation_results.json")
        logger.info(f"Recommendation evaluation results saved to: {save_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    args = parser.parse_args()
    
    from dotenv import load_dotenv
    load_dotenv()
    
    run_recommendation_evaluation(args.file)
