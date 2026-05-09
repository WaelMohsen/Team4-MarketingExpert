from pathlib import Path
from typing import List
import pandas as pd
import matplotlib.pyplot as plt

from src.modules.comparsion.json_to_csv_writer import JsonToCsvWriter

# Configure logging using shared structure
try:
    from src.shared.utils.logger import setup_logging
    logger = setup_logging(module_name="Comparison Module")
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class ComparisonModule:
    """
    Version-based Evaluation Comparison Module.

    This module performs metric aggregation and comparison across multiple
    run versions for a given campaign.

    It operates on pre-built CSV inputs (generated from multiple run folders)
    and produces:
        - Version-level summary tables (mean scores per metric)
        - Comparison visualizations (bar charts)

    Supported module types:
        - "analysis": compares analysis evaluation metrics
        - "recommendation": compares recommendation evaluation metrics
          (aggregated across multiple recommendation cards per version)

    Typical workflow:
        1. Load combined CSV (aggregated from multiple runs)
        2. Validate schema based on module type
        3. Group results by version
        4. Compute mean score per metric
        5. Generate comparison plots
    """

    ANALYSIS = "analysis"
    RECOMMENDATION = "recommendation"

    def __init__(self, input_csv: str | Path, module_type: str) -> None:
        self.input_csv = Path(input_csv)
        self.module_type = module_type

        logger.info(
            "Initialized ComparisonModule | module_type=%s | input_csv=%s",
            self.module_type,
            self.input_csv,
        )

    def get_version_summary(self) -> pd.DataFrame:
        """
        Compute a version-level summary table.

        This method:
            - Loads the input CSV containing multiple runs
            - Validates required columns based on module type
            - Groups rows by version
            - Computes the average score for each metric

        Notes:
            - For recommendation data, multiple rows (cards) per version
              are averaged into a single version-level score.
            - Output is sorted by version for consistent comparison.

        Returns:
            pd.DataFrame: Aggregated metrics per version.
        """
        logger.info("Version summary started | module_type=%s", self.module_type)

        df = self.load_data()
        version_summary = self._build_version_summary(df)

        logger.info(
            "Version summary completed | module_type=%s | rows=%d | columns=%s",
            self.module_type,
            len(version_summary),
            list(version_summary.columns),
        )
        return version_summary

    def plot_version_comparison(
        self,
        version_summary: pd.DataFrame,
        output_path: str | Path,
        title: str = "",
        show: bool = False,
    ) -> Path:
        """
        Generate a bar chart comparing metrics across versions.

        Visualization structure:
            - X-axis: evaluation metrics (e.g., clarity, accuracy, etc.)
            - Y-axis: average scores
            - Each version is represented as a separate bar group

        Behavior:
            - Saves the plot to the specified output path
            - Optionally displays the plot (useful for debugging/local runs)

        Args:
            version_summary: Output from get_version_summary()
            output_path: Destination path for the saved plot
            title: Optional custom title (auto-generated if not provided)
            show: Whether to display the plot interactively

        Returns:
            Path: Path to the saved plot file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        metrics = self._get_metrics()

        logger.info(
            "Generating version comparison plot | module_type=%s | output_path=%s | metrics=%s",
            self.module_type,
            output_path,
            metrics,
        )

        try:
            plot_df = version_summary.set_index("version")[metrics].T

            logger.debug("Plot DataFrame shape: %s", plot_df.shape)
            logger.debug("Plot DataFrame preview:\n%s", plot_df.head())

            ax = plot_df.plot(kind="bar", figsize=(10, 6))
            ax.set_title(title or f"{self.module_type.capitalize()} Metric Comparison Across Versions")
            ax.set_xlabel("Metric")
            ax.set_ylabel("Score")
            ax.tick_params(axis="x", rotation=0)
            ax.legend(title="Version")

            plt.tight_layout()
            plt.savefig(output_path)
            logger.info("Plot saved successfully | path=%s", output_path)

            if show:
                plt.show()
            else:
                plt.close()

            return output_path

        except Exception:
            logger.exception(
                "Failed to generate plot | module_type=%s | output_path=%s",
                self.module_type,
                output_path,
            )
            raise

    def load_data(self) -> pd.DataFrame:
        """
        Load comparison CSV into a DataFrame and validate required columns.

        Returns:
            pd.DataFrame: Validated comparison data loaded from CSV.

        Raises:
            FileNotFoundError: If the input CSV does not exist.
            ValueError: If required columns are missing.
        """
        logger.info("Loading comparison CSV | path=%s", self.input_csv)

        if not self.input_csv.exists():
            logger.error("Input file not found: %s", self.input_csv)
            raise FileNotFoundError(f"Input file not found: {self.input_csv}")

        df = pd.read_csv(self.input_csv)

        logger.info(
            "CSV loaded successfully | rows=%d | columns=%s",
            len(df),
            list(df.columns),
        )

        self._validate_columns(df)
        return df

    def _build_version_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Build a version-level summary DataFrame.

        For each version, this method computes the mean score of all
        metric columns relevant to the selected module type.

        Args:
            df: Input DataFrame containing comparison rows.

        Returns:
            pd.DataFrame: One aggregated row per version, sorted by version.
        """
        metrics = self._get_metrics()

        logger.info(
            "Building version summary | module_type=%s | metrics=%s",
            self.module_type,
            metrics,
        )

        version_summary = (
            df.groupby("version", as_index=False)[metrics]
            .mean(numeric_only=True)
            .sort_values(by="version")
        )

        logger.debug("Version summary preview:\n%s", version_summary.head())
        return version_summary

    def _get_required_columns(self) -> List[str]:
        """
        Return required CSV columns based on module type.

        Returns:
            List[str]: Required schema for the selected module type.

        Raises:
            ValueError: If module_type is not supported.
        """
        if self.module_type == self.ANALYSIS:
            return ["version", "clarity", "accuracy", "structure", "overall"]

        if self.module_type == self.RECOMMENDATION:
            return [
                "version",
                "Structure",
                "Feasibility",
                "Recommendation_Count",
                "Analysis_Grounding",
                "Action_Step_Completeness",
                "Priority_Alignment",
                "Tone_Audience_Compliance",
                "Expected_Impact_Quality",
                "Overall",
            ]

        logger.error("Unsupported module_type provided: %s", self.module_type)
        raise ValueError(f"Unsupported module_type: {self.module_type}")

    def _get_metrics(self) -> List[str]:
        """
        Return metric columns only, excluding identifier columns.

        Returns:
            List[str]: Metric column names used for aggregation and plotting.
        """
        return [
            column
            for column in self._get_required_columns()
            if column not in {"version", "card_title"}
        ]

    def _validate_columns(self, df: pd.DataFrame) -> None:
        """
        Ensure the input CSV contains all required columns.

        Args:
            df: DataFrame to validate.

        Raises:
            ValueError: If one or more required columns are missing.
        """
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

        logger.info("CSV schema validation passed | module_type=%s", self.module_type)


def get_project_root() -> Path:
    """
    Resolve the project root directory from the current file location.

    Returns:
        Path: Project root path.
    """
    return Path(__file__).resolve().parents[3]


def get_outputs_dir() -> Path:
    """
    Return the main outputs directory.

    Returns:
        Path: Path to data/outputs.
    """
    return get_project_root() / "data" / "outputs"


def find_campaign_dirs(outputs_dir: Path) -> List[Path]:
    """
    Return all campaign directories under the outputs folder.

    A valid campaign directory is any folder whose name starts with
    'campaign_'.

    Args:
        outputs_dir: Root outputs directory.

    Returns:
        List[Path]: Sorted list of campaign directories.
    """
    return sorted(
        path for path in outputs_dir.iterdir()
        if path.is_dir() and path.name.startswith("campaign_")
    )


def find_run_result_dirs(campaign_dir: Path) -> List[Path]:
    """
    Return all run results directories for a campaign.

    This function scans a campaign directory, finds all folders named
    'run_*', and returns their nested 'results' directories.

    Args:
        campaign_dir: Campaign directory path.

    Returns:
        List[Path]: Sorted results directories from oldest to newest.
    """
    return sorted(
        run_dir / "results"
        for run_dir in campaign_dir.iterdir()
        if run_dir.is_dir()
        and run_dir.name.startswith("run_")
        and (run_dir / "results").exists()
    )


def find_last_n_run_result_dirs(campaign_dir: Path, last_n: int | None = None) -> List[Path]:
    """
    Retrieve result directories for the most recent runs in a campaign.

    This function enables flexible comparison scope:
        - All runs (full historical comparison)
        - Last N runs (focused comparison on recent experiments)

    Args:
        campaign_dir: Path to a campaign directory (e.g., data/outputs/campaign_1)
        last_n:
            - None → return all available runs
            - Positive integer → return only the most recent N runs

    Returns:
        List[Path]: Sorted list of result directories (oldest → newest)

    Raises:
        ValueError: If last_n is not positive
    """
    result_dirs = find_run_result_dirs(campaign_dir)

    if last_n is None:
        return result_dirs

    if last_n <= 0:
        raise ValueError(f"last_n must be a positive integer or None, got: {last_n}")

    return result_dirs[-last_n:]


def delete_file_if_exists(file_path: Path) -> None:
    """
    Delete a file if it exists.

    Args:
        file_path: Path of the file to remove.
    """
    if file_path.exists():
        file_path.unlink()
        logger.info("Deleted file | path=%s", file_path)


def build_campaign_temp_csvs(
    campaign_dir: Path,
    comparison_dir: Path,
    last_n: int | None = None,
) -> tuple[Path, Path]:
    """
    Construct temporary CSV inputs by aggregating evaluation JSON files
    across selected run folders within a campaign.

    Workflow:
        1. Select runs using last_n logic
        2. Extract evaluation JSONs from each run
        3. Convert JSON → CSV using JsonToCsvWriter
        4. Append results into unified temporary CSV files

    Outputs:
        - One temporary CSV for analysis results
        - One temporary CSV for recommendation results

    Notes:
        - These files are intermediate artifacts
        - They are deleted after final summaries and plots are generated

    Args:
        campaign_dir: Campaign directory containing run folders
        comparison_dir: Directory to store temporary and final outputs
        last_n: Controls how many recent runs are included

    Returns:
        tuple[Path, Path]:
            (analysis_temp_csv, recommendation_temp_csv)

    Raises:
        FileNotFoundError: If no valid run results are found
    """
    result_dirs = find_last_n_run_result_dirs(campaign_dir, last_n=last_n)

    if not result_dirs:
        raise FileNotFoundError(f"No run results found under: {campaign_dir}")

    analysis_temp_csv = comparison_dir / "_temp_analysis_summary_input.csv"
    recommendation_temp_csv = comparison_dir / "_temp_recommendation_summary_input.csv"

    delete_file_if_exists(analysis_temp_csv)
    delete_file_if_exists(recommendation_temp_csv)

    logger.info(
        "Building temporary campaign CSVs | campaign=%s | selected_runs=%s",
        campaign_dir.name,
        [result_dir.parent.name for result_dir in result_dirs],
    )

    for results_dir in result_dirs:
        run_dir = results_dir.parent
        version = run_dir.name

        analysis_json = results_dir / "analysis_evaluation_results.json"
        recommendation_json = results_dir / "recommendation_evaluation_results.json"

        if analysis_json.exists():
            analysis_writer = JsonToCsvWriter(
                input_json=analysis_json,
                output_csv=analysis_temp_csv,
                version=version,
            )
            analysis_writer.write_csv()
            logger.info("Added analysis result | version=%s | file=%s", version, analysis_json)
        else:
            logger.warning("Missing analysis file: %s", analysis_json)

        if recommendation_json.exists():
            recommendation_writer = JsonToCsvWriter(
                input_json=recommendation_json,
                output_csv=recommendation_temp_csv,
                version=version,
            )
            recommendation_writer.write_csv()
            logger.info("Added recommendation result | version=%s | file=%s", version, recommendation_json)
        else:
            logger.warning("Missing recommendation file: %s", recommendation_json)

    return analysis_temp_csv, recommendation_temp_csv


def run_analysis_comparison(analysis_input_csv: Path, comparison_dir: Path) -> None:
    """
    Generate the final analysis summary CSV and comparison plot.

    This function reads the temporary analysis CSV, aggregates metrics by
    version, saves the final summary CSV, generates a plot, and removes
    the intermediate input file.

    Args:
        analysis_input_csv: Temporary CSV built from analysis evaluation JSON files.
        comparison_dir: Output directory for final comparison results.
    """
    if not analysis_input_csv.exists():
        logger.warning("Analysis input CSV not found: %s", analysis_input_csv)
        return

    analysis_comparison = ComparisonModule(
        input_csv=analysis_input_csv,
        module_type=ComparisonModule.ANALYSIS,
    )

    analysis_summary = analysis_comparison.get_version_summary()
    analysis_summary.to_csv(comparison_dir / "analysis_summary.csv", index=False)

    analysis_comparison.plot_version_comparison(
        version_summary=analysis_summary,
        output_path=comparison_dir / "analysis_comparison_plot.png",
        title="Analysis Scores Comparison Across Runs",
        show=False,
    )

    delete_file_if_exists(analysis_input_csv)


def run_recommendation_comparison(recommendation_input_csv: Path, comparison_dir: Path) -> None:
    """
    Generate the final recommendation summary CSV and comparison plot.

    This function reads the temporary recommendation CSV, aggregates metrics
    by version, saves the final summary CSV, generates a plot, and removes
    the intermediate input file.

    Args:
        recommendation_input_csv: Temporary CSV built from recommendation evaluation JSON files.
        comparison_dir: Output directory for final comparison results.
    """
    if not recommendation_input_csv.exists():
        logger.warning("Recommendation input CSV not found: %s", recommendation_input_csv)
        return

    recommendation_comparison = ComparisonModule(
        input_csv=recommendation_input_csv,
        module_type=ComparisonModule.RECOMMENDATION,
    )

    recommendation_summary = recommendation_comparison.get_version_summary()
    recommendation_summary.to_csv(
        comparison_dir / "recommendation_summary.csv",
        index=False,
    )

    recommendation_comparison.plot_version_comparison(
        version_summary=recommendation_summary,
        output_path=comparison_dir / "recommendation_comparison_plot.png",
        title="Recommendation Scores Comparison Across Runs",
        show=False,
    )

    delete_file_if_exists(recommendation_input_csv)


def run_pipeline(last_n: int | None = None) -> None:
    """
    Execute the full multi-campaign comparison pipeline.

    This pipeline:
        - Iterates over all campaign directories
        - Selects runs (all or last N)
        - Builds temporary CSV datasets from JSON evaluation outputs
        - Computes version-level summaries
        - Generates comparison plots
        - Cleans up intermediate files

    Processing hierarchy:
        data/outputs/
            ├── campaign_1/
            │     ├── run_*/
            │     └── comparison_results/
            ├── campaign_2/
            ...

    Args:
        last_n:
            - None → include all runs in each campaign
            - Positive integer → include only the most recent N runs

    Output per campaign:
        - analysis_summary.csv
        - recommendation_summary.csv
        - analysis_comparison_plot.png
        - recommendation_comparison_plot.png

    Raises:
        FileNotFoundError: If expected directories or data are missing
        Exception: For any pipeline execution failure
    """
    logger.info("Starting multi-campaign comparison pipeline | last_n=%s", last_n)

    try:
        outputs_dir = get_outputs_dir()

        if not outputs_dir.exists():
            raise FileNotFoundError(f"Outputs directory not found: {outputs_dir}")

        campaign_dirs = find_campaign_dirs(outputs_dir)

        if not campaign_dirs:
            raise FileNotFoundError(f"No campaign directories found under: {outputs_dir}")

        for campaign_dir in campaign_dirs:
            print(f"\nProcessing {campaign_dir.name}...")
            logger.info("Processing campaign: %s", campaign_dir)

            comparison_dir = campaign_dir / "comparison_results"
            comparison_dir.mkdir(parents=True, exist_ok=True)

            analysis_temp_csv, recommendation_temp_csv = build_campaign_temp_csvs(
                campaign_dir=campaign_dir,
                comparison_dir=comparison_dir,
                last_n=last_n,
            )

            run_analysis_comparison(
                analysis_input_csv=analysis_temp_csv,
                comparison_dir=comparison_dir,
            )

            run_recommendation_comparison(
                recommendation_input_csv=recommendation_temp_csv,
                comparison_dir=comparison_dir,
            )

            print(f"Finished {campaign_dir.name}. Results saved in {comparison_dir}")

        print("\nAll campaign comparisons completed successfully.")
        logger.info("Multi-campaign comparison pipeline finished successfully")

    except Exception:
        logger.exception("Comparison pipeline failed")
        raise


if __name__ == "__main__":
    # Compare the last 2 runs:
    # run_pipeline(last_n=2)
    # Compare all runs:
    run_pipeline(last_n=2)