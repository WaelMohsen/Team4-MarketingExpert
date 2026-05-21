import csv
import json
from pathlib import Path
from typing import Any, Dict, List


class JsonToCsvWriter:
    """
    Reads evaluation JSON files and appends normalized rows to a CSV file.

    Supported JSON formats:
    1) Analysis evaluation JSON
    2) Recommendation evaluation JSON
    """

    ANALYSIS_TYPE = "analysis"
    RECOMMENDATION_TYPE = "recommendation"

    def __init__(self, input_json: str | Path, output_csv: str | Path, version: str) -> None:
        self.input_json = Path(input_json)
        self.output_csv = Path(output_csv)
        self.version = version

    def write_csv(self) -> None:
        """
        Main entry point:
        - validate input
        - load JSON
        - detect JSON type
        - extract rows
        - write rows using the correct header
        """
        self._validate_input_file()
        data = self._load_json()
        json_type = self._detect_json_type(data)
        rows = self._extract_rows(data, json_type)
        fieldnames = self._get_fieldnames(json_type)
        print(rows)
        print(fieldnames)
        if not rows:
            raise ValueError("No rows could be extracted from the JSON file.")

        self._ensure_output_directory()
        self._append_rows_to_csv(rows, fieldnames)

    def _validate_input_file(self) -> None:
        if not self.input_json.exists():
            raise FileNotFoundError(f"File not found: {self.input_json}")

    def _ensure_output_directory(self) -> None:
        self.output_csv.parent.mkdir(parents=True, exist_ok=True)

    def _load_json(self) -> Any:
        with open(self.input_json, "r", encoding="utf-8") as file:
            return json.load(file)

    def _detect_json_type(self, data: Any) -> str:

      """
      Detect whether JSON is:
       - analysis evaluation JSON:
        dict with top-level 'scores' containing:
        clarity, accuracy, structure, overall

       - recommendation evaluation JSON:
        dict with top-level 'scores' containing:
        Feasibility, Recommendation_Count, Analysis_Grounding,
        Action_Step_Completeness, Priority_Alignment,
        Tone_Audience_Compliance, Expected_Impact_Quality, Overall
     """

      if not isinstance(data, dict):
        raise ValueError("Invalid JSON format. Expected a dictionary.")

      scores = data.get("scores")

      if not isinstance(scores, dict):
        raise ValueError("Could not determine JSON type: missing or invalid 'scores' section.")

      analysis_score_keys = {
        "clarity",
        "accuracy",
        "structure",
        "hallucination",''
        'kpi_alignment',
        "overall",
      }

      recommendation_score_keys = {
        "Structure",
        "Feasibility",
        "Recommendation_Count",
        "Analysis_Grounding",
        "Action_Step_Completeness",
        "Priority_Alignment",
        "Tone_Audience_Compliance",
        "Expected_Impact_Quality",
        "Overall",
      }

      score_keys = set(scores.keys())

      if analysis_score_keys.issubset(score_keys):
        return self.ANALYSIS_TYPE

      if recommendation_score_keys.issubset(score_keys):
        return self.RECOMMENDATION_TYPE

      raise ValueError(
        f"Could not determine JSON type from score keys: {sorted(score_keys)}"
    )

    def _extract_rows(self, data: Any, json_type: str) -> List[Dict[str, Any]]:
        if json_type == self.ANALYSIS_TYPE:
            return self._build_analysis_row(data)
        

        if json_type == self.RECOMMENDATION_TYPE:
            return self._build_recommendation_rows(data)

        raise ValueError(f"Unsupported JSON type: {json_type}")

    def _get_fieldnames(self, json_type: str) -> List[str]:
        """
        Return the correct CSV header for each JSON type.
        """
        if json_type == self.ANALYSIS_TYPE:
            return ["version", "clarity", "accuracy", "structure", "hallucination","kpi_alignment","overall"]

        if json_type == self.RECOMMENDATION_TYPE:
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
                "Overall"]

        raise ValueError(f"Unsupported JSON type: {json_type}")

    def _build_analysis_row(self, data: Dict[str, Any]) -> Dict[str, Any]:
        scores = data.get("scores", {})
        return {
            "version": self.version,
            "clarity": scores.get("clarity"),
            "accuracy": scores.get("accuracy"),
            "structure": scores.get("structure"),
            "hallucination" : scores.get("hallucination"),
            "kpi_alignment": scores.get("kpi_alignment"),
            "overall": scores.get("overall"),
        }

  
    def _build_recommendation_rows(self, data: Dict[str, Any]) ->Dict[str, Any]:
         scores = data.get("scores", {})

         return  {
            "version": self.version,
            "Structure": scores.get("Structure"),
            "Feasibility": scores.get("Feasibility"),
            "Recommendation_Count": scores.get("Recommendation_Count"),
            "Analysis_Grounding": scores.get("Analysis_Grounding"),
            "Action_Step_Completeness": scores.get("Action_Step_Completeness"),
            "Priority_Alignment": scores.get("Priority_Alignment"),
            "Tone_Audience_Compliance": scores.get("Tone_Audience_Compliance"),
            "Expected_Impact_Quality": scores.get("Expected_Impact_Quality"),
            "Overall": scores.get("Overall"),
          }
       

     

    def _append_rows_to_csv(
        self,
        row: Dict[str, Any],
        fieldnames: List[str],
    ) -> None:
        """
        Append rows to CSV using the correct header.
        """
        file_exists = self.output_csv.exists()
        print( "this row"+str(row))
        with open(self.output_csv, "a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            writer.writerow(row)
   