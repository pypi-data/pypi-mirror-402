"""L1: Adaptive Quantized Semantic Routing Layer (AQSRL).

This implementation wraps the vendored SRM (SemanticRoutingMemory) to provide:
- Multi-probe routing (top-m centroids)
- Confidence and margin metrics (conf, Δ)
- Optional online centroid adaptation (EMA)

AQSRL deliberately avoids storing sensitive payloads.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from srmem import SemanticRoutingMemory, SRMConfig

from ..core.types import MemoryItem, MemoryMetadata, VaultPointer
from ..core.exceptions import ValidationError
from ..embeddings.base import EmbeddingProvider
from .config import AQSRLConfig


@dataclass(slots=True)
class AQSRLRouteDiagnostics:
    """Diagnostics for a routing decision."""

    conf: float
    qerr: float
    margin: float
    probed_centroids: list[int]
    n_candidates: int


class AQSRL:
    """AQSRL index.

    Notes
    -----
    - If the codebook is not fitted, writes are buffered until enough items
      are collected to fit a codebook.
    """

    def __init__(
        self,
        embedder: EmbeddingProvider,
        cfg: AQSRLConfig | None = None,
    ) -> None:
        self.embedder = embedder
        self.cfg = cfg or AQSRLConfig(K=256, m=8)

        if self.cfg.K < 2:
            raise ValidationError("AQSRLConfig.K must be >= 2")
        if self.cfg.m <= 0:
            raise ValidationError("AQSRLConfig.m must be >= 1")

        # If m > K, clamp to K (common in unit tests/small-K configs).
        m_eff = min(self.cfg.m, self.cfg.K)

        self._srm = SemanticRoutingMemory(
            SRMConfig(
                d=self.embedder.dim,
                K=self.cfg.K,
                m=m_eff,
                top_k=self.cfg.top_k,
                max_candidates=self.cfg.max_candidates,
                pre_normalize=self.cfg.pre_normalize,
                rerank_metric=("cosine" if self.cfg.rerank_metric == "cosine" else "dot"),
                store_item_embeddings=False,
                store_payloads=False,
                adaptive_update=self.cfg.adaptive_update,
                tau=self.cfg.tau,
                eta=self.cfg.eta,
                seed=self.cfg.seed,
            )
        )

        # L1 item registry (id -> MemoryItem). SRM stores the bucket membership.
        self._items: Dict[str, MemoryItem] = {}

        # Bootstrap buffer before codebook fit
        self._boot_X: List[np.ndarray] = []
        self._boot_items: List[MemoryItem] = []

    @property
    def codebook_fitted(self) -> bool:
        return self._srm.codebook is not None

    @property
    def size(self) -> int:
        return len(self._items)

    def _maybe_fit_codebook(self) -> None:
        if self.codebook_fitted:
            return
        need = self.cfg.resolved_bootstrap_min_items()
        if len(self._boot_items) < need:
            return
        X = np.vstack(self._boot_X).astype(np.float32, copy=False)
        # Fit SRM codebook, then add buffered items.
        self._srm.fit_codebook(X_train=X, n_iter=25, init="kmeans++", verbose=False)
        ids = [it.id for it in self._boot_items]
        self._srm.add_items(X_items=X, ids=ids, payloads=None)
        for it, vec in zip(self._boot_items, X):
            code, _, _ = self._quant_metrics(vec)
            updated = it.with_updates(code=int(code))
            self._items[updated.id] = updated
        self._boot_X.clear()
        self._boot_items.clear()

    def write_semantic(
        self,
        *,
        item_id: str,
        text: str,
        ptr: VaultPointer | None = None,
        meta: MemoryMetadata | None = None,
        summary: str | None = None,
    ) -> MemoryItem:
        """Write a semantic item into L1.

        Parameters
        ----------
        item_id:
            Unique id.
        text:
            Text to embed and route.
        ptr:
            Optional pointer to DV.
        meta:
            Memory metadata.
        summary:
            Optional short proposition/summary.
        """
        if not item_id:
            raise ValidationError("item_id must be non-empty")
        if item_id in self._items:
            raise ValidationError(f"Duplicate L1 item id: {item_id}")

        meta = meta or MemoryMetadata()
        X = self.embedder.embed_text(text)

        # Buffer until codebook is fitted
        if not self.codebook_fitted:
            it = MemoryItem(id=item_id, code=0, ptr=ptr, meta=meta, summary=summary)
            self._boot_items.append(it)
            self._boot_X.append(np.asarray(X, dtype=np.float32)[None, :])
            self._maybe_fit_codebook()
            return it

        # Add to SRM (routing buckets)
        self._srm.add_items(X_items=X[None, :], ids=[item_id], payloads=None)

        # Compute routing code for item (best centroid)
        code, _, _ = self._quant_metrics(X)
        it = MemoryItem(id=item_id, code=int(code), ptr=ptr, meta=meta, summary=summary)
        self._items[item_id] = it
        return it

    def delete(self, item_id: str) -> bool:
        """Delete a semantic item.

        Note: the vendored SRM does not support true deletions. We keep a
        tombstone in the registry and filter at read time.
        """
        return self._items.pop(item_id, None) is not None

    def _quant_metrics(self, x: np.ndarray) -> Tuple[int, float, float]:
        """Compute best code, qerr and margin for a single vector."""
        if self._srm.codebook is None:
            return 0, float("inf"), 0.0
        cb = self._srm.codebook.astype(np.float32, copy=False)

        xq = np.asarray(x, dtype=np.float32)
        if xq.ndim != 1 or xq.shape[0] != cb.shape[1]:
            raise ValidationError("Embedding dimension mismatch")

        if self.cfg.pre_normalize:
            n = float(np.linalg.norm(xq) + 1e-12)
            xq = xq / n

        # Squared L2 distances, O(K*d) and K is typically small (256)
        dif = cb - xq[None, :]
        dist2 = np.sum(dif * dif, axis=1)
        best = int(np.argmin(dist2))
        d1 = float(dist2[best])
        # second best
        if dist2.size >= 2:
            d2 = float(np.partition(dist2, 1)[1])
        else:
            d2 = d1
        margin = float(max(0.0, d2 - d1))
        return best, d1, margin

    def route(
        self,
        query: str,
        *,
        top_k: int | None = None,
        m: int | None = None,
        max_candidates: int | None = None,
    ) -> Tuple[List[MemoryItem], AQSRLRouteDiagnostics]:
        """Route a query and return candidate items plus diagnostics."""
        if not self.codebook_fitted:
            return [], AQSRLRouteDiagnostics(conf=0.0, qerr=float("inf"), margin=0.0, probed_centroids=[], n_candidates=0)

        Xq = self.embedder.embed_text(query)
        code, qerr, margin = self._quant_metrics(Xq)
        conf = float(1.0 / (1.0 + qerr))

        res = self._srm.query(
            Xq,
            top_k=top_k or self.cfg.top_k,
            m=m or self.cfg.m,
            max_candidates=max_candidates or self.cfg.max_candidates,
            return_payloads=False,
            return_embeddings=False,
        )

        ids = [str(i) for i in (res.get("ids") or [])]
        items: List[MemoryItem] = []
        for _id in ids:
            it = self._items.get(_id)
            if it is not None:
                it.meta.touch_access()
                items.append(it)

        diags = AQSRLRouteDiagnostics(
            conf=conf,
            qerr=float(qerr),
            margin=float(margin),
            probed_centroids=[int(c) for c in (res.get("probed_centroids") or [])],
            n_candidates=int(res.get("n_candidates") or 0),
        )
        return items, diags

    def export_state(self) -> Dict[str, Any]:
        """Export a minimal state snapshot.

        This is intended for observability or debugging, not as a stable
        serialization format.
        """
        return {
            "size": self.size,
            "codebook_fitted": self.codebook_fitted,
            "K": self.cfg.K,
            "m": self.cfg.m,
            "top_k": self.cfg.top_k,
        }
