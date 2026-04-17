import json
import csv
from pathlib import Path
from typing import Any, Dict
from src.core.base_module import BaseModule
import pandas as pd
import matplotlib.pyplot as plt

class ComparisonModule(BaseModule):

    def __init__(self, input_json: str, output_csv: str, version: str): 
        self.input_json = Path(input_json)
        self.output_csv = Path(output_csv)
        self.version = version




    def ReadJsonAndWriteCsv(self):
        """
        Read analysis_result/ recommendation_result JSON and append metrics to CSV.
        """

        if not self.input_json.exists():
            raise FileNotFoundError(f"File not found: {self.input_json}")

        # ensure output directory exists
        self.output_csv.parent.mkdir(parents=True, exist_ok=True)

        # read JSON
        with open(self.input_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        scores = data.get("scores", {})

        row = {
            "version": self.version,
            "clarity": scores.get("clarity"),
            "accuracy": scores.get("accuracy"),
            "structure": scores.get("structure"),
            "overall": scores.get("overall"),
        }

        file_exists = self.output_csv.exists()

        # append to CSV
        with open(self.output_csv, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["version", "clarity", "accuracy", "structure", "overall"]
            )

            # write header only once
            if not file_exists:
                writer.writeheader()

            writer.writerow(row)

        

    def compare_versions(self, csv_path: str):
        """
        Compare metrics across different versions and draw charts.
        """
        df = pd.read_csv(csv_path)
        required_cols = ["version", "clarity", "accuracy", "structure"]
        for col in required_cols:
            if col not in df.columns:
               raise ValueError(f"Missing column: {col}")

        # draw bar charts for each metric
        # normalize version names
        df["version"] = df["version"].str.lower()
        metrics = ["clarity", "accuracy", "structure","overall"]

        for metric in metrics:
            plt.figure(figsize=(6, 4))

            plt.bar(df["version"], df[metric])

            plt.title(f"{metric.capitalize()} Comparison Across Versions")
            plt.xlabel("Version")
            plt.ylabel("Score")
            plt.ylim(0, 3.2)

            plt.tight_layout()
            plt.show()
    
    def run(self):
        self.ReadJsonAndWriteCsv()
        self.compare_versions(str(self.output_csv)) 


def main():
    INPUT_JSON = "../../../data/outputs/run_20260414_004119/campaign_1/analysis_evaluation_results.json"
    OUTPUT_CSV = "../../../data/outputs/run_20260414_004119/comparsion_results/analysis_comparson_result.csv"
    comparison_module = ComparisonModule(
        input_json=INPUT_JSON,
        output_csv=OUTPUT_CSV,
        version="v1"
    )
    comparison_module.run()

       
if __name__ == "__main__":
    main()  