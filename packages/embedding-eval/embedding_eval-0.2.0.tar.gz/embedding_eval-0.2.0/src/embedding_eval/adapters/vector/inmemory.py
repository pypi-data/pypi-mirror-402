"""
In-Memory Vector Store adapter.

Provides an in-memory implementation of the VectorStore protocol
that requires no external dependencies. Performs real similarity
calculations using brute-force search.
"""

from __future__ import annotations

import math
from typing import Any


class InMemoryVectorStore:
    """
    In-memory implementation of VectorStore protocol.

    Stores vectors in dictionaries and performs brute-force similarity search.
    No external dependencies required - ideal for testing and small datasets.

    Example:
        ```python
        store = InMemoryVectorStore()
        store.connect()
        store.create_collection("test", dimensions=768)
        store.upsert("test", ["id1"], [[0.1, 0.2, ...]], texts=["hello"])
        results = store.search("test", query_embedding, top_k=5)
        ```
    """

    def __init__(self):
        """Initialize empty storage."""
        self._connected = False
        self._collections: dict[str, dict[str, Any]] = {}

    def connect(self) -> None:
        """Establish connection (no-op for in-memory store)."""
        self._connected = True

    def disconnect(self) -> None:
        """Close connection (no-op for in-memory store)."""
        self._connected = False

    def is_connected(self) -> bool:
        """Check if connection is active."""
        return self._connected

    # -------------------------------------------------------------------------
    # Collection Management
    # -------------------------------------------------------------------------

    def create_collection(
        self,
        name: str,
        dimensions: int,
        distance_metric: str = "cosine",
    ) -> bool:
        """Create a new vector collection."""
        if name in self._collections:
            return False

        self._collections[name] = {
            "dimensions": dimensions,
            "distance_metric": distance_metric,
            "vectors": {},  # id -> {"embedding": [...], "metadata": {...}, "text": "..."}
        }
        return True

    def delete_collection(self, name: str) -> bool:
        """Delete a collection."""
        if name not in self._collections:
            return False
        del self._collections[name]
        return True

    def collection_exists(self, name: str) -> bool:
        """Check if collection exists."""
        return name in self._collections

    def list_collections(self) -> list[str]:
        """List all collection names."""
        return list(self._collections.keys())

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
        """Insert or update vectors in a collection."""
        if collection_name not in self._collections:
            raise ValueError(f"Collection {collection_name} does not exist")

        collection = self._collections[collection_name]
        metadata = metadata or [{}] * len(ids)
        texts = texts or [""] * len(ids)

        for i, id_ in enumerate(ids):
            collection["vectors"][id_] = {
                "embedding": embeddings[i],
                "metadata": metadata[i],
                "text": texts[i],
            }

        return len(ids)

    def search(
        self,
        collection_name: str,
        query_embedding: list[float],
        top_k: int = 5,
        filter: dict[str, Any] | None = None,
        include_metadata: bool = True,
        include_embeddings: bool = False,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors."""
        if collection_name not in self._collections:
            raise ValueError(f"Collection {collection_name} does not exist")

        collection = self._collections[collection_name]
        distance_metric = collection["distance_metric"]

        # Calculate similarity scores
        scored_results = []
        for id_, data in collection["vectors"].items():
            # Apply filter if provided
            if filter:
                match = all(data["metadata"].get(k) == v for k, v in filter.items())
                if not match:
                    continue

            score = self._calculate_similarity(
                query_embedding,
                data["embedding"],
                distance_metric,
            )
            scored_results.append((id_, score, data))

        # Sort by score (descending for similarity)
        scored_results.sort(key=lambda x: x[1], reverse=True)

        # Build results
        results = []
        for id_, score, data in scored_results[:top_k]:
            result = {"id": id_, "score": score}
            if include_metadata:
                result["metadata"] = data["metadata"]
                result["text"] = data["text"]
            if include_embeddings:
                result["embedding"] = data["embedding"]
            results.append(result)

        return results

    def delete(
        self,
        collection_name: str,
        ids: list[str] | None = None,
        filter: dict[str, Any] | None = None,
    ) -> int:
        """Delete vectors by ID or filter."""
        if collection_name not in self._collections:
            raise ValueError(f"Collection {collection_name} does not exist")

        collection = self._collections[collection_name]
        deleted = 0

        if ids:
            for id_ in ids:
                if id_ in collection["vectors"]:
                    del collection["vectors"][id_]
                    deleted += 1

        if filter:
            to_delete = []
            for id_, data in collection["vectors"].items():
                match = all(data["metadata"].get(k) == v for k, v in filter.items())
                if match:
                    to_delete.append(id_)
            for id_ in to_delete:
                del collection["vectors"][id_]
                deleted += 1

        return deleted

    def count(self, collection_name: str) -> int:
        """Get number of vectors in collection."""
        if collection_name not in self._collections:
            raise ValueError(f"Collection {collection_name} does not exist")
        return len(self._collections[collection_name]["vectors"])

    def get_by_id(self, collection_name: str, id_: str) -> dict[str, Any] | None:
        """Get a vector by ID."""
        if collection_name not in self._collections:
            raise ValueError(f"Collection {collection_name} does not exist")

        data = self._collections[collection_name]["vectors"].get(id_)
        if data is None:
            return None

        return {
            "id": id_,
            "embedding": data["embedding"],
            "metadata": data["metadata"],
            "text": data["text"],
        }

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    def _calculate_similarity(
        self,
        vec1: list[float],
        vec2: list[float],
        metric: str,
    ) -> float:
        """Calculate similarity between two vectors."""
        if metric == "cosine":
            return self._cosine_similarity(vec1, vec2)
        elif metric == "euclidean":
            dist = self._euclidean_distance(vec1, vec2)
            return 1.0 / (1.0 + dist)
        elif metric == "dot":
            return self._dot_product(vec1, vec2)
        else:
            raise ValueError(f"Unknown distance metric: {metric}")

    @staticmethod
    def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity."""
        dot = sum(a * b for a, b in zip(vec1, vec2, strict=True))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    @staticmethod
    def _euclidean_distance(vec1: list[float], vec2: list[float]) -> float:
        """Calculate Euclidean distance."""
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2, strict=True)))

    @staticmethod
    def _dot_product(vec1: list[float], vec2: list[float]) -> float:
        """Calculate dot product."""
        return sum(a * b for a, b in zip(vec1, vec2, strict=True))
