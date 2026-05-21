import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from run_pipeline import main

@pytest.mark.integration
def test_MainPipelineFlow_ShouldExecuteAllModules_WhenValidArgsProvided():
    """Verify that the main pipeline flow executes correctly with mocked modules."""
    # Arrange
    # Mock arguments
    mock_args = MagicMock()
    mock_args.input_csv = "data/test.csv"
    mock_args.output_base_dir = "data/outputs/"
    mock_args.row_limit = 1
    mock_args.batch_size = 6
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
                    
                    # Act
                    # Execute main
                    main()
                    
                    # Assert
                    # Verify that modules were initialized and run
                    assert MockEnrich.called
                    assert MockAnal.called
                    assert MockRec.called
                    assert MockEval.called
                    
                    # Verify that iteration happened for the dataframe
                    # In this case, 1 row because of row_limit
                    assert MockEnrich.return_value.run.call_count == 1


@pytest.mark.integration
def test_MainPipelineFlow_ShouldGroupByIndexColumn_WhenIndexColumnIsPresent():
    """Verify that when an index column is present, the pipeline groups rows by it."""
    # Arrange
    mock_args = MagicMock()
    mock_args.input_csv = "data/test.csv"
    mock_args.output_base_dir = "data/outputs/"
    mock_args.row_limit = None
    mock_args.batch_size = 6
    mock_args.skip_evaluation = False
    
    # 4 rows: 2 for index 1, 2 for index 2
    mock_processed_df = pd.DataFrame({
        "index": [1, 1, 2, 2],
        "platform": ["Google", "TikTok", "Meta", "Google"],
        "campaign_name": ["C1", "C1", "C2", "C2"],
        "date": ["2024-01-01", "2024-01-02", "2024-01-01", "2024-01-02"],
        "spend": [100, 150, 200, 250],
        "primary_goal": ["Traffic", "Traffic", "Sales", "Sales"],
        "industry": ["Fintech", "Fintech", "SaaS", "SaaS"],
        "offering": ["O1", "O1", "O2", "O2"],
        "audience": ["A1", "A1", "A2", "A2"],
        "funnel_stage": ["consideration", "consideration", "conversion", "conversion"]
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
                    
                    # Act
                    main()
                    
                    # Assert
                    # Verify that modules were run per group (total 2 campaigns: index 1 and index 2)
                    assert MockEnrich.called
                    assert MockAnal.called
                    assert MockRec.called
                    assert MockEval.called
                    
                    # Verify call count is 2 (one for campaign_1, one for campaign_2)
                    assert MockEnrich.return_value.run.call_count == 2
