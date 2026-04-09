class AnalysisEvaluatorError(Exception):
    """Base exception for AnalysisEvaluator errors."""


class InvalidInputError(AnalysisEvaluatorError):
    """Raised when forward() receives invalid inputs."""


class EvaluationExecutionError(AnalysisEvaluatorError):
    """Raised when the DSPy evaluation call fails."""


class InvalidEvaluationResultError(AnalysisEvaluatorError):
    """Raised when the evaluation result is missing required structure."""

