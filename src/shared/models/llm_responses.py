from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional, Dict, Literal, Any

# ==========================================
# STAGE 1: ANALYSIS SCHEMAS
# ==========================================
class BudgetEfficiencyInsight(BaseModel):
    insight: str = Field(description="what spend allocation/efficiency shows")
    evidence: str = Field(description="which platforms/metrics support it")
    business_impact: str = Field(description="why it matters to the target")

class ResultsValueInsight(BaseModel):
    insight: str = Field(description="what outcomes are being generated")
    evidence: str = Field(description="leads/customers/revenue/ROAS/CAC as available")
    business_impact: str = Field(description="link to acquisition and revenue impact")

class CrossChannelPattern(BaseModel):
    pattern_or_risk: str
    evidence: str
    why_it_matters: str

class ChannelNote(BaseModel):
    platform: str
    what_we_see: List[str] = Field(..., min_length=1, description="Factual observations")
    what_it_likely_means: List[str] = Field(..., min_length=1, description="Hypotheses tied to observations")
    risks_or_watchouts: List[str]

class AnalysisSection(BaseModel):
    executive_summary: str = Field(..., min_length=10, description="plain English, business-focused summary")
    budget_and_efficiency: List[BudgetEfficiencyInsight]
    results_and_value: List[ResultsValueInsight]
    cross_channel_patterns_and_risks: List[CrossChannelPattern]
    channel_notes: List[ChannelNote] = Field(..., min_length=1)
    missing_info: List[str] = Field(description="missing element + why it matters")

class AnalysisResponse(BaseModel):
    analysis: AnalysisSection

def validate_analysis_output(output: Dict[str, Any]) -> bool:
    try:
        AnalysisResponse.model_validate(output)
        return True
    except ValidationError:
        return False

# ==========================================
# STAGE 2: RECOMMENDATION SCHEMAS
# ==========================================
class RecommendationCard(BaseModel):
    title: str = Field(description="short, direct, outcome-focused title")
    whats_happening: str = Field(description="simple explanation of issue/opportunity")
    what_you_should_do: List[str] = Field(..., min_length=1, description="actionable steps")
    why_this_matters: str = Field(description="business impact in plain English")
    priority: Literal["High", "Medium", "Low"] = Field(description="High, Medium, or Low")
    expected_impact: str = Field(description="directional improvement, no numeric promises unless supported")
    owner_suggestion: str = Field(description="e.g., 'Media buyer', 'Creative team', 'Web team', 'Analytics'")

class RecommendationResponse(BaseModel):
    recommendations: List[RecommendationCard] = Field(..., min_length=4, max_length=4)

def validate_recommendation_output(output: Dict[str, Any]) -> bool:
    try:
        RecommendationResponse.model_validate(output)
        return True
    except ValidationError:
        return False


# ==========================================
# STAGE 3: EVALUATION SCHEMAS
# ==========================================
class EvaluationSection(BaseModel):
    clarity_reasoning: str
    clarity_score: int = Field(ge=1, le=3)
    accuracy_reasoning: str
    accuracy_score: int = Field(ge=1, le=3)
    structure_reasoning: str
    structure_score: int = Field(ge=1, le=3)
    feasibility_reasoning: Optional[str] = None
    feasibility_score: Optional[int] = Field(None, ge=1, le=3)
    verdict: str = Field(description="reject, revise, or accept")
    key_issues: List[str]
    improvement_suggestions: List[str]

class AnalysisEvaluationResponse(BaseModel):
    evaluation: EvaluationSection

class RecommendationEvaluationResponse(BaseModel):
    evaluation: EvaluationSection


if __name__ == "__main__":
    # Example: Generate output object from AnalysisResponse
    example_analysis = AnalysisResponse(
        analysis=AnalysisSection(
            executive_summary="Sample analysis summary",
            budget_and_efficiency=[
                BudgetEfficiencyInsight(
                    insight="High spend on underperforming channel",
                    evidence="Channel X has 2x higher CAC than benchmark",
                    business_impact="Reallocating 20% budget could improve overall ROAS"
                )
            ],
            results_and_value=[
                ResultsValueInsight(
                    insight="Strong lead generation volume",
                    evidence="1,500 leads/month at $15 CAC",
                    business_impact="Supports 30% MoM revenue growth"
                )
            ],
            cross_channel_patterns_and_risks=[
                CrossChannelPattern(
                    pattern_or_risk="Attribution overlap between channels",
                    evidence="30% of converters touched 2+ channels",
                    why_it_matters="Multi-touch attribution needed for accurate ROI"
                )
            ],
            channel_notes=[
                ChannelNote(
                    platform="Google Ads",
                    what_we_see=["$50K spend", "1,200 conversions"],
                    what_it_likely_means=["Strong brand search intent", "Mature campaign"],
                    risks_or_watchouts=["ROAS trending down YoY"]
                )
            ],
            missing_info=["Customer lifetime value", "Competitor spend data"]
        )
    )
    
    print("Analysis Response object created successfully:")
    print(example_analysis.model_dump_json(indent=2))
    print("\nStructured outputs schema definitions loaded successfully.")
