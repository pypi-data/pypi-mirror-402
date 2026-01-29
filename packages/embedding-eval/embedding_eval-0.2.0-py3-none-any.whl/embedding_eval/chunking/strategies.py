"""
Chunking strategies for document processing.

Provides strategies for splitting documents into chunks suitable for
embedding and retrieval.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import tiktoken

from embedding_eval.core.models import Chunk, ChunkingStrategy, Document


class BaseChunker(ABC):
    """Abstract base class for chunking strategies."""

    @property
    @abstractmethod
    def strategy(self) -> ChunkingStrategy:
        """Return the chunking strategy type."""
        ...

    @abstractmethod
    def chunk(self, document: Document) -> list[Chunk]:
        """
        Split a document into chunks.

        Args:
            document: Document to chunk

        Returns:
            List of Chunk objects
        """
        ...

    @property
    @abstractmethod
    def chunk_size(self) -> int:
        """Return configured chunk size."""
        ...

    @property
    @abstractmethod
    def overlap(self) -> int:
        """Return configured overlap."""
        ...


class FixedSizeChunker(BaseChunker):
    """
    Fixed-size chunking with token-based splitting.

    Splits text into chunks of approximately equal token size with optional overlap.
    Uses tiktoken for accurate token counting.

    This is the recommended default chunker - simple, generalizable, and effective.

    Example:
        ```python
        chunker = FixedSizeChunker(chunk_size=512, overlap=50)
        chunks = chunker.chunk(document)
        ```
    """

    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 50,
        encoding_name: str = "cl100k_base",
    ):
        """
        Initialize fixed-size chunker.

        Args:
            chunk_size: Target chunk size in tokens (default: 512)
            overlap: Number of overlapping tokens between chunks (default: 50)
            encoding_name: Tiktoken encoding name (cl100k_base for GPT-4/embeddings)
        """
        self._chunk_size = chunk_size
        self._overlap = overlap
        self._encoding = tiktoken.get_encoding(encoding_name)

    @property
    def strategy(self) -> ChunkingStrategy:
        return ChunkingStrategy.FIXED

    @property
    def chunk_size(self) -> int:
        return self._chunk_size

    @property
    def overlap(self) -> int:
        return self._overlap

    def chunk(self, document: Document) -> list[Chunk]:
        """Split document into fixed-size token chunks."""
        if not document.content:
            return []

        # Tokenize the entire document
        tokens = self._encoding.encode(document.content)

        if len(tokens) == 0:
            return []

        chunks = []
        start_idx = 0
        chunk_num = 0

        while start_idx < len(tokens):
            # Calculate end index
            end_idx = min(start_idx + self._chunk_size, len(tokens))

            # Extract tokens for this chunk
            chunk_tokens = tokens[start_idx:end_idx]

            # Decode back to text
            chunk_text = self._encoding.decode(chunk_tokens)

            # Calculate character positions
            char_start, char_end = self._find_char_positions(
                document.content, chunk_text, start_idx, tokens
            )

            chunk = Chunk(
                content=chunk_text,
                document_id=document.id,
                strategy=ChunkingStrategy.FIXED,
                start_char=char_start,
                end_char=char_end,
                token_count=len(chunk_tokens),
                metadata={
                    "chunk_index": chunk_num,
                    "chunk_size_setting": self._chunk_size,
                    "overlap_setting": self._overlap,
                },
            )
            chunks.append(chunk)

            # Move to next chunk with overlap
            if end_idx >= len(tokens):
                break

            start_idx = end_idx - self._overlap
            chunk_num += 1

            # Prevent infinite loop if overlap >= chunk_size
            if start_idx <= 0 or self._overlap >= self._chunk_size:
                start_idx = end_idx

        return chunks

    def _find_char_positions(
        self,
        original_text: str,
        chunk_text: str,
        token_start: int,
        all_tokens: list[int],
    ) -> tuple[int, int]:
        """Find character positions for a chunk in the original text."""
        prefix_text = self._encoding.decode(all_tokens[:token_start])
        char_start = len(prefix_text)
        char_end = char_start + len(chunk_text)
        return char_start, char_end

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self._encoding.encode(text))

    def chunk_text(self, text: str, document_id: str = "") -> list[Chunk]:
        """
        Convenience method to chunk raw text.

        Args:
            text: Text to chunk
            document_id: Optional document ID for metadata

        Returns:
            List of Chunk objects
        """
        doc = Document(id=document_id or "doc", content=text)
        return self.chunk(doc)


def get_chunker(
    strategy: ChunkingStrategy = ChunkingStrategy.FIXED,
    chunk_size: int = 512,
    overlap: int = 50,
    **kwargs,
) -> BaseChunker:
    """
    Factory function to get a chunker by strategy.

    Args:
        strategy: Chunking strategy (currently only FIXED supported)
        chunk_size: Target chunk size in tokens
        overlap: Overlap between chunks in tokens
        **kwargs: Additional strategy-specific parameters

    Returns:
        Configured chunker instance
    """
    if strategy == ChunkingStrategy.FIXED:
        return FixedSizeChunker(chunk_size=chunk_size, overlap=overlap, **kwargs)
    else:
        raise ValueError(f"Unknown chunking strategy: {strategy}")
