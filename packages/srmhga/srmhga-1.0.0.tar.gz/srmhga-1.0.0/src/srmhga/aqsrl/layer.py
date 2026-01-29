"""AQSRL (Adaptive Quantized Semantic Routing Layer).

This layer provides fast semantic routing using a vector-quantized codebook.
In this implementation, SRM-HGA uses the vendored SRM library as the routing
engine and stores only lightweight `MemoryItem` objects.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from srmem import SemanticRoutingMemory, SRMConfig

from ..core.types import MemoryItem, VaultPointer
from ..core.exceptions import ValidationError
from ..embeddings.base import EmbeddingProvider

from .config import AQSRLConfig


@dataclass(slots=True)
class RouteDiagnostics:
    """Diagnostics returned by a route operation."""

    qerr: float
    conf: float
    margin: float
    best_centroid: int
    second_centroid: int
    probed_centroids: List[int]
    n_candidates: int


class AQSRL:
    """L1 routing layer.

    Notes
    -----
    - Sensitive payloads are NOT stored in L1.
    - L1 stores only routing codes and minimal metadata (MemoryItem).
    """

    def __init__(self, *, embedder: EmbeddingProvider, cfg: AQSRLConfig | None = None):
        self.embedder = embedder
        self.cfg = cfg or AQSRLConfig()

        if self.cfg.K < 2:
            raise ValidationError("AQSRL K must be >= 2")
        if self.cfg.m <= 0 or self.cfg.m > self.cfg.K:
            raise ValidationError("AQSRL m must be in [1,K]")

        srm_cfg = SRMConfig(
            d=self.embedder.dim,
            K=self.cfg.K,
            m=self.cfg.m,
            top_k=self.cfg.top_k,
            max_candidates=self.cfg.max_candidates,
            pre_normalize=bool(self.cfg.pre_normalize),
            rerank_metric="cosine" if self.cfg.rerank_metric == "cosine" else "dot",
            store_item_embeddings=False,
            store_payloads=False,
            adaptive_update=bool(self.cfg.adaptive_update),
            tau=float(self.cfg.tau),
            eta=float(self.cfg.eta),
            seed=int(self.cfg.seed),
        )
        self._srm = SemanticRoutingMemory(srm_cfg)
        self._items: Dict[str, MemoryItem] = {}

        # Bootstrap buffer until we can fit a codebook
        self._pending_ids: List[str] = []
        self._pending_embs: List[np.ndarray] = []

    @property
    def is_ready(self) -> bool:
        return self._srm.codebook is not None

    @property
    def size(self) -> int:
        return len(self._items)

    def warmup_fit(self, X_train: np.ndarray, *, init: str = "kmeans++", n_iter: int = 25) -> None:
        """Fit the codebook from training vectors."""
        self._srm.fit_codebook(X_train, init=init, n_iter=n_iter)

        # Flush pending
        if self._pending_ids:
            X = np.vstack(self._pending_embs).astype(np.float32, copy=False)
            ids = list(self._pending_ids)
            self._pending_ids.clear()
            self._pending_embs.clear()
            codes = self._add_embeddings(X, ids)
            # Update stored MemoryItem codes
            for _id, code in zip(ids, codes):
                self._items[_id] = self._items[_id].with_updates(code=int(code))

    def _add_embeddings(self, X: np.ndarray, ids: Sequence[str]) -> np.ndarray:
        idxs = self._srm.add_items(X, ids=ids)
        # Determine codes: SRM does not return codes, so compute quickly
        # by assigning via nearest centroid for each X.
        codes, _ = self._quantize(X)
        return codes

    def write(self, *, item: MemoryItem, embedding: np.ndarray) -> None:
        """Write an already-embedded MemoryItem into L1."""
        if item.id in self._items:
            raise ValidationError(f"Duplicate MemoryItem id: {item.id}")

        self._items[item.id] = item

        if not self.is_ready:
            self._pending_ids.append(item.id)
            self._pending_embs.append(np.asarray(embedding, dtype=np.float32))
            if len(self._pending_ids) >= self.cfg.resolved_bootstrap_min_items():
                X_train = np.vstack(self._pending_embs)
                self.warmup_fit(X_train)
            return

        codes = self._add_embeddings(np.asarray(embedding, dtype=np.float32)[None, :], [item.id])
        self._items[item.id] = item.with_updates(code=int(codes[0]))

    def write_text(
        self,
        *,
        item_id: str,
        text: str,
        ptr: VaultPointer | None = None,
        summary: str | None = None,
        meta_kwargs: dict | None = None,
    ) -> MemoryItem:
        """Embed text and write a memory item."""
        meta_kwargs = meta_kwargs or {}
        from ..core.types import MemoryMetadata

        meta = MemoryMetadata(**meta_kwargs)
        item = MemoryItem(id=item_id, code=0, ptr=ptr, meta=meta, summary=summary)
        emb = self.embedder.embed_text(text)
        self.write(item=item, embedding=emb)
        return self._items[item_id]

    def get(self, item_id: str) -> MemoryItem | None:
        return self._items.get(item_id)

    def delete(self, item_id: str) -> bool:
        """Delete by tombstoning from L1.

        SRM v1.0.0 does not support physical delete from buckets; we remove from
        the in-memory map and let retrieval filter results.
        """
        return self._items.pop(item_id, None) is not None

    def route(self, query: str, *, top_k: Optional[int] = None, m: Optional[int] = None) -> Tuple[List[MemoryItem], RouteDiagnostics]:
        """Route a query to candidate memory items.

        Returns
        -------
        (items, diagnostics)
        """
        if not self.is_ready:
            return [], RouteDiagnostics(
                qerr=float("inf"),
                conf=0.0,
                margin=0.0,
                best_centroid=-1,
                second_centroid=-1,
                probed_centroids=[],
                n_candidates=0,
            )

        x = self.embedder.embed_text(query)
        qerr, conf, margin, best, second = self._confidence_metrics(x)

        res = self._srm.query(x, top_k=top_k or self.cfg.top_k, m=m or self.cfg.m, max_candidates=self.cfg.max_candidates)
        ids: List[str] = list(res.get("ids") or [])
        items: List[MemoryItem] = [self._items[i] for i in ids if i in self._items]

        diag = RouteDiagnostics(
            qerr=qerr,
            conf=conf,
            margin=margin,
            best_centroid=best,
            second_centroid=second,
            probed_centroids=list(res.get("probed_centroids") or []),
            n_candidates=int(res.get("n_candidates") or 0),
        )
        return items, diag

    def _quantize(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        cb = self._srm.codebook
        if cb is None:
            raise RuntimeError("Codebook not fitted")
        X = np.asarray(X, dtype=np.float32)
        if X.ndim == 1:
            X = X[None, :]
        if self.cfg.pre_normalize:
            X = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-12)
        # squared L2
        dist2 = np.sum((X[:, None, :] - cb[None, :, :]) ** 2, axis=2)
        codes = np.argmin(dist2, axis=1)
        mins = dist2[np.arange(dist2.shape[0]), codes]
        return codes.astype(np.int64), mins.astype(np.float32)

    def _confidence_metrics(self, x: np.ndarray) -> Tuple[float, float, float, int, int]:
        cb = self._srm.codebook
        if cb is None:
            return float("inf"), 0.0, 0.0, -1, -1
        v = np.asarray(x, dtype=np.float32)
        if v.ndim != 1:
            raise ValidationError("Query embedding must be 1D")
        if self.cfg.pre_normalize:
            v = v / (np.linalg.norm(v) + 1e-12)
        dist2 = np.sum((cb - v[None, :]) ** 2, axis=1)
        order = np.argsort(dist2)
        best = int(order[0])
        second = int(order[1]) if len(order) > 1 else best
        d1 = float(dist2[best])
        d2 = float(dist2[second]) if len(order) > 1 else float("inf")
        margin = float(max(d2 - d1, 0.0))
        conf = float(1.0 / (1.0 + d1))
        return d1, conf, margin, best, second
