import os
import json
from datetime import datetime
from typing import Any


def save_results_to_json(llms_result: Any, output_dir: str = "logs", filename: str = "evaluation_results.json") -> str:
    """
    Save results to a timestamped JSON file.
    """

    # Ensure base directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Create timestamped run directory
    date_str = datetime.now().strftime("%Y-%m-%d")
    run_dir = os.path.join(output_dir, date_str)
    os.makedirs(run_dir, exist_ok=True)

    # Define output file
    file_path = os.path.join(run_dir, filename)

    # Write JSON
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(llms_result, file, ensure_ascii=False, indent=2)

    return file_path