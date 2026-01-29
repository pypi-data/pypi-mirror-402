"""
Fixture validation utilities.

Provides tools to validate Q&A fixtures against documents and
check that fixtures meet statistical requirements.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AnswerIssue:
    """An issue found with an answer."""

    question: str
    answer: str
    issue_type: str  # "not_found", "partial_match", "case_mismatch"
    suggestion: str | None = None


@dataclass
class ValidationResult:
    """Result of fixture validation."""

    # Counts
    total_questions: int = 0
    answers_found: int = 0
    answers_missing: int = 0
    duplicates_found: int = 0

    # Distribution
    category_counts: dict[str, int] = field(default_factory=dict)
    difficulty_counts: dict[str, int] = field(default_factory=dict)

    # Issues
    answer_issues: list[AnswerIssue] = field(default_factory=list)
    duplicate_questions: list[str] = field(default_factory=list)

    # Threshold checks
    meets_min_questions: bool = False
    meets_recommended_questions: bool = False
    meets_min_multihop: bool = False
    meets_recommended_multihop: bool = False
    meets_min_hard: bool = False
    meets_recommended_hard: bool = False

    @property
    def category_percentages(self) -> dict[str, float]:
        """Get category distribution as percentages."""
        if self.total_questions == 0:
            return {}
        return {
            cat: (count / self.total_questions) * 100 for cat, count in self.category_counts.items()
        }

    @property
    def difficulty_percentages(self) -> dict[str, float]:
        """Get difficulty distribution as percentages."""
        if self.total_questions == 0:
            return {}
        return {
            diff: (count / self.total_questions) * 100
            for diff, count in self.difficulty_counts.items()
        }

    @property
    def multihop_percentage(self) -> float:
        """Get percentage of multi-hop questions."""
        if self.total_questions == 0:
            return 0.0
        return (self.category_counts.get("multi_hop", 0) / self.total_questions) * 100

    @property
    def hard_percentage(self) -> float:
        """Get percentage of hard questions."""
        if self.total_questions == 0:
            return 0.0
        return (self.difficulty_counts.get("hard", 0) / self.total_questions) * 100

    @property
    def is_valid(self) -> bool:
        """Check if fixture passes minimum requirements."""
        return (
            self.answers_missing == 0
            and self.duplicates_found == 0
            and self.meets_min_questions
            and self.meets_min_multihop
            and self.meets_min_hard
        )

    @property
    def summary(self) -> str:
        """Generate a human-readable summary."""
        lines = []
        lines.append("=" * 50)
        lines.append("FIXTURE VALIDATION REPORT")
        lines.append("=" * 50)

        # Basic counts
        lines.append(f"\nTotal questions: {self.total_questions}")
        lines.append(f"Answers verified: {self.answers_found}/{self.total_questions}")
        if self.answers_missing > 0:
            lines.append(f"  ✗ {self.answers_missing} answers NOT found in document")
        else:
            lines.append("  ✓ All answers found verbatim")

        if self.duplicates_found > 0:
            lines.append(f"  ✗ {self.duplicates_found} duplicate questions found")
        else:
            lines.append("  ✓ No duplicate questions")

        # Category distribution
        lines.append("\nCategory Distribution:")
        for cat, pct in sorted(self.category_percentages.items(), key=lambda x: -x[1]):
            count = self.category_counts[cat]
            lines.append(f"  {cat}: {pct:.1f}% ({count})")

        # Difficulty distribution
        lines.append("\nDifficulty Distribution:")
        for diff in ["easy", "medium", "hard"]:
            if diff in self.difficulty_counts:
                pct = self.difficulty_percentages[diff]
                count = self.difficulty_counts[diff]
                lines.append(f"  {diff}: {pct:.1f}% ({count})")

        # Threshold checks
        lines.append("\nThreshold Checks:")

        # Questions
        if self.meets_recommended_questions:
            lines.append(f"  ✓ Questions: {self.total_questions} (≥80 recommended)")
        elif self.meets_min_questions:
            lines.append(f"  ~ Questions: {self.total_questions} (≥50 min, ≥80 recommended)")
        else:
            lines.append(f"  ✗ Questions: {self.total_questions} (need ≥50 minimum)")

        # Multi-hop
        if self.meets_recommended_multihop:
            lines.append(f"  ✓ Multi-hop: {self.multihop_percentage:.1f}% (≥20% recommended)")
        elif self.meets_min_multihop:
            lines.append(
                f"  ~ Multi-hop: {self.multihop_percentage:.1f}% (≥10% min, ≥20% recommended)"
            )
        else:
            lines.append(f"  ✗ Multi-hop: {self.multihop_percentage:.1f}% (need ≥10% minimum)")

        # Hard
        if self.meets_recommended_hard:
            lines.append(f"  ✓ Hard: {self.hard_percentage:.1f}% (≥40% recommended)")
        elif self.meets_min_hard:
            lines.append(f"  ~ Hard: {self.hard_percentage:.1f}% (≥30% min, ≥40% recommended)")
        else:
            lines.append(f"  ✗ Hard: {self.hard_percentage:.1f}% (need ≥30% minimum)")

        # Overall status
        lines.append("\n" + "=" * 50)
        if self.is_valid:
            lines.append("STATUS: ✓ VALID (meets minimum requirements)")
        else:
            lines.append("STATUS: ✗ INVALID (does not meet minimum requirements)")
        lines.append("=" * 50)

        # Issues detail
        if self.answer_issues:
            lines.append("\nAnswer Issues:")
            for issue in self.answer_issues[:10]:  # Show first 10
                lines.append(f"  • Q: {issue.question[:50]}...")
                lines.append(f'    A: "{issue.answer}" - {issue.issue_type}')
                if issue.suggestion:
                    lines.append(f"    Suggestion: {issue.suggestion}")
            if len(self.answer_issues) > 10:
                lines.append(f"  ... and {len(self.answer_issues) - 10} more issues")

        if self.duplicate_questions:
            lines.append("\nDuplicate Questions:")
            for q in self.duplicate_questions[:5]:
                lines.append(f"  • {q[:60]}...")
            if len(self.duplicate_questions) > 5:
                lines.append(f"  ... and {len(self.duplicate_questions) - 5} more")

        return "\n".join(lines)


def validate_fixture(
    qa_pairs: list[dict[str, Any]],
    doc_content: str | None = None,
    min_questions: int = 50,
    recommended_questions: int = 80,
    min_multihop_pct: float = 10.0,
    recommended_multihop_pct: float = 20.0,
    min_hard_pct: float = 30.0,
    recommended_hard_pct: float = 40.0,
) -> ValidationResult:
    """
    Validate a Q&A fixture.

    Checks:
    - Answer verification (if doc_content provided)
    - Category distribution
    - Difficulty distribution
    - Duplicate questions
    - Threshold requirements

    Args:
        qa_pairs: List of Q&A pair dictionaries
        doc_content: Document content for answer verification (optional)
        min_questions: Minimum required questions (default: 50)
        recommended_questions: Recommended question count (default: 80)
        min_multihop_pct: Minimum multi-hop percentage (default: 10%)
        recommended_multihop_pct: Recommended multi-hop percentage (default: 20%)
        min_hard_pct: Minimum hard question percentage (default: 30%)
        recommended_hard_pct: Recommended hard percentage (default: 40%)

    Returns:
        ValidationResult with detailed findings

    Example:
        ```python
        from embedding_eval import validate_fixture

        result = validate_fixture(qa_pairs, doc_content)
        print(result.summary)

        if not result.is_valid:
            print("Issues found:")
            for issue in result.answer_issues:
                print(f"  - {issue.answer}: {issue.issue_type}")
        ```
    """
    result = ValidationResult()
    result.total_questions = len(qa_pairs)

    # Count categories and difficulties
    category_counter: Counter[str] = Counter()
    difficulty_counter: Counter[str] = Counter()
    questions_seen: dict[str, int] = {}

    for i, qa in enumerate(qa_pairs):
        question = qa.get("question", "")
        answer = qa.get("answer", "")
        category = qa.get("category", "exact")
        difficulty = qa.get("difficulty", "medium")

        # Count categories and difficulties
        category_counter[category] += 1
        difficulty_counter[difficulty] += 1

        # Check for duplicates (normalize whitespace)
        normalized_q = " ".join(question.lower().split())
        if normalized_q in questions_seen:
            result.duplicate_questions.append(question)
            result.duplicates_found += 1
        else:
            questions_seen[normalized_q] = i

        # Verify answer in document
        if doc_content is not None:
            issue = _check_answer(question, answer, doc_content)
            if issue:
                result.answer_issues.append(issue)
                result.answers_missing += 1
            else:
                result.answers_found += 1
        else:
            # If no document provided, assume all answers valid
            result.answers_found += 1

    result.category_counts = dict(category_counter)
    result.difficulty_counts = dict(difficulty_counter)

    # Check thresholds
    result.meets_min_questions = result.total_questions >= min_questions
    result.meets_recommended_questions = result.total_questions >= recommended_questions

    multihop_pct = result.multihop_percentage
    result.meets_min_multihop = multihop_pct >= min_multihop_pct
    result.meets_recommended_multihop = multihop_pct >= recommended_multihop_pct

    hard_pct = result.hard_percentage
    result.meets_min_hard = hard_pct >= min_hard_pct
    result.meets_recommended_hard = hard_pct >= recommended_hard_pct

    return result


def _check_answer(question: str, answer: str, doc_content: str) -> AnswerIssue | None:
    """
    Check if an answer appears in the document.

    Returns an AnswerIssue if there's a problem, None if answer is valid.
    """
    if not answer or not answer.strip():
        return AnswerIssue(
            question=question,
            answer=answer,
            issue_type="empty_answer",
            suggestion="Provide a non-empty answer",
        )

    # Normalize whitespace in answer for matching
    normalized_answer = " ".join(answer.split())

    # Check exact match
    if normalized_answer in doc_content:
        return None

    # Check case-insensitive match
    if normalized_answer.lower() in doc_content.lower():
        # Find the actual case in document
        pattern = re.escape(normalized_answer)
        match = re.search(pattern, doc_content, re.IGNORECASE)
        if match:
            return AnswerIssue(
                question=question,
                answer=answer,
                issue_type="case_mismatch",
                suggestion=f'Found as: "{match.group()}"',
            )

    # Check for partial matches (answer words appear but not together)
    answer_words = normalized_answer.lower().split()
    if len(answer_words) > 1:
        doc_lower = doc_content.lower()
        words_found = sum(1 for word in answer_words if word in doc_lower)
        if words_found == len(answer_words):
            return AnswerIssue(
                question=question,
                answer=answer,
                issue_type="words_scattered",
                suggestion="All words found but not as exact phrase",
            )
        elif words_found > 0:
            return AnswerIssue(
                question=question,
                answer=answer,
                issue_type="partial_match",
                suggestion=f"Only {words_found}/{len(answer_words)} words found",
            )

    # Try to find similar strings
    suggestion = _find_similar(normalized_answer, doc_content)

    return AnswerIssue(
        question=question,
        answer=answer,
        issue_type="not_found",
        suggestion=suggestion,
    )


def _find_similar(answer: str, doc_content: str, context_size: int = 50) -> str | None:
    """Try to find similar text in document."""
    answer_lower = answer.lower()

    # Try matching first few words
    words = answer_lower.split()
    if len(words) >= 2:
        first_words = " ".join(words[:2])
        idx = doc_content.lower().find(first_words)
        if idx >= 0:
            # Extract context around match
            start = max(0, idx - 10)
            end = min(len(doc_content), idx + len(answer) + context_size)
            context = doc_content[start:end].replace("\n", " ")
            return f'Similar text near: "...{context}..."'

    # Try matching first word only
    if words:
        first_word = words[0]
        if len(first_word) > 3:  # Skip short words
            idx = doc_content.lower().find(first_word)
            if idx >= 0:
                start = max(0, idx - 10)
                end = min(len(doc_content), idx + context_size)
                context = doc_content[start:end].replace("\n", " ")
                return f'Found "{first_word}" near: "...{context}..."'

    return None


def print_validation_report(result: ValidationResult) -> None:
    """Print a validation report to stdout."""
    print(result.summary)
