import os
import logging
import pandas as pd
from fastapi import FastAPI, HTTPException
from src.api.schemas import AnalysisRequest, RecommendationRequest
from src.core.execution_context import ExecutionContext
from src.modules.enrichment.enrichment_module import EnrichmentModule
from src.modules.analysis.analysis_module import AnalysisModule
from src.modules.recommendation.recommendation_module import RecommendationModule

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(name)s | %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Marketing Intelligence API",
    description="API for Stage 1 Analysis and Stage 2 Recommendations",
    version="1.0.0"
)

# Initialize modules
enrichment_module = EnrichmentModule()
analysis_module = AnalysisModule()
recommendation_module = RecommendationModule()

@app.get("/")
async def root():
    return {"message": "Welcome to the Marketing Intelligence API"}

@app.post("/api/v1/analysis")
async def analyze(request: AnalysisRequest):
    """
    Perform Stage 1 Analysis on raw campaign data.
    """
    try:
        context = ExecutionContext()
        
        # 1. Prepare raw data as DataFrame for EnrichmentModule
        df = pd.DataFrame([request.campaign_data])
        context.processed_df = df
        
        if request.business_domain:
            context.set_metadata("business_domain", request.business_domain)
        if request.campaign_target:
            context.set_metadata("campaign_target", request.campaign_target)

        # 2. Execute Enrichment
        logger.info("Executing Enrichment via API...")
        context = enrichment_module.run(context)
        
        # 3. Execute Analysis
        logger.info("Executing Analysis via API...")
        context = analysis_module.run(context)
        
        if context.errors:
            raise HTTPException(status_code=500, detail=f"Analysis failed: {context.errors}")
            
        return context.analysis_results
        
    except Exception as e:
        logger.error(f"Error in analysis endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/recommendation")
async def recommend(request: RecommendationRequest):
    """
    Perform Stage 2 Recommendations. 
    If analysis_results are not provided, it automatically runs Stage 1 Analysis first.
    """
    try:
        context = ExecutionContext()
        
        # 1. Prepare raw data as DataFrame for EnrichmentModule
        df = pd.DataFrame([request.campaign_data])
        context.processed_df = df
        
        if request.business_domain:
            context.set_metadata("business_domain", request.business_domain)
        if request.campaign_target:
            context.set_metadata("campaign_target", request.campaign_target)

        # 2. Execute Enrichment
        logger.info("Executing Enrichment via API...")
        context = enrichment_module.run(context)

        # 3. Execute Analysis (if not provided)
        if request.analysis_results:
            logger.info("Using provided analysis results...")
            context.analysis_results = request.analysis_results
        else:
            logger.info("Analysis results not provided. Executing Stage 1 Analysis internally...")
            context = analysis_module.run(context)

        # 4. Execute Recommendations
        logger.info("Executing Stage 2 Recommendations via API...")
        context = recommendation_module.run(context)
        
        if context.errors:
            raise HTTPException(status_code=500, detail=f"Recommendation failed: {context.errors}")
            
        return {
            "analysis_used": context.analysis_results,
            "recommendations": context.recommendation_results
        }
        
    except Exception as e:
        logger.error(f"Error in recommendation endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
