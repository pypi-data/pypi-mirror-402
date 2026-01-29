"""
Embedding model adapters.

Provides standardized interfaces for embedding providers:
- SentenceTransformerEmbedding: Free, local models (recommended: bge-base)
- OpenAIEmbedding: OpenAI API models (text-embedding-3-small)
"""

from embedding_eval.adapters.embedding.sentence_transformer import (
    MODEL_ALIASES,
    POPULAR_MODELS,
    SentenceTransformerEmbedding,
    get_model_info,
    list_models,
)

__all__ = [
    "SentenceTransformerEmbedding",
    "POPULAR_MODELS",
    "MODEL_ALIASES",
    "list_models",
    "get_model_info",
]


# Lazy import OpenAI to avoid requiring openai package
def get_openai_embedding(*args, **kwargs):
    """Get OpenAI embedding adapter (requires openai package)."""
    from embedding_eval.adapters.embedding.openai_embedding import OpenAIEmbedding

    return OpenAIEmbedding(*args, **kwargs)
