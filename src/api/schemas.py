from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class AnalysisRequest(BaseModel):
    campaign_data: Dict[str, Any]
    business_domain: Optional[Dict[str, Any]] = None
    campaign_target: Optional[Dict[str, Any]] = None

class RecommendationRequest(BaseModel):
    campaign_data: Dict[str, Any]
    analysis_results: Optional[Dict[str, Any]] = None
    business_domain: Optional[Dict[str, Any]] = None
    campaign_target: Optional[Dict[str, Any]] = None
