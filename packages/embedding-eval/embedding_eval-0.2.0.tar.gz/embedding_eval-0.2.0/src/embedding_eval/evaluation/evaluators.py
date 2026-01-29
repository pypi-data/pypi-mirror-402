"""
Evaluation module for assessing retrieval quality.

Provides the BinaryEvaluator for comparing retrieved chunks against expected answers.
Uses substring matching with normalization - simple, reproducible, no LLM cost.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod

from embedding_eval.core.models import EvaluationMode, EvaluationScore, QAPair


class BaseEvaluator(ABC):
    """Abstract base class for evaluators."""

    @property
    @abstractmethod
    def mode(self) -> EvaluationMode:
        """Return the evaluation mode."""
        ...

    @abstractmethod
    def evaluate(
        self,
        question: str,
        expected_answer: str,
        retrieved_chunks: list[str],
    ) -> EvaluationScore:
        """
        Evaluate whether retrieved chunks can answer the question.

        Args:
            question: The question asked
            expected_answer: Ground truth answer
            retrieved_chunks: List of retrieved text chunks

        Returns:
            EvaluationScore with score and details
        """
        ...

    def evaluate_batch(
        self,
        qa_pairs: list[QAPair],
        retrieved_chunks_list: list[list[str]],
    ) -> list[EvaluationScore]:
        """
        Evaluate multiple Q&A pairs.

        Args:
            qa_pairs: List of Q&A pairs
            retrieved_chunks_list: List of retrieved chunks for each pair

        Returns:
            List of evaluation scores
        """
        scores = []
        for qa, chunks in zip(qa_pairs, retrieved_chunks_list, strict=True):
            score = self.evaluate(qa.question, qa.answer, chunks)
            score.qa_pair_id = qa.id
            scores.append(score)
        return scores


class BinaryEvaluator(BaseEvaluator):
    """
    Binary evaluator that checks if the answer is present in retrieved chunks.

    Uses substring matching with optional normalization to determine if
    the expected answer appears in any of the retrieved chunks.

    This is the recommended evaluator for parameter optimization:
    - Simple and reproducible
    - No LLM cost
    - Proven effective for fair comparison (see EDD-005)

    Example:
        ```python
        evaluator = BinaryEvaluator()
        score = evaluator.evaluate(
            question="What is the capital of France?",
            expected_answer="Paris",
            retrieved_chunks=["France is a country in Europe. Paris is its capital."]
        )
        print(score.score)  # 1.0
        ```
    """

    def __init__(
        self,
        case_sensitive: bool = False,
        normalize_whitespace: bool = True,
        partial_match_threshold: float = 0.8,
        fuzzy_word_match: bool = True,
        normalize_currency: bool = True,
    ):
        """
        Initialize binary evaluator.

        Args:
            case_sensitive: Whether matching is case-sensitive
            normalize_whitespace: Whether to normalize whitespace before matching
            partial_match_threshold: Minimum fraction of answer words that must appear
                                     for partial credit (0 = exact only, 1 = any word)
            fuzzy_word_match: Whether to use fuzzy matching for word forms
                              (handles plurals, verb conjugations, etc.)
            normalize_currency: Whether to normalize currency formatting
        """
        self._case_sensitive = case_sensitive
        self._normalize_whitespace = normalize_whitespace
        self._partial_match_threshold = partial_match_threshold
        self._fuzzy_word_match = fuzzy_word_match
        self._normalize_currency = normalize_currency

    @property
    def mode(self) -> EvaluationMode:
        return EvaluationMode.BINARY

    def evaluate(
        self,
        question: str,
        expected_answer: str,
        retrieved_chunks: list[str],
    ) -> EvaluationScore:
        """
        Check if the expected answer appears in retrieved chunks.

        Returns score of 1.0 if answer found, 0.0 otherwise.
        Also computes partial match score based on word overlap.
        """
        if not retrieved_chunks:
            return EvaluationScore(
                score=0.0,
                retrieved_chunks=retrieved_chunks,
                explanation="No chunks retrieved",
            )

        # Normalize texts
        normalized_answer = self._normalize(expected_answer)
        combined_chunks = " ".join(retrieved_chunks)
        normalized_chunks = self._normalize(combined_chunks)

        # Check for exact substring match
        if normalized_answer in normalized_chunks:
            return EvaluationScore(
                score=1.0,
                retrieved_chunks=retrieved_chunks,
                explanation="Exact answer found in retrieved chunks",
            )

        # Fallback: If answer starts with currency symbol, try without it
        if self._normalize_currency and re.match(r"^[$€£¥]", normalized_answer):
            answer_without_currency = re.sub(r"^[$€£¥]", "", normalized_answer)
            if answer_without_currency in normalized_chunks:
                return EvaluationScore(
                    score=1.0,
                    retrieved_chunks=retrieved_chunks,
                    explanation="Answer found (currency symbol stripped)",
                )

        # Check for partial match (word overlap)
        answer_words = set(normalized_answer.split())
        chunk_words = set(normalized_chunks.split())

        if answer_words:
            if self._fuzzy_word_match:
                overlap = self._count_fuzzy_matches(answer_words, chunk_words)
            else:
                overlap = len(answer_words & chunk_words)

            overlap_ratio = overlap / len(answer_words)

            if overlap_ratio >= self._partial_match_threshold:
                return EvaluationScore(
                    score=overlap_ratio,
                    retrieved_chunks=retrieved_chunks,
                    explanation=f"Partial match: {overlap}/{len(answer_words)} answer words found",
                )

        return EvaluationScore(
            score=0.0,
            retrieved_chunks=retrieved_chunks,
            explanation="Answer not found in retrieved chunks",
        )

    def _normalize(self, text: str) -> str:
        """Normalize text for matching."""
        result = text

        # Normalize curly quotes and apostrophes
        result = result.replace("\u2019", "'")  # ' -> '
        result = result.replace("\u2018", "'")  # ' -> '
        result = result.replace("\u201c", '"')  # " -> "
        result = result.replace("\u201d", '"')  # " -> "

        if not self._case_sensitive:
            result = result.lower()

        if self._normalize_currency:
            result = re.sub(r"([$€£¥])\s+", r"\1", result)

        # Remove trademark/registered symbols
        result = re.sub(r"[®™©]", "", result)

        if self._normalize_whitespace:
            result = " ".join(result.split())

        return result

    def _count_fuzzy_matches(self, answer_words: set, chunk_words: set) -> int:
        """
        Count fuzzy matches between answer words and chunk words.

        Handles common word form variations:
        - Plurals: "perspective" matches "perspectives"
        - Verb forms: "observe" matches "observes", "observing"
        """
        matches = 0
        chunk_text = " ".join(chunk_words)

        for word in answer_words:
            if word in chunk_words:
                matches += 1
                continue

            if word in chunk_text:
                matches += 1
                continue

            word_stem = word.rstrip("s")
            if any(cw.startswith(word_stem) or cw.startswith(word) for cw in chunk_words):
                matches += 1
                continue

            if any(word.startswith(cw.rstrip("s")) for cw in chunk_words if len(cw) > 3):
                matches += 1
                continue

        return matches


def get_evaluator(mode: EvaluationMode = EvaluationMode.BINARY, **kwargs) -> BaseEvaluator:
    """
    Factory function to get an evaluator by mode.

    Args:
        mode: Evaluation mode (currently only BINARY supported)
        **kwargs: Mode-specific parameters

    Returns:
        Configured evaluator instance
    """
    if mode == EvaluationMode.BINARY:
        return BinaryEvaluator(**kwargs)
    else:
        raise ValueError(f"Unknown evaluation mode: {mode}")
