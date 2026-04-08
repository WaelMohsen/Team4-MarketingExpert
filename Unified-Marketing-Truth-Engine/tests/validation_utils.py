

import json
from typing import Any, Dict, Union
from analysis_evaluator_error_handling import InvalidInputError, EvaluationExecutionError, InvalidEvaluationResultError
StructuredInput = Union[str, list, dict]

class ValidationUtils:
    """
    Utility class for validation, normalization, and safe type casting.
    All methods are static and can be used without instantiating the class.
    """

    # ---------- Type Casting ----------

    @staticmethod
    def cast_to_float(value: Any, default: float = 0.0) -> float:
        """
        Safely converts input to float with fallback.
        """
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def cast_to_bool(value: Any, default: bool = False) -> bool:
        """
        Safely converts input to boolean.
        """
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "1", "yes"}:
                return True
            if normalized in {"false", "0", "no", ""}:
                return False
            return default

        if isinstance(value, (int, float)):
            return bool(value)

        return default

    # ---------- Score Handling ----------

    @staticmethod
    def clamp_score(score: float, min_value: float = 1.0, max_value: float = 3.0) -> float:
        """
        Ensures a score stays within a defined range.
        """
        if not isinstance(min_value, (int, float)) or not isinstance(max_value, (int, float)):
            raise ValueError("min_value and max_value must be numeric.")

        if min_value > max_value:
            raise ValueError(
                f"min_value ({min_value}) cannot be greater than max_value ({max_value})."
            )

        if not isinstance(score, (int, float)):
            raise TypeError(
                f"score must be numeric, got {type(score).__name__}."
            )

        return min(max(score, min_value), max_value)

    # ---------- Structure Helpers ----------

    @staticmethod
    def ensure_list(value: Any) -> list:
        """
        Normalize value into a list.
        """
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return [value]
        return [value]

    # ---------- Text Validation ----------

    @staticmethod
    def validate_text_input(value: Any, var_name: str) -> str:
        """
        Ensures input is a non-empty string.
        """
        if not isinstance(value, str):
            raise InvalidInputError(
                f"{var_name} must be a string, got {type(value).__name__}."
            )

        cleaned_value = value.strip()
        if not cleaned_value:
            raise InvalidInputError(f"{var_name} cannot be empty.")

        return cleaned_value

    # ---------- Structure → String ----------

    @staticmethod
    def convert_structure_to_string(data: Any, var_name: str) -> str:
        """
        Converts structured input (str, list, dict) into a clean string.
        """
        if isinstance(data, str):
            cleaned_value = data.strip()
            if not cleaned_value:
                raise InvalidInputError(f"{var_name} cannot be empty.")
            return cleaned_value

        if isinstance(data, (list, dict)):
            try:
                return json.dumps(data, indent=2)
            except TypeError as exc:
                raise InvalidInputError(
                    f"{var_name} contains non-serializable values."
                ) from exc

        raise InvalidInputError(
            f"{var_name} must be a string, list, or dict, got {type(data).__name__}."
        )