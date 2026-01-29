"""
OpenAI Embedding adapter.

Provides integration with OpenAI's text embedding models.
Requires OPENAI_API_KEY environment variable.

Cost: ~$0.02 per 1M tokens for text-embedding-3-small
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


class OpenAIEmbedding:
    """
    OpenAI embedding model adapter.

    Supports text-embedding-3-small, text-embedding-3-large, and text-embedding-ada-002.

    Example:
        ```python
        model = OpenAIEmbedding(model="text-embedding-3-small")
        embedding = model.embed_text("Hello world")
        ```

    Environment:
        OPENAI_API_KEY: Required API key
    """

    MODEL_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        dimensions: int | None = None,
        api_key: str | None = None,
    ):
        """
        Initialize OpenAI embedding model.

        Args:
            model: Model name (text-embedding-3-small, text-embedding-3-large)
            dimensions: Output dimensions (text-embedding-3-* models only)
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package required. Install with: pip install openai") from None

        self._model = model
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")

        if not self._api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )

        if dimensions is not None:
            self._dimensions = dimensions
        else:
            self._dimensions = self.MODEL_DIMENSIONS.get(model, 1536)

        self._client = OpenAI(api_key=self._api_key)

    @property
    def model_name(self) -> str:
        """Full model identifier."""
        return f"openai:{self._model}"

    @property
    def dimensions(self) -> int:
        """Output embedding dimensions."""
        return self._dimensions

    def embed_text(self, text: str) -> list[float]:
        """
        Embed a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Embed multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Handle empty strings
        texts = [t if t else " " for t in texts]

        kwargs = {
            "model": self._model,
            "input": texts,
        }

        # Add dimensions parameter for v3 models
        if self._model.startswith("text-embedding-3"):
            kwargs["dimensions"] = self._dimensions

        response = self._client.embeddings.create(**kwargs)

        # Sort by index to ensure correct order
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return [item.embedding for item in sorted_data]

    def embed_query(self, query: str) -> list[float]:
        """
        Embed a query.

        For OpenAI models, this is identical to embed_text.

        Args:
            query: Query text

        Returns:
            Query embedding vector
        """
        return self.embed_text(query)

    def embed_documents(self, documents: list[str]) -> list[list[float]]:
        """
        Embed documents for storage.

        Args:
            documents: List of document texts

        Returns:
            List of embedding vectors
        """
        return self.embed_texts(documents)
