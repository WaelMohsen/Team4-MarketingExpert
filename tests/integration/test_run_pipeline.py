import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from run_pipeline import main
from src.modules.ingestion.ingestion_module import IngestionModule
from src.modules.preprocessing.preprocessing_module import PreprocessingModule
from src.modules.enrichment.enrichment_module import EnrichmentModule
from src.modules.analysis.analysis_module import AnalysisModule
from src.modules.recommendation.recommendation_module import RecommendationModule
from src.modules.evaluation.evaluation_module import EvaluationModule

@pytest.mark.integration
def test_MainPipelineFlow_ShouldExecuteAllModules_WhenValidArgsProvided():
    """Verify that the main pipeline flow executes correctly with mocked module operations."""
    # Arrange
    # Mock arguments
    mock_args = MagicMock()
    mock_args.input_csv = "data/test.csv"
    mock_args.output_base_dir = "data/outputs/"
    mock_args.row_limit = 1
    mock_args.batch_size = 6
    mock_args.skip_evaluation = False
    mock_args.batch_size = 6
    
    # Preprocessed DF mock
    mock_processed_df = pd.DataFrame({
        "platform": ["Google"],
        "campaign_name": ["C1"],
        "date": ["2024-01-01"],
        "spend": [100]
    })
    
    with patch("run_pipeline.parse_args", return_value=mock_args):
        with patch("os.makedirs"):
            # Patch only the run and save methods of the actual modules to preserve Runnable inheritance
            with patch.object(IngestionModule, "run") as mock_ingest_run, \
                 patch.object(IngestionModule, "save"), \
                 patch.object(PreprocessingModule, "run") as mock_prep_run, \
                 patch.object(PreprocessingModule, "save"), \
                 patch.object(EnrichmentModule, "run") as mock_enrich_run, \
                 patch.object(EnrichmentModule, "save"), \
                 patch.object(AnalysisModule, "run") as mock_anal_run, \
                 patch.object(AnalysisModule, "save"), \
                 patch.object(RecommendationModule, "run") as mock_rec_run, \
                 patch.object(RecommendationModule, "save"), \
                 patch.object(EvaluationModule, "run") as mock_eval_run, \
                 patch.object(EvaluationModule, "save"):
                
                # Mock run implementations to return context and propagate data correctly
                def side_effect_ingest(ctx):
                    ctx.raw_df = mock_processed_df
                    return ctx
                    
                def side_effect_prep(ctx):
                    ctx.processed_df = mock_processed_df
                    return ctx

                mock_ingest_run.side_effect = side_effect_ingest
                mock_prep_run.side_effect = side_effect_prep
                mock_enrich_run.side_effect = lambda ctx: ctx
                mock_anal_run.side_effect = lambda ctx: ctx
                mock_rec_run.side_effect = lambda ctx: ctx
                mock_eval_run.side_effect = lambda ctx: ctx
                
                # Act
                # Execute main
                main()
                
                # Assert
                # Verify that each module's run was executed
                assert mock_ingest_run.called
                assert mock_prep_run.called
                assert mock_enrich_run.called
                assert mock_anal_run.called
                assert mock_rec_run.called
                assert mock_eval_run.called
                
                # Verify call counts (1 call for 1 row batch slice)
                assert mock_enrich_run.call_count == 1
