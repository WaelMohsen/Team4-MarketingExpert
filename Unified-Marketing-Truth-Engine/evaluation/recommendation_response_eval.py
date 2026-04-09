import json
import logging
import os
from typing import List, Dict, Any

import dspy

logger = logging.getLogger(__name__)


class EvaluateRecommendation(dspy.Signature):
    """
    Evaluate the quality of a marketing recommendation for non-marketer end users.

    The evaluation should consider:
    - Clarity: Is the recommendation easy to understand and actionable?
    - Accuracy: Is it logically correct and grounded in the provided context?
    - Non-redundancy: Is it specific and avoids generic or repeated advice?

    The evaluator MUST:
    - Use only the provided inputs (no assumptions).
    - Be strict and critical (avoid inflated scores).
    - Justify each score with concrete reasoning.
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
            "Explain whether the recommendation is clear, specific, and actionable. "
            "Mention if steps, metrics, or examples are missing or vague."
        )
    )
    clarity_score = dspy.OutputField(
        desc=(
            "Integer score (1-5): "
            "1=very vague/unusable, 3=somewhat clear but incomplete, 5=very clear and directly actionable."
        )
    )

    # Accuracy
    accuracy_reasoning = dspy.OutputField(
        desc=(
            "Explain whether the recommendation logically follows from the analysis_context. "
            "Highlight mismatches, unsupported claims, or correct data usage."
        )
    )
    accuracy_score = dspy.OutputField(
        desc=(
            "Integer score (1-5): "
            "1=incorrect/misleading, 3=partially correct, 5=fully grounded and logically sound."
        )
    )

    # Non-redundancy
    redundancy_reasoning = dspy.OutputField(
        desc=(
            "Explain whether the recommendation is specific vs generic. "
            "Call out clichés (e.g., 'improve targeting', 'optimize creatives') if not contextualized."
        )
    )
    non_redundancy_score = dspy.OutputField(
        desc=(
            "Integer score (1-5): "
            "1=generic/repetitive, 3=somewhat specific, 5=highly tailored and unique."
        )
    )

    # Overall judgment
    overall_score = dspy.OutputField(
        desc=(
            "Weighted overall score (1-5). Prioritize accuracy > clarity > non-redundancy."
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
            "List of the most critical problems in the recommendation (bullet points)."
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
        self.evaluate = dspy.ChainOfThought(EvaluateRecommendation)

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
        non_redundancy_score = self._safe_parse_score(result.non_redundancy_score)

        # --- Weighted overall (accuracy > clarity > non-redundancy) ---
        weighted_overall = (
            (0.5 * accuracy_score) +
            (0.3 * clarity_score) +
            (0.2 * non_redundancy_score)
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
                "non_redundancy": non_redundancy_score,
                "overall": final_overall_score
            },
            "reasoning": {
                "clarity": result.clarity_reasoning,
                "accuracy": result.accuracy_reasoning,
                "non_redundancy": result.redundancy_reasoning
            },
            "verdict": verdict,
            "key_issues": key_issues,
            "improvement_suggestions": improvement_suggestions,

            # Optional debug info (very useful in pipelines)
            "meta": {
                "weighted_overall": weighted_overall,
                "llm_overall_used": use_llm_score
            }
        }


def evaluate_recommendations(
    recommendations_data: List[Dict[str, Any]], 
    campaign_target: Dict[str, Any], 
    business_domain: Dict[str, Any], 
    analysis_context: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Evaluate a list of recommendations using contextual campaign data.

    Returns a list of structured evaluation results.
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
                "scores": {"clarity": 0.0, "accuracy": 0.0, "non_redundancy": 0.0, "overall": 0.0},
                "reasoning": {"clarity": "Error", "accuracy": "Error", "non_redundancy": "Error"},
                "verdict": "error",
                "key_issues": [f"Evaluation failed with error: {str(e)}"],
                "improvement_suggestions": [],
                "meta": {"error": str(e)}
            }

        # Attach metadata
        eval_result["recommendation_index"] = idx
        eval_result["original_recommendation"] = rec

        # Extract scores safely for logging
        scores = eval_result.get("scores", {})
        clarity = scores.get("clarity", 0.0)
        accuracy = scores.get("accuracy", 0.0)
        non_redundancy = scores.get("non_redundancy", 0.0)
        overall = scores.get("overall", 0.0)

        logger.info(
            f"[Rec {idx + 1}] "
            f"Clarity: {clarity:.2f} | "
            f"Accuracy: {accuracy:.2f} | "
            f"Non-Redundancy: {non_redundancy:.2f} | "
            f"Overall: {overall:.2f} | "
            f"Verdict: {eval_result.get('verdict', 'N/A')}"
        )

        results.append(eval_result)

    # --- Optional: Rank recommendations by overall score ---
    results = sorted(
        results,
        key=lambda x: x.get("scores", {}).get("overall", 0.0),
        reverse=True
    )

    logger.info("\nEvaluation completed. Recommendations ranked by overall score.\n")

    return results

if __name__ == "__main__":
    from pathlib import Path
    
    BASE_DIR = Path(__file__).resolve().parent.parent
    LOG_DIR = BASE_DIR / "logs"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    log_file = LOG_DIR / "recommendation_evaluation.log"
    
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

    # --- Sample Inputs ---
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
    
    # --- Run Evaluation ---
    logger.info("Executing evaluation...\n")

    eval_output = evaluate_recommendations(
        sample_recommendations,
        campaign_target=sample_campaign_target,
        business_domain=sample_business_domain,
        analysis_context=sample_analysis_context
    )

    # --- Pretty Summary ---
    print("\n" + "="*60)
    print("           EVALUATION SUMMARY (RANKED)")
    print("="*60)

    for i, rec in enumerate(eval_output, 1):
        scores = rec.get("scores", {})
        title = rec.get("original_recommendation", {}).get("title", "N/A")

        print(f"\n#{i} - {title}")
        print("-" * 60)
        print(f"Overall Score : {scores.get('overall', 0):.2f}")
        print(f"Clarity       : {scores.get('clarity', 0):.2f}")
        print(f"Accuracy      : {scores.get('accuracy', 0):.2f}")
        print(f"Non-Redundancy: {scores.get('non_redundancy', 0):.2f}")
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

    # --- Aggregate Stats ---
    print("\n" + "="*60)
    print("           AGGREGATE METRICS")
    print("="*60)

    if eval_output:
        avg_score = sum(r["scores"]["overall"] for r in eval_output) / len(eval_output)
        accept_count = sum(1 for r in eval_output if r["verdict"] == "accept")
        revise_count = sum(1 for r in eval_output if r["verdict"] == "revise")
        reject_count = sum(1 for r in eval_output if r["verdict"] == "reject")

        print(f"Average Score : {avg_score:.2f}")
        print(f"Accepted      : {accept_count}")
        print(f"Needs Revision: {revise_count}")
        print(f"Rejected      : {reject_count}")

    # --- Save Output to File ---
    output_path = LOG_DIR / "evaluation_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(eval_output, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Evaluation results successfully saved to: {output_path}")
