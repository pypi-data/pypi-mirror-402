"""
Core data models and protocols.
"""

from embedding_eval.core.models import (
    Chunk,
    ChunkingConfig,
    ChunkingStrategy,
    ConfigurationResult,
    Document,
    EmbeddingConfig,
    EvaluationMode,
    EvaluationScore,
    OptimizationResult,
    QAPair,
    RetrievalConfig,
    Section,
)
from embedding_eval.core.protocols import Chunker, EmbeddingModel, VectorStore

__all__ = [
    # Models
    "Chunk",
    "ChunkingConfig",
    "ChunkingStrategy",
    "ConfigurationResult",
    "Document",
    "EmbeddingConfig",
    "EvaluationMode",
    "EvaluationScore",
    "OptimizationResult",
    "QAPair",
    "RetrievalConfig",
    "Section",
    # Protocols
    "Chunker",
    "EmbeddingModel",
    "VectorStore",
]
