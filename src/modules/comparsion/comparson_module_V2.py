from pathlib import Path
from typing import List
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

from src.modules.comparsion.json_to_csv_writer import JsonToCsvWriter
# Configure logging using shared structure
try:
    from src.shared.utils.logger import setup_logging
    logger = setup_logging(file_name="comparison.log",module_name ='Comparison Module')
    from src.shared.utils.json_saver import save_results_to_json
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class ComparisonModule:
    """
    Comparison Module for Evaluation Results
    This module provides a structured pipeline to compare evaluation scores across
    multiple versions of generated outputs (e.g., LLM analysis and recommendations).
    It supports two evaluation types:
        1. Analysis
        2. Recommendation
    """

    ANALYSIS = "analysis"
    RECOMMENDATION = "recommendation"

    def __init__(self, analysis_or_recommendation_scores_as_csv: str | Path, module_type: str) -> None:
        self.analysis_or_recommendation_scores_as_csv = Path(analysis_or_recommendation_scores_as_csv)
        self.module_type = module_type
        
        logger.info(
            "Initialized ComparisonModule | module_type=%s | file to be compared=%s",
            self.module_type,
            self.analysis_or_recommendation_scores_as_csv,
        )


    def compare_versions(self) -> pd.DataFrame:
        """
        Version-Level Comparison
        - Groups results by version.
        - Computes the average score for each metric per version.
        - Enables direct comparison of model performance across versions.
        - For recommendation data, aggregates multiple cards within each version.
        """
        logger.info("Comparison was started | module_type=%s", self.module_type)
        df = self.load_data()
        summary_df  = self._build_version_summary(df)
        logger.info(
            "Comparison was completed | module_type=%s | rows=%d | columns=%s",
            self.module_type,
            len(summary_df),
            list(summary_df.columns),
        )
        return summary_df 

    def compare_recommendation_cards(self) -> pd.DataFrame:
        """
        Return recommendation card-level comparison.
        Only valid for recommendation module_type.
        """
        logger.info("Card-level comparison was started | module_type=%s", self.module_type)
        df = self.load_data()
        card_df = self._build_card_level_comparison(df)
        logger.info(
            "Completed card-level comparison | module_type=%s | rows=%d",
            self.module_type,
            len(card_df),
        )
        return card_df 
    

    def plot_version_comparison(
        self,
        summary_df: pd.DataFrame,
        output_path: str | Path,
        title: str = "",
        show: bool = True,
    ) -> Path:
        """
        - Generates bar charts comparing metrics across versions.
        - Plots metrics on the x-axis and scores on the y-axis.
        - Each version is represented as a separate bar group.
        - Saves plots to disk and optionally displays them interactively.

        """
        #from pathlib import Path
        #import matplotlib.pyplot as plt

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        metrics = self._get_metrics()
        
        logger.info(
            "Generating comparison plot | module_type=%s | output_path=%s | metrics=%s",
            self.module_type,
            output_path,
            metrics,
        )
        try:
            # Group by metrics, not versions
            plot_df = summary_df.set_index("version")[metrics].T
            logger.debug("Plot DataFrame shape: %s", plot_df.shape)
            logger.debug("Plot DataFrame preview:\n%s", plot_df.head())
            plot_df.plot(kind="bar",figsize=(10, 6))
            
            plt.title(title or f"{self.module_type.capitalize()} Metric Comparison Across Versions")
            plt.xlabel("Metric")
            plt.ylabel("Score")
            plt.xticks(rotation=0)
            plt.legend(title="Version")
            plt.tight_layout()

            plt.savefig(output_path)
            logger.info("Plot saved successfully | path=%s", output_path)

            if show:
                logger.info("Displaying plot interactively")
                plt.show(block=False)
                plt.pause(0.1)

            if not show:
                logger.info("Plot display disabled; closing figure")
                plt.close()

            return output_path
        
        except Exception as exc:
            logger.exception(
                "Failed to generate plot | module_type=%s | output_path=%s",
                self.module_type,
                output_path,
            )



    # Helper methods

    def load_data(self) -> pd.DataFrame:
        """Load comparison CSV into a DataFrame.
        - Reads evaluation results from CSV files.
        - Validates required schema based on module type.
        - Ensures all necessary metric columns are present before processing.
        """
        logger.info("Loading comparison CSV | path=%s", self.analysis_or_recommendation_scores_as_csv)
        
        if not self.analysis_or_recommendation_scores_as_csv.exists():
            logger.error("Analysis/recommendation file not found: %s", self.analysis_or_recommendation_scores_as_csv)
            raise FileNotFoundError(f"Analysis/recommendation file not found: {self.analysis_or_recommendation_scores_as_csv}")

        df = pd.read_csv(self.analysis_or_recommendation_scores_as_csv)
        logger.info(
            "CSV loaded successfully | rows=%d | columns=%s",
            len(df),
            list(df.columns),
        )
        self._validate_columns(df)
        return df
    
    def _build_version_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Build version-level summary.
        For recommendation data, this averages all cards inside each version.
        """
        metrics = self._get_metrics()
        logger.info(
            "Building version summary | module_type=%s | metrics=%s",
            self.module_type,
            metrics,
        )
        
        # Group all rows by version. Compute mean (average) for each metric
        summary_df = (
            df.groupby("version", as_index=False)[metrics]
            .mean(numeric_only=True)
            .sort_values(by="version")
        )
        logger.debug("Version summary preview:\n%s", summary_df.head())
        return summary_df

    def _build_card_level_comparison(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Return card-level rows for recommendation comparisons.
        - Provides comparison across recommendation cards.
        - Preserves individual rows (no aggregation).
        - Useful for inspecting variation between cards within the same version.
        """
        if self.module_type != self.RECOMMENDATION:
            logger.error(
                "Card-level comparison requested for unsupported module_type=%s",
                self.module_type,
            )
            raise ValueError(
                "Card-level comparison is only supported for recommendation module."
            )

        metrics = self._get_metrics()
        logger.info("Building card-level comparison | metrics=%s", metrics)
        result_df = df[["version", "card_title", *metrics]].copy()
        
        logger.debug("Card-level comparison preview:\n%s", result_df.head())
        return result_df.sort_values(by=["card_title", "version"])

    def _get_required_columns(self) -> List[str]:
        """Return required CSV columns based on module type."""
        if self.module_type == self.ANALYSIS:
            required = ["version", "clarity", "accuracy", "structure", "overall"]
            logger.debug("Required columns for analysis: %s", required)
            return required 

        if self.module_type == self.RECOMMENDATION:
            required = [
                "version",
                "card_title",
                "clarity",
                "accuracy",
                "structure",
                "feasibility",
                "overall",
            ]
            logger.debug("Required columns for recommendation: %s", required)
            return required

        logger.error("Unsupported module_type provided: %s", self.module_type)
        raise ValueError(f"Unsupported module_type: {self.module_type}")

    def _get_metrics(self) -> List[str]:
        """Return metric columns only."""
        metrics =[
            column
            for column in self._get_required_columns()
            if column not in {"version", "card_title"}
        ]
        logger.debug("Resolved metric columns: %s", metrics)
        return metrics

    def _validate_columns(self, df: pd.DataFrame) -> None:
        """Ensure the input CSV contains the required columns."""
        missing_cols = [
            col for col in self._get_required_columns() if col not in df.columns
        ]
        if missing_cols:
            logger.error(
                "Missing required columns | module_type=%s | missing=%s | available=%s",
                self.module_type,
                missing_cols,
                list(df.columns),
            )
            raise ValueError(
                f"Missing required columns for '{self.module_type}': {missing_cols}"
            )
        logger.info(
            "CSV schema validation passed | module_type=%s",
            self.module_type,
        )


    
# Pipline execution
def run_pipeline() -> None:
    """
    End-to-End Pipeline Execution
    - Converts JSON evaluation outputs into CSV format.
    - Runs both analysis and recommendation comparisons.
    - Generates summaries and visualizations.
    - Saves outputs (CSV summaries + plots) into a structured directory.
    """
    logger.info("Starting comparison pipeline")
    try:

        PROJECT_ROOT = Path(__file__).resolve().parents[3]   # adjust level if needed

        base_dir = PROJECT_ROOT / "data" / "outputs" / "run_20260414_004119" / "campaign_1"

        analysis_json = base_dir / "analysis_evaluation_results.json"
        recommendation_json = base_dir / "recommendation_evaluation_results.json"

        output_dir = base_dir / "comparison_results"

        analysis_csv = output_dir / "analysis_scores.csv"
        recommendation_csv = output_dir / "recommendation_scores.csv"

        version = "v5"  
        logger.info("Resolved pipeline paths | base_dir=%s | output_dir=%s", base_dir, output_dir)
        logger.info("Using version=%s", version)


        # Step 1: convert JSON to CSV
        logger.info("Step 1: Converting JSON files to CSV")
        print("Converting JSON to CSV...")

        analysis_writer = JsonToCsvWriter(
            input_json=analysis_json,
            output_csv=analysis_csv,
            version=version,
        )
        analysis_writer.write_csv()
        logger.info("Analysis CSV created | path=%s", analysis_csv)

        recommendation_writer = JsonToCsvWriter(
            input_json=recommendation_json,
            output_csv=recommendation_csv,
            version=version,
        )
        recommendation_writer.write_csv()
        logger.info("Recommendation CSV created | path=%s", recommendation_csv)

        print("CSV files created successfully.")

        # Step 2: Analysis Comparison
        print("\nRunning analysis comparison...")
        logger.info("Step 2: Running analysis comparison")

        analysis_comparison = ComparisonModule(
            analysis_or_recommendation_scores_as_csv=analysis_csv,
            module_type=ComparisonModule.ANALYSIS,
        )

        analysis_summary = analysis_comparison.compare_versions()
        logger.info("Analysis summary generated successfully")

        print("\nAnalysis Summary:")
        print(analysis_summary)
        logger.debug("Analysis summary:\n%s", analysis_summary)

        analysis_plot_path = output_dir / "analysis_comparison_plot.png"

        analysis_comparison.plot_version_comparison(
            summary_df=analysis_summary,
            output_path=analysis_plot_path,
            title="Analysis Scores Comparison",
            show=True,   # display + save
        )

        # Step 3: Recommendation Comparison
        print("\nRunning recommendation comparison...")
        logger.info("Step 3: Running recommendation comparison")

        recommendation_comparison = ComparisonModule(
            analysis_or_recommendation_scores_as_csv=recommendation_csv,
            module_type=ComparisonModule.RECOMMENDATION,
        )

        recommendation_summary = recommendation_comparison.compare_versions()
        logger.info("Recommendation version summary generated successfully")
        logger.debug("Recommendation summary:\n%s", recommendation_summary)

        print("\nRecommendation Summary (Version-level):")
        print(recommendation_summary)

        recommendation_plot_path = output_dir / "recommendation_comparison_plot.png"

        recommendation_comparison.plot_version_comparison(
            summary_df=recommendation_summary,
            output_path=recommendation_plot_path,
            title="Recommendation Scores Comparison",
            show=True,
        )
        # Optional: card-level comparison
        logger.info("Step 4: Running recommendation card-level comparison")
        card_level = recommendation_comparison.compare_recommendation_cards()
        logger.debug("Recommendation card-level comparison:\n%s", card_level)
        print("\nRecommendation Card-Level Comparison:")
        print(card_level)

        # Optional: Save summaries
        logger.info("Step 5: Saving summary CSV files")
        analysis_summary.to_csv(output_dir / "analysis_summary.csv", index=False)
        recommendation_summary.to_csv(output_dir / "recommendation_summary.csv", index=False)
        card_level.to_csv(output_dir / "recommendation_card_level.csv", index=False)

        print("\nAll outputs saved successfully.")
        logger.info(
            "All output files saved successfully | analysis_summary=%s | recommendation_summary=%s | card_level=%s"
        )

        plt.show()
        logger.info("Comparison pipeline finished successfully")

    except Exception:
        logger.exception("Comparison pipeline failed")
        raise

# Entry Point
if __name__ == "__main__":
    run_pipeline()    