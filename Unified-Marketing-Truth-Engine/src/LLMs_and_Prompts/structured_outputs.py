from pydantic import BaseModel, Field
from typing import List

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
    what_we_see: List[str] = Field(description="Factual observations")
    what_it_likely_means: List[str] = Field(description="Hypotheses tied to observations")
    risks_or_watchouts: List[str]

class AnalysisSection(BaseModel):
    executive_summary: str = Field(description="plain English, business-focused summary")
    budget_and_efficiency: List[BudgetEfficiencyInsight]
    results_and_value: List[ResultsValueInsight]
    cross_channel_patterns_and_risks: List[CrossChannelPattern]
    channel_notes: List[ChannelNote]
    missing_info: List[str] = Field(description="missing element + why it matters")

class AnalysisResponse(BaseModel):
    analysis: AnalysisSection

# ==========================================
# STAGE 2: RECOMMENDATION SCHEMAS
# ==========================================

class RecommendationCard(BaseModel):
    title: str = Field(description="short, direct, outcome-focused title")
    whats_happening: str = Field(description="simple explanation of issue/opportunity")
    what_you_should_do: List[str] = Field(description="actionable steps")
    why_this_matters: str = Field(description="business impact in plain English")
    priority: str = Field(description="High, Medium, or Low")
    expected_impact: str = Field(description="directional improvement, no numeric promises unless supported")
    owner_suggestion: str = Field(description="e.g., 'Media buyer', 'Creative team', 'Web team', 'Analytics'")

class RecommendationResponse(BaseModel):
    recommendations: List[RecommendationCard]
