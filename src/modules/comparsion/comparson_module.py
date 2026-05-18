from pathlib import Path
from typing import Any, List
import json

import pandas as pd
import matplotlib.pyplot as plt


# Configure logging using shared structure
try:
    from src.shared.utils.logger import setup_logging
    logger = setup_logging(module_name="Comparison Module")
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class ComparisonModule:
    ANALYSIS = "analysis"
    RECOMMENDATION = "recommendation"

    def __init__(self, data: pd.DataFrame, module_type: str) -> None:
        self.data = data.copy()
        self.module_type = module_type

        logger.info(
            "Initialized ComparisonModule | module_type=%s | rows=%d",
            self.module_type,
            len(self.data),
        )

        self._validate_columns(self.data)

    def get_version_summary(self) -> pd.DataFrame:
        logger.info("Version summary started | module_type=%s", self.module_type)
        return self._build_version_summary(self.data)

    def plot_version_comparison(
        self,
        version_summary: pd.DataFrame,
        output_path: str | Path,
        title: str = "",
        show: bool = False,
    ) -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        metrics = self._get_metrics()

        plot_df = version_summary.set_index("version")[metrics].T

        ax = plot_df.plot(kind="bar", figsize=(10, 6))
        ax.set_title(title or f"{self.module_type.capitalize()} Metric Comparison Across Versions")
        ax.set_xlabel("Metric")
        ax.set_ylabel("Score")
        ax.tick_params(axis="x", rotation=0)
        ax.legend(title="Version")

        plt.tight_layout()
        plt.savefig(output_path)

        if show:
            plt.show()
        else:
            plt.close()

        logger.info("Plot saved successfully | path=%s", output_path)
        return output_path

    def _build_version_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        metrics = self._get_metrics()

        return (
            df.groupby("version", as_index=False)[metrics]
            .mean(numeric_only=True)
            .sort_values(by="version")
        )

    def _get_required_columns(self) -> List[str]:
        if self.module_type == self.ANALYSIS:
            return [
                "version",
                "clarity",
                "accuracy",
                "hallucination",
                "structure",
                "kpi_alignment",
                "overall",
            ]

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

        raise ValueError(f"Unsupported module_type: {self.module_type}")

    def _get_metrics(self) -> List[str]:
        return [
            column
            for column in self._get_required_columns()
            if column not in {"version", "card_title"}
        ]

    def _validate_columns(self, df: pd.DataFrame) -> None:
        missing_cols = [
            col for col in self._get_required_columns() if col not in df.columns
        ]

        if missing_cols:
            raise ValueError(
                f"Missing required columns for '{self.module_type}': {missing_cols}. "
                f"Available columns: {list(df.columns)}"
            )


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def get_outputs_dir() -> Path:
    return get_project_root() / "data" / "outputs"


def find_campaign_dirs(outputs_dir: Path) -> List[Path]:
    return sorted(
        path for path in outputs_dir.iterdir()
        if path.is_dir() and path.name.startswith("campaign_")
    )


def find_run_result_dirs(campaign_dir: Path) -> List[Path]:
    return sorted(
        run_dir / "results"
        for run_dir in campaign_dir.iterdir()
        if run_dir.is_dir()
        and run_dir.name.startswith("run_")
        and (run_dir / "results").exists()
    )


def find_last_n_run_result_dirs(
    campaign_dir: Path,
    last_n: int | None = None,
) -> List[Path]:
    result_dirs = find_run_result_dirs(campaign_dir)

    if last_n is None:
        return result_dirs

    if last_n <= 0:
        raise ValueError(f"last_n must be a positive integer or None, got: {last_n}")

    return result_dirs[-last_n:]


def _extract_records(payload: Any) -> list[dict[str, Any]]:
    """
    Convert common JSON shapes into tabular records.

    Supports:
    - list[dict]
    - dict containing a list[dict]
    - single dict of scalar metrics
    """
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    if isinstance(payload, dict):
        for value in payload.values():
            if isinstance(value, list) and all(isinstance(item, dict) for item in value):
                return value

        return [payload]

    raise ValueError(f"Unsupported JSON structure: {type(payload)}")


def load_evaluation_json_as_df(json_path: Path, version: str) -> pd.DataFrame:
    with json_path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    records = _extract_records(payload)
    df = pd.json_normalize(records)
    df.insert(0, "version", version)

    return df


def build_campaign_dataframes(
    campaign_dir: Path,
    last_n: int | None = None,
) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    result_dirs = find_last_n_run_result_dirs(campaign_dir, last_n=last_n)

    if not result_dirs:
        raise FileNotFoundError(f"No run results found under: {campaign_dir}")

    analysis_frames: list[pd.DataFrame] = []
    recommendation_frames: list[pd.DataFrame] = []

    logger.info(
        "Building campaign DataFrames in memory | campaign=%s | selected_runs=%s",
        campaign_dir.name,
        [result_dir.parent.name for result_dir in result_dirs],
    )

    for results_dir in result_dirs:
        run_dir = results_dir.parent
        version = run_dir.name

        analysis_json = results_dir / "analysis_evaluation_results.json"
        recommendation_json = results_dir / "recommendation_evaluation_results.json"

        if analysis_json.exists():
            analysis_frames.append(load_evaluation_json_as_df(analysis_json, version))
            logger.info("Loaded analysis result | version=%s | file=%s", version, analysis_json)
        else:
            logger.warning("Missing analysis file: %s", analysis_json)

        if recommendation_json.exists():
            recommendation_frames.append(load_evaluation_json_as_df(recommendation_json, version))
            logger.info("Loaded recommendation result | version=%s | file=%s", version, recommendation_json)
        else:
            logger.warning("Missing recommendation file: %s", recommendation_json)

    analysis_df = (
        pd.concat(analysis_frames, ignore_index=True)
        if analysis_frames
        else None
    )

    recommendation_df = (
        pd.concat(recommendation_frames, ignore_index=True)
        if recommendation_frames
        else None
    )

    return analysis_df, recommendation_df


def run_analysis_comparison(
    analysis_df: pd.DataFrame | None,
    comparison_dir: Path,
) -> None:
    if analysis_df is None or analysis_df.empty:
        logger.warning("No analysis data found")
        return

    analysis_comparison = ComparisonModule(
        data=analysis_df,
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


def run_recommendation_comparison(
    recommendation_df: pd.DataFrame | None,
    comparison_dir: Path,
) -> None:
    if recommendation_df is None or recommendation_df.empty:
        logger.warning("No recommendation data found")
        return

    recommendation_comparison = ComparisonModule(
        data=recommendation_df,
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


def run_pipeline(last_n: int | None = None) -> None:
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

            analysis_df, recommendation_df = build_campaign_dataframes(
                campaign_dir=campaign_dir,
                last_n=last_n,
            )

            run_analysis_comparison(
                analysis_df=analysis_df,
                comparison_dir=comparison_dir,
            )

            run_recommendation_comparison(
                recommendation_df=recommendation_df,
                comparison_dir=comparison_dir,
            )

            print(f"Finished {campaign_dir.name}. Results saved in {comparison_dir}")

        print("\nAll campaign comparisons completed successfully.")
        logger.info("Multi-campaign comparison pipeline finished successfully")

    except Exception:
        logger.exception("Comparison pipeline failed")
        raise


if __name__ == "__main__":
    run_pipeline(last_n=2)