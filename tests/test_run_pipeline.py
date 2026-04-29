import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from run_pipeline import main

def test_run_pipeline_main_flow():
    """Verify that the main pipeline flow executes correctly with mocked modules."""
    
    # Mock arguments
    mock_args = MagicMock()
    mock_args.input_csv = "data/test.csv"
    mock_args.output_base_dir = "data/outputs/"
    mock_args.row_limit = 1
    mock_args.skip_evaluation = False
    
    # Preprocessed DF mock
    mock_processed_df = pd.DataFrame({
        "platform": ["Google"],
        "campaign_name": ["C1"],
        "date": ["2024-01-01"],
        "spend": [100]
    })
    
    with patch("run_pipeline.parse_args", return_value=mock_args):
        with patch("os.makedirs"):
            with patch("run_pipeline.PipelineEngine") as MockEngine:
                mock_engine_instance = MockEngine.return_value
                # Mock preparation run
                mock_prep_context = MagicMock()
                mock_prep_context.errors = []
                mock_prep_context.processed_df = mock_processed_df
                mock_engine_instance.run.return_value = mock_prep_context
                
                # Mock granular modules
                with patch("run_pipeline.IngestionModule"), \
                     patch("run_pipeline.PreprocessingModule"), \
                     patch("run_pipeline.EnrichmentModule") as MockEnrich, \
                     patch("run_pipeline.AnalysisModule") as MockAnal, \
                     patch("run_pipeline.RecommendationModule") as MockRec, \
                     patch("run_pipeline.EvaluationModule") as MockEval:
                    
                    # Each module's run should return the context it received
                    MockEnrich.return_value.run.side_effect = lambda ctx: ctx
                    MockAnal.return_value.run.side_effect = lambda ctx: ctx
                    MockRec.return_value.run.side_effect = lambda ctx: ctx
                    MockEval.return_value.run.side_effect = lambda ctx: ctx
                    
                    # Execute main
                    main()
                    
                    # Verify that modules were initialized and run
                    assert MockEnrich.called
                    assert MockAnal.called
                    assert MockRec.called
                    assert MockEval.called
                    
                    # Verify that iteration happened for the dataframe
                    # In this case, 1 row because of row_limit
                    assert MockEnrich.return_value.run.call_count == 1
