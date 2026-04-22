from __future__ import annotations

import hashlib
import logging
import os
from collections.abc import Sequence

from chromadb.api.types import EmbeddingFunction

logger = logging.getLogger("buddy.memory.embeddings")

_VECTOR_SIZE = 384
_REMOTE_EMBEDDING_MODEL = "all-MiniLM-L6-v2"


class LocalDeterministicEmbeddingFunction(EmbeddingFunction[str]):
    """Offline-safe embedding fallback for local development and startup."""

    def __init__(self) -> None:
        pass

    def __call__(self, input: Sequence[str]) -> list[list[float]]:
        return [self._embed_text(text) for text in input]

    def name(self) -> str:
        return "buddy-local-deterministic-v1"

    def _embed_text(self, text: str) -> list[float]:
        vector = [0.0] * _VECTOR_SIZE
        normalized = (text or "").strip().lower()
        if not normalized:
            return vector

        for token in normalized.split():
            token_hash = hashlib.sha256(token.encode("utf-8")).digest()
            for index, byte in enumerate(token_hash):
                slot = (index * 13 + byte) % _VECTOR_SIZE
                vector[slot] += (byte + 1) / 255.0

        norm = sum(value * value for value in vector) ** 0.5
        if norm == 0:
            return vector
        return [value / norm for value in vector]


def get_embedding_function() -> EmbeddingFunction[str]:
    """Return an embedding function that never requires network access by default."""
    mode = os.environ.get("BUDDY_EMBEDDINGS", "local").strip().lower()
    if mode != "sentence-transformer":
        return LocalDeterministicEmbeddingFunction()

    try:
        from chromadb.utils import embedding_functions

        return embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=_REMOTE_EMBEDDING_MODEL
        )
    except Exception as exc:  # pragma: no cover - exercised through import fallback
        logger.warning(
            "Falling back to local embeddings because the sentence-transformer model "
            "could not be initialized: %s",
            exc,
        )
        return LocalDeterministicEmbeddingFunction()
