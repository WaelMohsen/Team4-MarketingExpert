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
    business_context = data.get('business_domain')
    campaign_target = data.get('campaign_target')
    campaign_data = data.get('input_data') or data.get('campaign_data')
    analysis_context = data.get('analysis_response')
    recommendations = data.get('recommendation_response', {}).get('recommendations', [])

    if not recommendations and 'recommendations' in data:
        recommendations = data['recommendations']
        
    if not campaign_data:
        dir_name = os.path.dirname(file_path)
        enriched_summary_path = os.path.join(dir_name, 'enriched_summary.json')
        analysis_result_path = os.path.join(dir_name, 'analysis_result.json')
        
        if os.path.exists(enriched_summary_path):
            try:
                with open(enriched_summary_path, 'r', encoding='utf-8') as ef:
                    enriched_data = json.load(ef)
                    campaign_data = enriched_data
                    if not business_context:
                        identity = enriched_data.get('campaign_identity', {})
                        business_context = {
                            "industry": identity.get("industry", "Unknown"),
                            "offering": identity.get("offering", "Unknown"),
                            "audience": identity.get("audience", "Unknown"),
                            "funnel_stage": identity.get("funnel_stage", "Unknown")
                        }
                    if not campaign_target:
                        campaign_target = {"primary_goal": "Unknown"}
            except Exception as e:
                logger.warning(f"Could not load context from {enriched_summary_path}: {e}")
                
        if not analysis_context and os.path.exists(analysis_result_path):
            try:
                with open(analysis_result_path, 'r', encoding='utf-8') as af:
                    analysis_context = json.load(af)
            except Exception as e:
                logger.warning(f"Could not load analysis from {analysis_result_path}: {e}")

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
