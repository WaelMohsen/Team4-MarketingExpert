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
    Comparison Module for Evaluation Results.

    This module compares evaluation scores across multiple run versions
    of generated outputs such as analysis and recommendation results.

    Supported module types:
        1. analysis
        2. recommendation

    Final outputs per campaign:
        - analysis_summary.csv
        - recommendation_summary.csv
        - analysis_comparison_plot.png
        - recommendation_comparison_plot.png
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
        Return one version-level comparison table.

        - Loads the CSV
        - Validates the schema
        - Groups by version
        - Computes average score for each metric

        For recommendation data, this averages all cards within each version.
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
        Plot version-level metric comparison as a bar chart.

        - x-axis: metrics
        - y-axis: scores
        - each version appears as a separate bar group
        - saves plot to disk
        - optionally displays the plot
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
        Build a single version-level summary DataFrame.

        For each version, compute the mean of all metric columns.
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
        """
        if self.module_type == self.ANALYSIS:
            return ["version", "clarity", "accuracy", "structure", "overall"]

        if self.module_type == self.RECOMMENDATION:
            return [
                "version",
                "card_title",
                "clarity",
                "accuracy",
                "structure",
                "feasibility",
                "overall",
            ]

        logger.error("Unsupported module_type provided: %s", self.module_type)
        raise ValueError(f"Unsupported module_type: {self.module_type}")

    def _get_metrics(self) -> List[str]:
        """
        Return only metric columns, excluding identifiers.
        """
        return [
            column
            for column in self._get_required_columns()
            if column not in {"version", "card_title"}
        ]

    def _validate_columns(self, df: pd.DataFrame) -> None:
        """
        Ensure the input CSV contains all required columns.
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
    Resolve project root from current file path.
    """
    return Path(__file__).resolve().parents[3]


def get_outputs_dir() -> Path:
    """
    Return data/outputs directory.
    """
    return get_project_root() / "data" / "outputs"


def find_campaign_dirs(outputs_dir: Path) -> List[Path]:
    """
    Return all campaign_* directories.
    """
    return sorted(
        path for path in outputs_dir.iterdir()
        if path.is_dir() and path.name.startswith("campaign_")
    )


def find_run_result_dirs(campaign_dir: Path) -> List[Path]:
    """
    Return all run_*/results directories sorted from oldest to newest.
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
    Return the most recent run_*/results directories for one campaign.

    Args:
        campaign_dir: path like data/outputs/campaign_1
        last_n:
            - None -> return all runs
            - positive integer -> return only the last n runs

    Returns:
        A list of result directories sorted from oldest to newest.
        If last_n is given, only the most recent n runs are returned.
    """
    result_dirs = find_run_result_dirs(campaign_dir)

    if last_n is None:
        return result_dirs

    if last_n <= 0:
        raise ValueError(f"last_n must be a positive integer or None, got: {last_n}")

    return result_dirs[-last_n:]


def delete_file_if_exists(file_path: Path) -> None:
    """
    Delete file if it exists.
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
    Build temporary CSV files from the selected run folders inside one campaign.

    These CSV files are intermediate inputs only and will be deleted after
    summary CSVs and plots are created.
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
    Generate analysis summary CSV and plot, then delete temp input CSV.
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
    Generate recommendation summary CSV and plot, then delete temp input CSV.
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
    Run comparison across all campaigns.

    Args:
        last_n:
            - None -> compare all runs in each campaign
            - positive integer -> compare only the last n runs in each campaign
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
    # To define the number of last runs to be compared, use last_n 
    #run_pipeline(last_n=2)
    # To compare all the run, use last_n = None or run_pipeline()
    run_pipeline(last_n=None)
    
