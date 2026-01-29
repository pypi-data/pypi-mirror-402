"""
Adapters for external services.

- embedding: Embedding model adapters (SentenceTransformers, OpenAI)
- vector: Vector store adapters (InMemoryVectorStore)
"""

from embedding_eval.adapters.embedding import SentenceTransformerEmbedding
from embedding_eval.adapters.vector import InMemoryVectorStore

__all__ = ["SentenceTransformerEmbedding", "InMemoryVectorStore"]
