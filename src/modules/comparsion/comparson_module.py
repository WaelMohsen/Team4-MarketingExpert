import json
import csv
from pathlib import Path

INPUT_JSON = "/Users/marwa/Desktop/Marwa/NLP course/MarketingExpert/Team4-MarketingExpert/data/outputs/run_20260414_004119/campaign_1/analysis_evaluation_results.json"
OUTPUT_CSV = "/Users/marwa/Desktop/Marwa/NLP course/MarketingExpert/Team4-MarketingExpert/data/outputs/run_20260414_004119/comparsion_results/comparson_result.csv"

def ReadJsonAndWriteCsv():
    input_path = Path(INPUT_JSON)
    if not input_path.exists():
        raise FileNotFoundError(f"File not found: {INPUT_JSON}")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    scores = data.get("scores", {})

    row = {
        "clarity": scores.get("clarity"),
        "accuracy": scores.get("accuracy"),
        "structure": scores.get("structure"),
        "overall": scores.get("overall"),
    }

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["clarity", "accuracy", "structure", "overall", "verdict"]
        )
        writer.writeheader()
        writer.writerow(row)

    print(f"Saved CSV to: {OUTPUT_CSV}")
    print("Extracted data:", row)
