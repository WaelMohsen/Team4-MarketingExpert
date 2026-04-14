import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Any

from src.shared.utils.prompt_loader import PromptLoader
from src.shared.utils.prompt_builder import PromptBuilder
from src.shared.utils.llm_client import LLMApiClient
from src.shared.models.llm_responses import AnalysisEvaluationResponse
from src.shared.utils.prompt_registry import PromptRegistry

# Configure logging using shared structure
try:
    from src.shared.utils.logger import setup_logging
    logger = setup_logging(module_name ='llm_analysis_evaluator')
    from src.shared.utils.json_saver import save_results_to_json
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

class AnalysisEvaluator:
    """
    Evaluates campaign analysis reports using manual prompts and structured outputs.
    """
    def __init__(self):
        self.loader = PromptLoader.from_module_dir()
        self.builder = PromptBuilder(loader=self.loader)
        self.client = LLMApiClient(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            max_output_tokens=2000
        )

    def evaluate(self, campaign_data: Any, analysis_report: Any, campaign_target: Any, business_domain: Any) -> Dict[str, Any]:
        """Runs the evaluation using LLMApiClient."""
        
        # Prepare context strings
        context = {
            "target": campaign_target,
            "business_domain": business_domain
        }
        
        
        # We'll use a more flexible replacement for evaluation
        sys_text = self.loader.load_prompt_text(PromptRegistry.EVAL_ANALYSIS_SYSTEM.value)
        user_text = self.loader.load_prompt_text(PromptRegistry.EVAL_ANALYSIS_USER.value)
        
        user_text = (
            user_text.replace("{{CAMPAIGN_CONTEXT}}", json.dumps(context, indent=2))
            .replace("{{RAW_DATA}}", json.dumps(campaign_data, indent=2))
            .replace("{{ANALYSIS_REPORT}}", json.dumps(analysis_report, indent=2))
        )
        
        messages = [
            {"role": "system", "content": sys_text},
            {"role": "user", "content": user_text}
        ]

        logger.info("Executing Analysis Evaluation...")
        result = self.client.generate_json(messages, response_format=AnalysisEvaluationResponse)
        
        # Structure it for the existing reporter
        eval_data = result.get("evaluation", {})
        
        return {
            "scores": {
                "clarity": eval_data.get("clarity_score", 0),
                "accuracy": eval_data.get("accuracy_score", 0),
                "structure": eval_data.get("structure_score", 0),
                "overall": (eval_data.get("clarity_score", 0) + eval_data.get("accuracy_score", 0) + eval_data.get("structure_score", 0)) / 3
            },
            "reasoning": {
                "clarity": eval_data.get("clarity_reasoning"),
                "accuracy": eval_data.get("accuracy_reasoning"),
                "structure": eval_data.get("structure_reasoning"),
            },
            "verdict": eval_data.get("verdict"),
            "key_issues": eval_data.get("key_issues"),
            "improvement_suggestions": eval_data.get("improvement_suggestions"),
        }

def run_evaluation_pipeline(files: List[str]):
    """Main execution loop for analysis evaluation."""
    evaluator = AnalysisEvaluator()
    
    for file_path in files:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            continue

        logger.info(f"Processing File: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        campaign_data = data.get('input_data') or data.get('campaign_data')
        analysis_report = data.get('analysis_response')
        campaign_target = data.get('campaign_target')
        business_domain = data.get('business_domain')

        if not all([campaign_data, analysis_report]):
            logger.warning(f"Skipping {file_path}: missing required fields.")
            continue

        try:
            comparison_results = evaluator.evaluate(campaign_data, analysis_report, campaign_target, business_domain)
            
            # Save results
            save_path = save_results_to_json(comparison_results, filename="analysis_evaluation_results.json")
            logger.info(f"Evaluation results saved to: {save_path}")
            
            # Print summary
            print("\nEvaluation Summary:")
            print(json.dumps(comparison_results["scores"], indent=2))
            print(f"Verdict: {comparison_results['verdict']}")

        except Exception as e:
            logger.error(f"Failed to evaluate {file_path}: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--files", nargs="+", required=True)
    args = parser.parse_args()
    
    from dotenv import load_dotenv
    load_dotenv()
    
    run_evaluation_pipeline(args.files)
