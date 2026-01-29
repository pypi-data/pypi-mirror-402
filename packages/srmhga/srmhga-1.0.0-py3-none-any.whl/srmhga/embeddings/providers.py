"""Built-in embedding provider implementations.

The default production-friendly provider is SentenceTransformerProvider
(when `sentence-transformers` is available). For unit tests and minimal
installations, HashEmbeddingProvider provides deterministic lightweight
vectors without external dependencies.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .base import EmbeddingProvider


@dataclass(slots=True)
class HashEmbeddingProvider(EmbeddingProvider):
    """A tiny deterministic embedder for tests.

    **Not semantic.** Converts text to a pseudo-random vector using SHA-256.
    """

    dim: int = 384

    def embed_texts(self, texts: Sequence[str]) -> np.ndarray:
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, t in enumerate(texts):
            h = hashlib.sha256(t.encode("utf-8")).digest()
            # Expand bytes to floats deterministically
            arr = np.frombuffer(h * ((self.dim * 4) // len(h) + 1), dtype=np.uint8)
            arr = arr[: self.dim * 4].astype(np.float32)
            arr = arr.reshape(self.dim, 4).mean(axis=1)
            # normalize to unit-ish scale
            arr = (arr - arr.mean()) / (arr.std() + 1e-6)
            out[i] = arr
        return out


@dataclass(slots=True)
class SentenceTransformerProvider(EmbeddingProvider):
    """Sentence-Transformers provider.

    Requires: `pip install srmhga[sentence-transformers]`
    """

    model_name: str = "all-MiniLM-L6-v2"
    device: str | None = None

    def __post_init__(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except Exception as e:  # pragma: no cover
            raise ImportError(
                "SentenceTransformerProvider requires `sentence-transformers`. "
                "Install with: pip install srmhga[sentence-transformers]"
            ) from e
        self._model = SentenceTransformer(self.model_name, device=self.device)

    @property
    def dim(self) -> int:
        return int(getattr(self._model, "get_sentence_embedding_dimension")())

    def embed_texts(self, texts: Sequence[str]) -> np.ndarray:
        vecs = self._model.encode(list(texts), normalize_embeddings=True)
        return np.asarray(vecs, dtype=np.float32)
