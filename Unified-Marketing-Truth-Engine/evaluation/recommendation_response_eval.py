import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Any

import dspy

logger = logging.getLogger(__name__)


class ResponsePromptBuilder(dspy.Signature):
    """
    Evaluate the quality of a marketing recommendation for non-marketer end users.

    The evaluation should consider:
    - Clarity: Is the recommendation easy to understand and actionable?
    - Accuracy: Is it logically correct and grounded in the provided context?
    - Output Structure: Does the recommendation follow the required structure (e.g., JSON format with specific fields)?
    - Feasibility: Is it realistic and implementable given platform capabilities, permissions, and available data?

    The evaluator MUST:
    - Use only the provided inputs (no assumptions).
    - Be strict and critical (avoid inflated scores).
    - Justify each score with concrete reasoning.
    - limit reasoning to 200 characters per reasoning field
    - Return structured, consistent outputs.
    """

    # Inputs
    campaign_target = dspy.InputField(
        desc="Campaign goal and KPIs (e.g., increase CTR, reduce CPA, improve ROAS)."
    )
    business_domain = dspy.InputField(
        desc="Industry, product/service, audience, and funnel stage."
    )
    analysis_context = dspy.InputField(
        desc="Key insights derived from campaign data (metrics, trends, issues)."
    )
    recommendation = dspy.InputField(
        desc="The recommendation to evaluate (usually structured JSON)."
    )
    # Clarity
    clarity_reasoning = dspy.OutputField(
        desc=(
            "Explain whether the recommendation is clear,specific, not vague, and easy to understand for a non-marketer end user. "
            "Mention if steps, metrics, or examples are missing or vague."
        )
    )
    clarity_score = dspy.OutputField(
        desc=(
            "Integer score (1-3): " 
            "1=very vague/unusable, 2=somewhat clear but incomplete, 3=very clear ."
        )
    )

    # Accuracy
    accuracy_reasoning = dspy.OutputField(
        desc=(
            "Explain whether the recommendation logically follows from the analysis_context, and follows marketing best practices. " 
            "Highlight mismatches, unsupported claims, or incorrect data usage."
        )
    )
    accuracy_score = dspy.OutputField(
        desc=(
            "Integer score (1-3): "
            "1=incorrect/misleading, 2=partially correct, 3=fully grounded and logically sound."
        )
    )

    # Output Structure
    output_structure_reasoning = dspy.OutputField(
        desc="Explain whether the recommendation follows the required structure (e.g., JSON format with specific fields)."
    )

    output_structure_score = dspy.OutputField(
        desc=(
            "Integer score (1-3): "
            "1=missing most sections, "
            "2=partially structured, "
            "3=fully structured and well-formatted."
        )
    )

    # Feasibility
    feasibility_reasoning = dspy.OutputField(
        desc="Explain whether the recommendation can be implemented given platform capabilities, permissions, and available data."
    )

    feasibility_score = dspy.OutputField(
        desc=(
            "Integer score (1-3): "
            "1=Not feasible (requires unavailable features, permissions, or unrealistic changes), "
            "2=Partially feasible (requires extra setup, dependencies, or unclear steps), "
            "3=Fully feasible (directly implementable with current platform and permissions)."
        )
    )

    # Overall judgment
    overall_score = dspy.OutputField(
        desc=(
            "Weighted overall score (1-3). Prioritize accuracy > clarity > output_structure > feasibility."
        )
    )

    verdict = dspy.OutputField(
        desc=(
            "Final decision: one of ['reject', 'revise', 'accept']. "
            "Reject = major issues, Revise = usable but needs improvement, Accept = high quality."
        )
    )

    key_issues = dspy.OutputField(
        desc=(
            "Python list of the most critical problems in the recommendation (bullet points)." # TODO: make sure it is list
        )
    )

    improvement_suggestions = dspy.OutputField(
        desc=(
            "Concrete suggestions to improve the recommendation (specific rewrites or additions)."
        )
    )



class RecommendationEvaluator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.evaluate = dspy.ChainOfThought(ResponsePromptBuilder)

    def _safe_parse_score(self, value, default=0.0):
        """Robust score parsing (handles int, float, string, None)."""
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def forward(
        self,
        campaign_target: str,
        business_domain: str,
        analysis_context: str,
        recommendation: str
    ) -> Dict[str, Any]:
        """
        Evaluate a recommendation using campaign context.

        Returns structured evaluation including:
        - individual scores
        - reasoning
        - overall score (weighted)
        - verdict
        - improvement signals
        """

        result = self.evaluate(
            campaign_target=campaign_target,
            business_domain=business_domain,
            analysis_context=analysis_context,
            recommendation=recommendation
        )

        # --- Parse scores safely ---
        clarity_score = self._safe_parse_score(result.clarity_score)
        accuracy_score = self._safe_parse_score(result.accuracy_score)
        output_structure_score = self._safe_parse_score(result.output_structure_score)
        feasibility_score = self._safe_parse_score(result.feasibility_score)
        # --- Weighted overall (accuracy > clarity > output_structure > feasibility) ---
        weighted_overall = (
            (0.5 * accuracy_score) +
            (0.3 * clarity_score) +
            (0.2 * output_structure_score) +
            (0.1 * feasibility_score)
        )

        # --- Try to use LLM-provided overall_score if valid ---
        llm_overall_score = self._safe_parse_score(
            getattr(result, "overall_score", None),
            default=None
        )

        use_llm_score = llm_overall_score is not None and llm_overall_score > 0

        final_overall_score = (
            llm_overall_score
            if use_llm_score
            else weighted_overall
        )

        # --- Extract optional fields safely ---
        verdict = getattr(result, "verdict", "unknown")

        key_issues = getattr(result, "key_issues", [])
        if isinstance(key_issues, str):
            key_issues = [key_issues]

        improvement_suggestions = getattr(result, "improvement_suggestions", [])
        if isinstance(improvement_suggestions, str):
            improvement_suggestions = [improvement_suggestions]

        # --- Final structured output ---
        return {
            "scores": {
                "clarity": clarity_score,
                "accuracy": accuracy_score,
                "output_structure": output_structure_score,
                "feasibility": feasibility_score,
                "overall": final_overall_score
            },
            "reasoning": {
                "clarity": result.clarity_reasoning,
                "accuracy": result.accuracy_reasoning,
                "output_structure": result.output_structure_reasoning,
                "feasibility": result.feasibility_reasoning,
            },
            "verdict": verdict,
            "key_issues": key_issues,
            "improvement_suggestions": improvement_suggestions,

        }


def evaluate_recommendations(
    recommendations_data: List[Dict[str, Any]], 
    campaign_target: Dict[str, Any], 
    business_domain: Dict[str, Any], 
    analysis_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluate a list of recommendations using contextual campaign data.
    Returns a unified campaign evaluation object.
    """

    evaluator = RecommendationEvaluator()
    results = []
    
    # Convert structures to string once
    campaign_target_str = json.dumps(campaign_target, indent=2)
    business_domain_str = json.dumps(business_domain, indent=2)
    analysis_context_str = json.dumps(analysis_context, indent=2)
    
    for idx, rec in enumerate(recommendations_data):
        logger.info(f"Evaluating Recommendation {idx + 1}...")
        
        rec_str = json.dumps(rec, indent=2)
        
        try:
            eval_result = evaluator(
                campaign_target=campaign_target_str,
                business_domain=business_domain_str,
                analysis_context=analysis_context_str,
                recommendation=rec_str
            )
        except Exception as e:
            logger.error(f"Evaluation failed for recommendation {idx + 1}: {e}")
            eval_result = {
                "scores": {"clarity": 0.0, "accuracy": 0.0, "output_structure": 0.0, "feasibility": 0.0, "overall": 0.0},
                "reasoning": {"clarity": "Error", "accuracy": "Error", "output_structure": "Error", "feasibility": "Error"},
                "verdict": "error",
                "key_issues": [f"Evaluation failed with error: {str(e)}"],
                "improvement_suggestions": [],
                "meta": {"error": str(e)}
            }

        # Attach metadata and original objects (as JSON objects, not strings)
        eval_result = {
            "campaign_target": campaign_target,
            "business_domain": business_domain,
            "analysis_context": analysis_context,
            "recommendation": rec,
            "recommendation_index": idx,
            **eval_result
        }
        results.append(eval_result)

    # --- Rank recommendations by overall score ---
    results = sorted(
        results,
        key=lambda x: x.get("scores", {}).get("overall", 0.0),
        reverse=True
    )

    # --- Aggregate Stats ---
    avg_score = sum(r["scores"]["overall"] for r in results) / len(results) if results else 0.0
    verdict_counts = {
        "accept": sum(1 for r in results if r["verdict"] == "accept"),
        "revise": sum(1 for r in results if r["verdict"] == "revise"),
        "reject": sum(1 for r in results if r["verdict"] == "reject"),
        "error": sum(1 for r in results if r["verdict"] == "error")
    }

    logger.info("\nEvaluation completed. Recommendations ranked by overall score.\n")

    return {
        "campaign_target": campaign_target,
        "business_domain": business_domain,
        "analysis_context": analysis_context,
        "campaign_evaluation": {
            "overall_score": avg_score,
            "verdicts": verdict_counts,
            "recommendation_count": len(results),
            "timestamp": datetime.now().isoformat()
        },
        "recommendation_details": results
    }

def print_evaluation_summary(campaign_eval: Dict[str, Any]):
    """Prints a pretty summary of the campaign evaluation."""
    summary = campaign_eval.get("campaign_evaluation", {})
    recs = campaign_eval.get("recommendation_details", [])

    print("\n" + "="*60)
    print("           CAMPAIGN EVALUATION SUMMARY")
    print("="*60)
    print(f"Overall Score: {summary.get('overall_score', 0):.2f}")
    print(f"Total Recommendations: {summary.get('recommendation_count', 0)}")
    
    verdicts = summary.get("verdicts", {})
    print(f"Verdicts: Accept ({verdicts.get('accept', 0)}) | "
          f"Revise ({verdicts.get('revise', 0)}) | "
          f"Reject ({verdicts.get('reject', 0)})")
    
    print("\n" + "="*60)
    print("           DETAILED RECOMMENDATIONS (RANKED)")
    print("="*60)

    for i, rec in enumerate(recs, 1):
        scores = rec.get("scores", {})
        title = rec.get("original_recommendation", {}).get("title", "N/A")

        print(f"\n#{i} - {title}")
        print("-" * 60)
        print(f"Overall Score : {scores.get('overall', 0):.2f}")
        print(f"Clarity       : {scores.get('clarity', 0):.2f}")
        print(f"Accuracy      : {scores.get('accuracy', 0):.2f}")
        print(f"Output Structure: {scores.get('output_structure', 0):.2f}")
        print(f"Feasibility   : {scores.get('feasibility', 0):.2f}")
        print(f"Verdict       : {rec.get('verdict', 'N/A')}")

        # Show key issues (top 2 only for readability)
        issues = rec.get("key_issues", [])[:2]
        if issues:
            print("\nKey Issues:")
            for issue in issues:
                print(f"- {issue}")

        # Show top suggestion
        suggestions = rec.get("improvement_suggestions", [])[:1]
        if suggestions:
            print("\nTop Improvement:")
            print(f"-> {suggestions[0]}")

if __name__ == "__main__":
    import argparse
    from pathlib import Path
    
    parser = argparse.ArgumentParser(description="Evaluate Marketing Recommendations")
    parser.add_argument("--files", nargs="+", help="Specific JSON files to evaluate (e.g. data/outputs/campaign_1_result.json)")
    args = parser.parse_args()
    
    BASE_DIR = Path(__file__).resolve().parent.parent
    LOG_DIR = BASE_DIR / "logs"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create run directory
    run_dir = LOG_DIR / datetime.now().strftime("%Y-%m-%d")
    run_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = run_dir / "evaluation.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(str(log_file), encoding="utf-8"),
            logging.StreamHandler()
        ]
    )

    from dotenv import load_dotenv
    load_dotenv()

    # Configure DSPy LM
    try:
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        logger.info(f"Configuring DSPy LM with model: openai/{model}")
        lm = dspy.LM(f"openai/{model}")
        dspy.settings.configure(lm=lm)
    except Exception as e:
        logger.error(f"Failed to configure DSPy LM: {e}")
        raise

    if args.files:
        for file_path in args.files:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                logger.error(f"File not found: {file_path}")
                continue
                
            logger.info(f"\n--- Evaluating Campaign Result: {file_path_obj.name} ---")
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            campaign_target = data.get("campaign_target")
            business_domain = data.get("business_domain")
            analysis_context = data.get("analysis_response")
            recommendations_payload = data.get("recommendation_response", {}).get("recommendations", [])
            
            if not all([campaign_target, business_domain, analysis_context, recommendations_payload]):
                logger.warning(f"Skipping {file_path}: missing required fields.")
                continue
                
            eval_output = evaluate_recommendations(
                recommendations_payload,
                campaign_target=campaign_target,
                business_domain=business_domain,
                analysis_context=analysis_context
            )
            
            # Print Summary
            print_evaluation_summary(eval_output)
            
            # Save individual evaluation result
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_name = f"recommendations_evaluation_result_{file_path_obj.stem}_{timestamp}.json"
            output_path = run_dir / output_name
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(eval_output, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Evaluation for {file_path_obj.name} saved to: {output_path}")

    else:
        # Fallback to Sample Run if no files provided
        logger.info("No files provided. Running sample evaluation...\n")
        
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
                "executive_summary": "Google Ads is driving a high ROAS of 4.5x but has a limited impression share due to budget caps...",
            }
        }

        sample_recommendations = [
            {
                "title": "Shift Meta Budget to fully fund Google Ads",
                "whats_happening": "Google Ads has a 4.5x ROAS but is budget-capped...",
                "what_you_should_do": ["Reduce Meta daily budgets by 30%", "Reallocate to Google"],
                "why_this_matters": "capture high-intent demand",
                "priority": "High",
                "expected_impact": "Improved blended ROAS",
                "owner_suggestion": "Media buyer"
            }
        ]

        eval_output = evaluate_recommendations(
            sample_recommendations,
            campaign_target=sample_campaign_target,
            business_domain=sample_business_domain,
            analysis_context=sample_analysis_context
        )
        
        print_evaluation_summary(eval_output)
        # save file with timestamp
        output_path = run_dir / ("sample_evaluation_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(eval_output, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Sample evaluation results saved to: {output_path}")
