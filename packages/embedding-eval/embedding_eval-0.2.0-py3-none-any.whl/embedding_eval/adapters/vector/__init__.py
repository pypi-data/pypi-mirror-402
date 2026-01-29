"""
Vector store adapters.

Provides the InMemoryVectorStore for storing and searching embeddings.
No external dependencies required.
"""

from embedding_eval.adapters.vector.inmemory import InMemoryVectorStore

__all__ = ["InMemoryVectorStore"]
