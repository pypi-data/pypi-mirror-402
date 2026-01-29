"""
Core data models for embedding evaluation.

These models define the fundamental data structures used for
documents, chunks, Q&A pairs, and evaluation results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

# =============================================================================
# Enums
# =============================================================================


class ChunkingStrategy(str, Enum):
    """Available chunking strategies."""

    FIXED = "fixed"
    HIERARCHICAL = "hierarchical"


class EvaluationMode(str, Enum):
    """Evaluation modes for Q&A assessment."""

    BINARY = "binary"  # Answer substring present in retrieved chunks


# =============================================================================
# Core Data Models
# =============================================================================


@dataclass
class Document:
    """Represents an ingested document."""

    id: str = field(default_factory=lambda: f"doc_{uuid4().hex[:8]}")
    name: str = ""
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Section:
    """A logical section within a document."""

    id: str = field(default_factory=lambda: f"sec_{uuid4().hex[:8]}")
    title: str = ""
    content: str = ""
    level: int = 1  # Heading level (1-6)
    parent_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Chunk:
    """A chunk of text prepared for embedding."""

    id: str = field(default_factory=lambda: f"chunk_{uuid4().hex[:8]}")
    content: str = ""
    document_id: str = ""
    section_id: str | None = None

    # Chunking metadata
    strategy: ChunkingStrategy = ChunkingStrategy.FIXED
    start_char: int = 0
    end_char: int = 0
    token_count: int = 0

    # Embedding metadata (populated after embedding)
    embedding_model: str | None = None
    embedding: list[float] | None = None

    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class QAPair:
    """A question-answer pair for evaluation."""

    id: str = field(default_factory=lambda: f"qa_{uuid4().hex[:8]}")
    question: str = ""
    answer: str = ""
    document_id: str | None = None
    category: str = "exact"  # exact, multi_hop, fine_detail, etc.
    difficulty: str = "medium"  # easy, medium, hard
    metadata: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Configuration Models
# =============================================================================


@dataclass
class ChunkingConfig:
    """Configuration for a chunking strategy."""

    strategy: ChunkingStrategy = ChunkingStrategy.FIXED
    chunk_size: int = 512  # Target size in tokens
    chunk_overlap: int = 50  # Overlap in tokens
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class EmbeddingConfig:
    """Configuration for an embedding model."""

    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    dimensions: int | None = None
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalConfig:
    """Configuration for retrieval parameters."""

    top_k: int = 5
    similarity_threshold: float = 0.0
    params: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Result Models
# =============================================================================


@dataclass
class EvaluationScore:
    """Score for a single Q&A pair evaluation."""

    qa_pair_id: str = ""
    score: float = 0.0  # 0.0 to 1.0
    retrieved_chunks: list[str] = field(default_factory=list)
    explanation: str | None = None

    def __bool__(self) -> bool:
        """Return True if evaluation passed (score >= 0.5)."""
        return self.score >= 0.5


@dataclass
class ConfigurationResult:
    """Result for a single configuration combination."""

    id: str = field(default_factory=lambda: f"result_{uuid4().hex[:8]}")

    # Configuration used
    chunking_config: ChunkingConfig | None = None
    embedding_config: EmbeddingConfig | None = None
    retrieval_config: RetrievalConfig | None = None

    # Scores
    scores: list[EvaluationScore] = field(default_factory=list)
    accuracy: float = 0.0
    questions_passed: int = 0
    questions_total: int = 0

    # Timing
    embedding_time_ms: int = 0
    retrieval_time_ms: int = 0

    error: str | None = None


@dataclass
class OptimizationResult:
    """Result of a fair comparison optimization run."""

    model_name: str = ""

    # Best configuration found
    best_accuracy: float = 0.0
    best_params: dict[str, Any] = field(default_factory=dict)

    # Baseline (default params)
    baseline_accuracy: float = 0.0
    baseline_params: dict[str, Any] = field(default_factory=dict)

    # Improvement
    improvement_pct: float = 0.0

    # All results from grid search
    all_results: list[ConfigurationResult] = field(default_factory=list)

    # Confidence interval (95%)
    ci_lower: float = 0.0
    ci_upper: float = 0.0
