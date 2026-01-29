"""Embedding interfaces.

SRM-HGA uses embeddings for routing and for optional deterministic search.
The library keeps embedding providers pluggable.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

import numpy as np


class EmbeddingProvider(ABC):
    """Abstract embedding provider.

    Implementations must be thread-safe if used in concurrent settings.
    """

    @property
    @abstractmethod
    def dim(self) -> int:
        """Embedding dimension."""

    @abstractmethod
    def embed_texts(self, texts: Sequence[str]) -> np.ndarray:
        """Embed a batch of texts.

        Returns
        -------
        np.ndarray
            Shape (len(texts), dim), dtype float32.
        """

    def embed_text(self, text: str) -> np.ndarray:
        """Embed a single text."""
        X = self.embed_texts([text])
        return X[0]
