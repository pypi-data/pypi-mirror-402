"""
Protocol definitions for adapter interfaces.

These protocols define the contracts that adapter implementations must satisfy.
Using Python's Protocol (structural subtyping) allows for duck typing while
providing IDE support and type checking.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

# =============================================================================
# Vector Store Protocol
# =============================================================================


@runtime_checkable
class VectorStore(Protocol):
    """
    Protocol for vector database operations.

    Implementations should handle embedding storage and similarity search.

    Example implementations:
    - InMemoryVectorStore: No external dependencies
    - QdrantVectorStore: Production Qdrant backend
    """

    def connect(self) -> None:
        """Establish connection to the vector database."""
        ...

    def disconnect(self) -> None:
        """Close connection to the vector database."""
        ...

    def is_connected(self) -> bool:
        """Check if connection is active."""
        ...

    # -------------------------------------------------------------------------
    # Collection Management
    # -------------------------------------------------------------------------

    def create_collection(
        self,
        name: str,
        dimensions: int,
        distance_metric: str = "cosine",
    ) -> bool:
        """
        Create a new vector collection.

        Args:
            name: Collection name
            dimensions: Vector dimensions
            distance_metric: Distance metric (cosine, euclidean, dot)

        Returns:
            True if created successfully
        """
        ...

    def delete_collection(self, name: str) -> bool:
        """Delete a collection."""
        ...

    def collection_exists(self, name: str) -> bool:
        """Check if collection exists."""
        ...

    # -------------------------------------------------------------------------
    # Vector Operations
    # -------------------------------------------------------------------------

    def upsert(
        self,
        collection_name: str,
        ids: list[str],
        embeddings: list[list[float]],
        metadata: list[dict[str, Any]] | None = None,
        texts: list[str] | None = None,
    ) -> int:
        """
        Insert or update vectors in a collection.

        Args:
            collection_name: Target collection
            ids: Vector IDs
            embeddings: Vector embeddings
            metadata: Optional metadata for each vector
            texts: Optional original text for each vector

        Returns:
            Number of vectors upserted
        """
        ...

    def search(
        self,
        collection_name: str,
        query_embedding: list[float],
        top_k: int = 5,
        filter: dict[str, Any] | None = None,
        include_metadata: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Search for similar vectors.

        Args:
            collection_name: Collection to search
            query_embedding: Query vector
            top_k: Number of results
            filter: Optional metadata filter
            include_metadata: Include metadata in results

        Returns:
            List of results with id, score, and metadata
        """
        ...

    def count(self, collection_name: str) -> int:
        """Get number of vectors in collection."""
        ...


# =============================================================================
# Embedding Model Protocol
# =============================================================================


@runtime_checkable
class EmbeddingModel(Protocol):
    """
    Protocol for embedding model providers.

    Implementations should handle text embedding with support for
    batching and dimension configuration.

    Example implementations:
    - SentenceTransformerEmbedding: Local models (free)
    - OpenAIEmbedding: OpenAI API models
    """

    @property
    def model_name(self) -> str:
        """Full model identifier (e.g., 'sentence-transformers/bge-base-en-v1.5')."""
        ...

    @property
    def dimensions(self) -> int:
        """Output embedding dimensions."""
        ...

    def embed_text(self, text: str) -> list[float]:
        """
        Embed a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        ...

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Embed multiple texts (batched for efficiency).

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        ...

    def embed_query(self, query: str) -> list[float]:
        """
        Embed a query (may use different parameters for asymmetric search).

        Args:
            query: Query text

        Returns:
            Query embedding vector
        """
        ...


# =============================================================================
# Chunker Protocol
# =============================================================================


@runtime_checkable
class Chunker(Protocol):
    """
    Protocol for text chunking strategies.

    Example implementations:
    - FixedSizeChunker: Split by token count
    - HierarchicalChunker: Section-aware chunking
    """

    def chunk(self, text: str, document_id: str = "") -> list:
        """
        Split text into chunks.

        Args:
            text: Text to chunk
            document_id: Optional document ID for chunk metadata

        Returns:
            List of Chunk objects
        """
        ...
