from pathlib import Path
from typing import List
import pandas as pd
import matplotlib.pyplot as plt


from src.modules.comparsion.json_to_csv_writer import JsonToCsvWriter

class ComparisonModule:
    """
    Compares evaluation results across versions.

    Supports:
    - analysis comparison
    - recommendation comparison
    """

    ANALYSIS = "analysis"
    RECOMMENDATION = "recommendation"

    def __init__(self, comparison_csv: str | Path, module_type: str) -> None:
        self.comparison_csv = Path(comparison_csv)
        self.module_type = module_type

    def load_data(self) -> pd.DataFrame:
        """Load comparison CSV into a DataFrame."""
        if not self.comparison_csv.exists():
            raise FileNotFoundError(f"Comparison file not found: {self.comparison_csv}")

        df = pd.read_csv(self.comparison_csv)
        self._validate_columns(df)
        return df

    def compare_versions(self) -> pd.DataFrame:
        """
        Return version-level comparison summary.

        - analysis: one row per version
        - recommendation: average across all cards per version
        """
        df = self.load_data()
        return self._build_version_summary(df)

    def compare_recommendation_cards(self) -> pd.DataFrame:
        """
        Return recommendation card-level comparison.
        Only valid for recommendation module_type.
        """
        df = self.load_data()
        return self._build_card_level_comparison(df)

    def _get_required_columns(self) -> List[str]:
        """Return required CSV columns based on module type."""
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

        raise ValueError(f"Unsupported module_type: {self.module_type}")

    def _get_metrics(self) -> List[str]:
        """Return metric columns only."""
        return [
            column
            for column in self._get_required_columns()
            if column not in {"version", "card_title"}
        ]

    def _validate_columns(self, df: pd.DataFrame) -> None:
        """Ensure the input CSV contains the required columns."""
        missing_cols = [
            col for col in self._get_required_columns() if col not in df.columns
        ]
        if missing_cols:
            raise ValueError(
                f"Missing required columns for '{self.module_type}': {missing_cols}"
            )

    def _build_version_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Build version-level summary.

        For recommendation data, this averages all cards inside each version.
        """
        metrics = self._get_metrics()
        
        # Group all rows by version. Compute mean (average) for each metric
        summary_df = (
            df.groupby("version", as_index=False)[metrics]
            .mean(numeric_only=True)
            .sort_values(by="version")
        )

        return summary_df

    def _build_card_level_comparison(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Return card-level rows for recommendation comparisons.
        """
        if self.module_type != self.RECOMMENDATION:
            raise ValueError(
                "Card-level comparison is only supported for recommendation module."
            )

        metrics = self._get_metrics()
        result_df = df[["version", "card_title", *metrics]].copy()

        return result_df.sort_values(by=["card_title", "version"])

    def plot_version_comparison(
        self,
        summary_df: pd.DataFrame,
        output_path: str | Path,
        title: str = "",
        show: bool = True,
    ) -> Path:
        from pathlib import Path
        import matplotlib.pyplot as plt

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        metrics = self._get_metrics()

        # Group by metrics, not versions
        plot_df = summary_df.set_index("version")[metrics].T

        plot_df.plot(kind="bar", figsize=(10, 6))

        plt.title(title or f"{self.module_type.capitalize()} Metric Comparison Across Versions")
        plt.xlabel("Metric")
        plt.ylabel("Score")
        plt.xticks(rotation=0)
        plt.legend(title="Version")
        plt.tight_layout()

        plt.savefig(output_path)

        if show:
            plt.show(block=False)
            plt.pause(0.1)

        if not show:
            plt.close()

        return output_path

# Dyplo
from pathlib import Path
def run_pipeline() -> None:
    """
    End-to-end pipeline:
    1) Convert JSON → CSV
    2) Run comparison for analysis
    3) Run comparison for recommendation
    """
    # Paths
    from pathlib import Path

    PROJECT_ROOT = Path(__file__).resolve().parents[3]   # adjust level if needed

    base_dir = PROJECT_ROOT / "data" / "outputs" / "run_20260414_004119" / "campaign_1"

    analysis_json = base_dir / "analysis_evaluation_results.json"
    recommendation_json = base_dir / "recommendation_evaluation_results.json"

    output_dir = base_dir / "comparison_results"

    analysis_csv = output_dir / "analysis_scores.csv"
    recommendation_csv = output_dir / "recommendation_scores.csv"

    version = "v2"  # You can parameterize this later

    # Step 1: JSON → CSV
    print("Converting JSON to CSV...")

    analysis_writer = JsonToCsvWriter(
        input_json=analysis_json,
        output_csv=analysis_csv,
        version=version,
    )
    analysis_writer.write_csv()

    recommendation_writer = JsonToCsvWriter(
        input_json=recommendation_json,
        output_csv=recommendation_csv,
        version=version,
    )
    recommendation_writer.write_csv()

    print("CSV files created successfully.")

    # Step 2: Analysis Comparison
    print("\nRunning analysis comparison...")

    analysis_comparison = ComparisonModule(
        comparison_csv=analysis_csv,
        module_type=ComparisonModule.ANALYSIS,
    )

    analysis_summary = analysis_comparison.compare_versions()
    print("\nAnalysis Summary:")
    print(analysis_summary)

    analysis_plot_path = output_dir / "analysis_comparison_plot.png"

    analysis_comparison.plot_version_comparison(
        summary_df=analysis_summary,
        output_path=analysis_plot_path,
        title="Analysis Scores Comparison",
        show=True,   # display + save
    )

    # Step 3: Recommendation Comparison
    print("\nRunning recommendation comparison...")

    recommendation_comparison = ComparisonModule(
        comparison_csv=recommendation_csv,
        module_type=ComparisonModule.RECOMMENDATION,
    )

    recommendation_summary = recommendation_comparison.compare_versions()
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
    card_level = recommendation_comparison.compare_recommendation_cards()
    print("\nRecommendation Card-Level Comparison:")
    print(card_level)

    # Optional: Save summaries
    analysis_summary.to_csv(output_dir / "analysis_summary.csv", index=False)
    recommendation_summary.to_csv(output_dir / "recommendation_summary.csv", index=False)
    card_level.to_csv(output_dir / "recommendation_card_level.csv", index=False)

    print("\nAll outputs saved successfully.")
    plt.show()


# Entry Point
if __name__ == "__main__":
    run_pipeline()    