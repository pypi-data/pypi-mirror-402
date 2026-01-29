"""
Sentence Transformers Embedding Adapter.

Provides embeddings using open-source models from HuggingFace.
Free to use, runs locally, no API costs.

Recommended models:
- BAAI/bge-base-en-v1.5: Best cost/performance (94.4% accuracy)
- sentence-transformers/all-MiniLM-L6-v2: Fast, lightweight
"""

from __future__ import annotations

import logging
from typing import Any, Literal

logger = logging.getLogger(__name__)


# Popular model configurations
POPULAR_MODELS: dict[str, dict[str, Any]] = {
    "BAAI/bge-base-en-v1.5": {
        "dimensions": 768,
        "max_seq_length": 512,
        "requires_prefix": True,
        "query_prefix": "Represent this sentence for searching relevant passages: ",
        "document_prefix": "",
        "notes": "Strong general purpose, recommended",
    },
    "BAAI/bge-small-en-v1.5": {
        "dimensions": 384,
        "max_seq_length": 512,
        "requires_prefix": True,
        "query_prefix": "Represent this sentence for searching relevant passages: ",
        "document_prefix": "",
        "notes": "Smaller, faster BGE variant",
    },
    "sentence-transformers/all-MiniLM-L6-v2": {
        "dimensions": 384,
        "max_seq_length": 256,
        "requires_prefix": False,
        "notes": "Fast, lightweight, great for prototyping",
    },
    "sentence-transformers/all-mpnet-base-v2": {
        "dimensions": 768,
        "max_seq_length": 384,
        "requires_prefix": False,
        "notes": "Good balance of speed and quality",
    },
    "intfloat/e5-base-v2": {
        "dimensions": 768,
        "max_seq_length": 512,
        "requires_prefix": True,
        "query_prefix": "query: ",
        "document_prefix": "passage: ",
        "notes": "Strong retrieval performance",
    },
}

# Shortcuts for common models
MODEL_ALIASES = {
    "bge-base": "BAAI/bge-base-en-v1.5",
    "bge-small": "BAAI/bge-small-en-v1.5",
    "e5-base": "intfloat/e5-base-v2",
    "minilm": "sentence-transformers/all-MiniLM-L6-v2",
    "mpnet": "sentence-transformers/all-mpnet-base-v2",
}


class SentenceTransformerEmbedding:
    """
    Open-source embedding model adapter using sentence-transformers.

    Key advantages:
    - Free to use (no API costs)
    - Run locally (data privacy)
    - No rate limits

    Example:
        ```python
        # Using model alias
        embedding = SentenceTransformerEmbedding(model="bge-base")

        # Using full model name
        embedding = SentenceTransformerEmbedding(
            model="BAAI/bge-base-en-v1.5"
        )

        # Embed texts
        vectors = embedding.embed_texts(["Hello world"])

        # For retrieval with proper prefixes
        doc_vectors = embedding.embed_documents(documents)
        query_vector = embedding.embed_query("search query")
        ```
    """

    def __init__(
        self,
        model: str = "bge-base",
        device: str | None = None,
        normalize_embeddings: bool = True,
        trust_remote_code: bool = True,
        show_progress_bar: bool = False,
    ):
        """
        Initialize sentence-transformers embedding model.

        Args:
            model: Model name or alias (see MODEL_ALIASES)
            device: Device to run on ("cuda", "cpu", "mps", or None for auto)
            normalize_embeddings: Whether to L2-normalize embeddings
            trust_remote_code: Allow models with custom code
            show_progress_bar: Show progress during batch encoding
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers package required. Install with: pip install sentence-transformers"
            ) from None

        # Resolve alias
        self._model_name = MODEL_ALIASES.get(model, model)

        # Get model config if known
        self._config = POPULAR_MODELS.get(self._model_name, {})

        self._normalize = normalize_embeddings
        self._show_progress = show_progress_bar

        # Load model
        logger.info(f"Loading model: {self._model_name}")
        self._model = SentenceTransformer(
            self._model_name,
            device=device,
            trust_remote_code=trust_remote_code,
        )

        # Get actual dimensions from model
        self._dimensions = self._model.get_sentence_embedding_dimension()

        logger.info(
            f"Loaded {self._model_name}: {self._dimensions} dims, "
            f"max_seq_length={self._model.max_seq_length}"
        )

    @property
    def model_name(self) -> str:
        """Return the model name."""
        return self._model_name

    @property
    def dimensions(self) -> int:
        """Return the embedding dimensions."""
        return self._dimensions

    @property
    def max_seq_length(self) -> int:
        """Return maximum sequence length."""
        return self._model.max_seq_length

    @property
    def requires_prefix(self) -> bool:
        """Whether this model requires query/document prefixes."""
        return self._config.get("requires_prefix", False)

    def _add_prefix(
        self,
        texts: list[str],
        input_type: Literal["query", "document"] | None = None,
    ) -> list[str]:
        """Add appropriate prefix for models that require it."""
        if not self.requires_prefix or input_type is None:
            return texts

        if input_type == "query":
            prefix = self._config.get("query_prefix", "")
        else:
            prefix = self._config.get("document_prefix", "")

        if prefix:
            return [prefix + text for text in texts]
        return texts

    def embed_texts(
        self,
        texts: list[str],
        input_type: Literal["query", "document"] | None = None,
        batch_size: int = 32,
    ) -> list[list[float]]:
        """
        Embed a list of texts.

        Args:
            texts: List of texts to embed
            input_type: "query" or "document" for models requiring prefixes
            batch_size: Batch size for encoding

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        processed_texts = self._add_prefix(texts, input_type)

        embeddings = self._model.encode(
            processed_texts,
            batch_size=batch_size,
            normalize_embeddings=self._normalize,
            show_progress_bar=self._show_progress,
            convert_to_numpy=True,
        )

        return embeddings.tolist()

    def embed_text(self, text: str) -> list[float]:
        """Embed a single text."""
        return self.embed_texts([text])[0]

    def embed_query(self, query: str) -> list[float]:
        """
        Embed a query (adds query prefix for models that require it).
        """
        embeddings = self.embed_texts([query], input_type="query")
        return embeddings[0]

    def embed_documents(
        self,
        documents: list[str],
        batch_size: int = 32,
    ) -> list[list[float]]:
        """
        Embed documents for storage (adds document prefix if required).
        """
        return self.embed_texts(documents, input_type="document", batch_size=batch_size)


def list_models() -> dict[str, dict[str, Any]]:
    """Get information about available embedding models."""
    return POPULAR_MODELS.copy()


def get_model_info(model: str) -> dict[str, Any] | None:
    """Get information about a specific model."""
    model_name = MODEL_ALIASES.get(model, model)
    return POPULAR_MODELS.get(model_name)
