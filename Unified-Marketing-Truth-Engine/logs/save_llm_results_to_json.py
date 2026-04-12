import os
import json
from datetime import datetime
from typing import Any


def save_results_to_json(llms_result: Any, log_dir: str = "logs") -> str:
    """
    Save LLM evaluation results to a timestamped JSON file.

    Args:
        llms_result (Any): Data to serialize (must be JSON serializable).
        log_dir (str): Directory where results will be stored.

    Returns:
        str: Path to the created JSON file.
    """

    # Ensure base directory exists
    os.makedirs(log_dir, exist_ok=True)

    # Create timestamped run directory
    date_str = datetime.now().strftime("%Y-%m-%d")
    run_dir = os.path.join(log_dir, date_str)
    os.makedirs(run_dir, exist_ok=True)

    # Define output file
    file_path = os.path.join(run_dir, "analysis_evaluation_results.json")

    # Write JSON
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(llms_result, file, ensure_ascii=False, indent=2)

    return file_path