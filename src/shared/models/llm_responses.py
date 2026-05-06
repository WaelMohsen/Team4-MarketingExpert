from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional, Dict, Literal, Any

# ==========================================
# STAGE 1: ANALYSIS SCHEMAS
# ==========================================
class BudgetEfficiencyInsight(BaseModel):
    insight: str = Field(
        description="What the spend pattern shows — must reference at least 2 metrics"
    )
    evidence: str = Field(
        description="The specific metric values that support the insight, e.g. 'CPC $1.26, ROAS 1.8'"
    )
    business_impact: str = Field(
        description="Why this efficiency finding matters to the campaign goal in plain English"
    )

class ResultsValueInsight(BaseModel):
    insight: str = Field(
        description="What outcomes the campaign produced — must reference at least 2 metrics"
    )
    evidence: str = Field(
        description="The specific metric values that support the insight, e.g. '159 conversions at $16.74 CPA'"
    )
    business_impact: str = Field(
        description="Link to acquisition, revenue, or funnel impact in plain English"
    )

class CrossChannelPattern(BaseModel):
    pattern_or_risk: str = Field(
        description="The anomaly, trend, or risk observed across channels — fact or labeled hypothesis"
    )
    evidence: str = Field(
        description="The specific metrics or channel data that surface this pattern"
    )
    why_it_matters: str = Field(
        description="Business consequence if this pattern continues or goes unaddressed"
    )

class ChannelNote(BaseModel):
    platform: str = Field(description="Platform name, e.g. 'Google Ads', 'Meta'")
    what_we_see: List[str] = Field(
        ..., min_length=1,
        description="Factual observations with metric values — no interpretation"
    )
    what_it_likely_means: List[str] = Field(
        ..., min_length=1,
        description="Hypotheses tied to observations — prefix assumptions with 'likely' or 'suggests'"
    )
    risks_or_watchouts: List[str] = Field(
        ..., min_length=1,
        description="Risks or flags for downstream recommendation system"
    )

class AnalysisSection(BaseModel):
    executive_summary: str = Field(
        ..., min_length=10,
        description=(
            "Plain-English verdict covering: overall performance (strong/mixed/weak), "
            "budget efficiency, outcome quality, and the single most important risk or gap"
        )
    )
    budget_and_efficiency: List[BudgetEfficiencyInsight]
    results_and_value: List[ResultsValueInsight]
    cross_channel_patterns_and_risks: List[CrossChannelPattern]
    channel_notes: List[ChannelNote] = Field(..., min_length=1)
    missing_info: List[str] = Field(
        default_factory=list,
        description=(
            "Data absent from the input that would materially change the analysis — "
            "state what is missing and why it matters"
        )
    )

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
    title: str = Field(
        description="Short imperative phrase, e.g. 'Fix Click Loss on Landing Page'"
    )
    whats_happening: str = Field(
        description=(
            "Plain-English description of the issue, "
            "referencing the specific metric or finding from the analysis."
        )
    )
    what_you_should_do: List[str] = Field(
        ...,
        min_length=1,
        description=(
            "Each action must answer WHAT to change, "
            "WHERE to apply it, and HOW to execute it."
        ),
    )
    why_this_matters: str = Field(
        description="Business consequence of inaction, tied to the campaign goal."
    )
    priority: Literal["High", "Medium", "Low"]
    expected_impact: str = Field(
        description=(
            "Directional or quantified outcome tied to a metric, "
            "e.g. 'Estimated 15–25% CTR improvement' or 'Reduce CPC by ~$0.20'."
        )
    )
    owner_suggestion: str = Field(
        description=(
            "Job role or team responsible, "
            "e.g. 'Paid Media Manager', 'Growth Team', 'Web/Tech Team'."
        )
    )

class RecommendationResponse(BaseModel):
    recommendations: List[RecommendationCard] = Field(
        ..., min_length=4, max_length=4,
        description="Always exactly 4 recommendations."
    )

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

    verdict: Literal["accept", "revise", "reject"]

    key_issues: List[str]
    improvement_suggestions: List[str]

    
class AnalysisEvaluationResponse(BaseModel):
    evaluation: EvaluationSection

class RecommendationEvaluationSection(BaseModel):
    structure_score: int = Field(ge=1, le=3)
    structure_reasoning: str
    feasibility_score: int = Field(ge=1, le=3)
    feasibility_reasoning: str
    Recommendation_Count_score: int = Field(ge=1, le=3)
    Recommendation_Count_reasoning: str
    Analysis_Grounding_score: int = Field(ge=1, le=3)
    Analysis_Grounding_reasoning: str
    Action_Step_Completeness_score: int = Field(ge=1, le=3)
    Action_Step_Completeness_reasoning: str
    Priority_Alignment_score: int = Field(ge=1, le=3)
    Priority_Alignment_reasoning: str
    Tone_Audience_Compliance_score: int = Field(alias="Tone_&_Audience_Compliance_score", default=1, ge=1, le=3)
    Tone_Audience_Compliance_reasoning: str = Field(alias="Tone_&_Audience_Compliance_reasoning")
    Expected_Impact_Quality_score: int = Field(ge=1, le=3)
    Expected_Impact_Quality_reasoning: str
    instruction_adherence_reasoning: str
    instruction_adherence_score: int = Field(ge=1, le=3)
    verdict: str = Field(description="reject, revise, or accept")
    key_issues: List[str]
    improvement_suggestions: List[str]

    class Config:
        populate_by_name = True

class RecommendationEvaluationResponse(BaseModel):
    evaluation: RecommendationEvaluationSection


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
