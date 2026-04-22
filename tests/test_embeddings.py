from __future__ import annotations

import importlib

from memory.embeddings import LocalDeterministicEmbeddingFunction


def test_local_embedding_function_is_deterministic():
    embedding_function = LocalDeterministicEmbeddingFunction()

    first = embedding_function(["launch chrome"])
    second = embedding_function(["launch chrome"])

    assert first[0].tolist() == second[0].tolist()
    assert len(first[0]) == 384


def test_memory_manager_uses_offline_safe_embeddings_by_default(monkeypatch):
    monkeypatch.delenv("BUDDY_EMBEDDINGS", raising=False)

    module = importlib.import_module("memory.memory_manager")
    module = importlib.reload(module)

    assert isinstance(module.embedding_func, LocalDeterministicEmbeddingFunction)
