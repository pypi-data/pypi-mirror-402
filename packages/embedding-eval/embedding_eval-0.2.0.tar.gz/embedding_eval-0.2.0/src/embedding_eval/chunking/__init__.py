"""
Chunking strategies for document processing.

Provides the FixedSizeChunker for splitting documents into chunks
suitable for embedding and retrieval.
"""

from embedding_eval.chunking.strategies import (
    BaseChunker,
    FixedSizeChunker,
    get_chunker,
)

__all__ = [
    "BaseChunker",
    "FixedSizeChunker",
    "get_chunker",
]
