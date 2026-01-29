"""Optional LlamaIndex integration.

This is a minimal adapter that exposes SRMHGA as a callable retrieval function.
"""

from __future__ import annotations

from typing import Any, Callable

from ..stack import SRMHGA


def as_llamaindex_retriever(hga: SRMHGA) -> Callable[[str], list[str]]:
    """Return a callable retriever function usable in LlamaIndex pipelines."""

    def _retrieve(query: str) -> list[str]:
        res = hga.read(query, mode="auto", resolve_pointers=True, limit=5)
        chunks: list[str] = []
        for rec in res.resolved_records:
            if rec.get("kind") == "fact":
                chunks.append(f"{rec.get('key')}: {rec.get('value')}")
            elif rec.get("kind") == "episode":
                chunks.append(str(rec.get("event")))
            elif rec.get("kind") == "doc":
                chunks.append(str(rec.get("content")))
        return chunks

    return _retrieve
