"""
Evaluation module for assessing retrieval quality.

Provides the BinaryEvaluator for comparing retrieved chunks against expected answers.
Simple, reproducible, no LLM cost.

Also provides fixture validation utilities to verify Q&A fixtures meet quality requirements.
"""

from embedding_eval.evaluation.evaluators import (
    BaseEvaluator,
    BinaryEvaluator,
    get_evaluator,
)
from embedding_eval.evaluation.validation import (
    AnswerIssue,
    ValidationResult,
    print_validation_report,
    validate_fixture,
)

__all__ = [
    # Evaluators
    "BaseEvaluator",
    "BinaryEvaluator",
    "get_evaluator",
    # Validation
    "AnswerIssue",
    "ValidationResult",
    "print_validation_report",
    "validate_fixture",
]
