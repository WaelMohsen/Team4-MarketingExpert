import json
import logging
import os
from typing import List, Dict, Any

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
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            max_output_tokens=2000
        )

    def evaluate(self, business_context: Any, campaign_target: Any, campaign_data: Any, analysis_context: Any, recommendation: Any) -> Dict[str, Any]:
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
        result = self.client.generate_json(messages, response_format=RecommendationEvaluationResponse)
        
        eval_data = result.get("evaluation", {})
        
        return {
            "scores": {
                "clarity": eval_data.get("clarity_score", 0),
                "accuracy": eval_data.get("accuracy_score", 0),
                "structure": eval_data.get("structure_score", 0),
                "feasibility": eval_data.get("feasibility_score", 0),
                "overall": (eval_data.get("clarity_score", 0) + eval_data.get("accuracy_score", 0) + 
                           eval_data.get("structure_score", 0) + eval_data.get("feasibility_score", 0)) / 4
            },
            "reasoning": {
                "clarity": eval_data.get("clarity_reasoning"),
                "accuracy": eval_data.get("accuracy_reasoning"),
                "structure": eval_data.get("structure_reasoning"),
                "feasibility": eval_data.get("feasibility_reasoning"),
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
    business_context = data.get('business_domain') or data.get('campaign_target')
    analysis_context = data.get('analysis_results')
    recommendations = data.get('recommendation_results', {}).get('recommendations', [])

    results = []
    for rec in recommendations:
        try:
            eval_res = evaluator.evaluate(business_context, analysis_context, rec)
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
