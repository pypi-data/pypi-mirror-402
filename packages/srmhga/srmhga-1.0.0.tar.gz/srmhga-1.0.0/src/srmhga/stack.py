"""Top-level SRM-HGA stack.

This module integrates:
- L1 AQSRL (semantic routing)
- L2 Deterministic Vault (exact records)
- L3 Profile Memory
- UBTP triage gate

The default implementation is intentionally conservative: sensitive or uncertain
queries route to the deterministic vault.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional

from .aqsrl.aqsrl import AQSRL, AQSRLRouteDiagnostics
from .aqsrl.config import AQSRLConfig
from .consolidation.pipeline import Consolidator, ConsolidationResult
from .core.config import Config
from .core.exceptions import ValidationError
from .core.types import MemoryItem, MemoryMetadata, Policy, SearchHit, Sensitivity, VaultPointer
from .dv.base import StorageBackend
from .dv.sqlite_vault import SQLiteDeterministicVault
from .embeddings.base import EmbeddingProvider
from .metrics.sink import MetricsSink, NullMetrics
from .pm.profile_memory import ProfileMemory
from .triage.triage import TriageDecision, TriagePath, UBTPGate
from .forgetting.forget import ForgetResult, forget_l1


class ReadMode(str, Enum):
    AUTO = "auto"
    FAST = "fast"
    SAFE = "safe"
    FORCE_DV = "force_dv"


@dataclass(slots=True)
class ReadResult:
    """Result for :meth:`SRMHGA.read`."""

    mode: ReadMode
    path: TriagePath
    decision: TriageDecision
    semantic_items: list[MemoryItem]
    vault_hits: list[SearchHit]
    resolved_records: list[Mapping[str, Any]]
    diagnostics: AQSRLRouteDiagnostics | None = None


class SRMHGA:
    """SRM-HGA orchestrator.

    Parameters
    ----------
    embedder:
        Embedding provider.
    dv:
        Deterministic vault backend.
    pm:
        Profile memory wrapper. If not provided, created using DV.
    aqsrl:
        L1 AQSRL instance. If not provided, created from embedder and `aqsrl_config`.
    config:
        UBTP + budgeting configuration.
    metrics:
        Optional metrics sink.
    """

    def __init__(
        self,
        *,
        embedder: EmbeddingProvider,
        dv: StorageBackend | None = None,
        pm: ProfileMemory | None = None,
        aqsrl: AQSRL | None = None,
        aqsrl_config: AQSRLConfig | None = None,
        config: Config | None = None,
        metrics: MetricsSink | None = None,
    ) -> None:
        self.embedder = embedder
        self.cfg = (config or Config()).validate()
        self.metrics = metrics or NullMetrics()

        self.dv: StorageBackend = dv or SQLiteDeterministicVault(":memory:")
        self.pm = pm or ProfileMemory(self.dv)
        self.aqsrl = aqsrl or AQSRL(self.embedder, aqsrl_config or AQSRLConfig())

        self.ubtp = UBTPGate(self.cfg)
        self.consolidator = Consolidator(dv=self.dv, aqsrl=self.aqsrl, pm=self.pm)

    # -----------------
    # Write API
    # -----------------

    def write_episodic(self, event: str, meta: Mapping[str, Any] | None = None, *, policy: Policy = Policy.AUDITABLE, sensitivity: Sensitivity = Sensitivity.LOW) -> str:
        eid = self.dv.write_episodic(event, meta=meta, policy=policy, sensitivity=sensitivity)
        self.metrics.inc("dv.write_episodic")
        return eid

    def write_fact(self, key: str, value: Any, provenance: Mapping[str, Any] | None = None, *, policy: Policy = Policy.USER_CONFIRMED, sensitivity: Sensitivity = Sensitivity.MEDIUM, also_semantic: bool = True) -> str:
        k = self.dv.write_fact(key, value, provenance=provenance, policy=policy, sensitivity=sensitivity)
        self.metrics.inc("dv.write_fact")

        if also_semantic and sensitivity is not Sensitivity.HIGH:
            # Store a non-sensitive semantic pointer for fast lookup.
            try:
                ptr = VaultPointer(backend="sqlite", namespace="fact", key=str(key))
                meta_l1 = MemoryMetadata(policy=policy, sensitivity=sensitivity, tags=["fact"], importance=0.6)
                text = f"Fact: {key} = {value}"
                self.aqsrl.write_semantic(item_id=f"fact:{key}", text=text, ptr=ptr, meta=meta_l1, summary=str(key))
                self.metrics.inc("l1.write_fact_pointer")
            except Exception:
                pass
        return k

    def write_semantic(self, text: str, links: Mapping[str, Any] | None = None, meta: Mapping[str, Any] | None = None, *, policy: Policy = Policy.NORMAL, sensitivity: Sensitivity = Sensitivity.LOW) -> str:
        """Write a semantic memory.

        For provenance and auditability, the full text is stored in DV as a document
        and L1 only stores a pointer + minimal metadata.
        """
        doc_meta = dict(meta or {})
        if links:
            doc_meta["links"] = dict(links)

        if hasattr(self.dv, "write_document"):
            doc_id = getattr(self.dv, "write_document")(text, meta=doc_meta, policy=policy, sensitivity=sensitivity)
            ref = f"doc:{doc_id}"
        else:
            # Fallback: store as an episodic event
            eid = self.dv.write_episodic(text, meta=doc_meta, policy=policy, sensitivity=sensitivity)
            ref = f"episode:{eid}"

        item_id = f"sem:{uuid.uuid4()}"
        ptr = VaultPointer(backend="sqlite", namespace=ref.split(":", 1)[0], key=ref.split(":", 1)[1])

        tags = doc_meta.get("tags") if isinstance(doc_meta.get("tags"), list) else []
        mm = MemoryMetadata(tags=[str(t) for t in tags], policy=policy, sensitivity=sensitivity, importance=float(doc_meta.get("importance", 0.3)))
        self.aqsrl.write_semantic(item_id=item_id, text=text, ptr=ptr, meta=mm, summary=str(doc_meta.get("summary") or ""))
        self.metrics.inc("l1.write_semantic")
        return item_id

    # -----------------
    # Read API
    # -----------------

    def read(self, query: str, mode: str | ReadMode = ReadMode.AUTO, *, resolve_pointers: bool = True, limit: int = 10) -> ReadResult:
        if not query:
            raise ValidationError("query must be non-empty")
        rmode = ReadMode(mode) if not isinstance(mode, ReadMode) else mode

        if rmode is ReadMode.FORCE_DV or rmode is ReadMode.SAFE:
            hits = self.dv.search(query, limit=limit)
            self.metrics.inc("dv.search", path="deterministic")
            return ReadResult(
                mode=rmode,
                path=TriagePath.DETERMINISTIC,
                decision=self.ubtp.decide(query, conf=0.0, margin=0.0),
                semantic_items=[],
                vault_hits=hits,
                resolved_records=[self.dv.read_exact(h.ref) for h in hits[: min(3, len(hits))]],
                diagnostics=None,
            )

        semantic_items, diags = self.aqsrl.route(query, top_k=limit)
        self.metrics.observe("l1.conf", diags.conf)
        self.metrics.observe("l1.margin", diags.margin)

        decision = self.ubtp.decide(query, conf=diags.conf, margin=diags.margin)

        if rmode is ReadMode.FAST and decision.path is not TriagePath.DETERMINISTIC:
            return self._fast_result(rmode, decision, semantic_items, diags, resolve_pointers=resolve_pointers)

        if decision.path is TriagePath.FAST_SEMANTIC:
            return self._fast_result(rmode, decision, semantic_items, diags, resolve_pointers=resolve_pointers)

        # fallback deterministic
        hits = self.dv.search(query, limit=limit)
        self.metrics.inc("dv.search", path="deterministic")
        return ReadResult(
            mode=rmode,
            path=TriagePath.DETERMINISTIC,
            decision=decision,
            semantic_items=semantic_items,
            vault_hits=hits,
            resolved_records=[self.dv.read_exact(h.ref) for h in hits[: min(3, len(hits))]],
            diagnostics=diags,
        )

    def _fast_result(self, mode: ReadMode, decision: TriageDecision, items: list[MemoryItem], diags: AQSRLRouteDiagnostics, *, resolve_pointers: bool) -> ReadResult:
        self.metrics.inc("read.fast_path")
        recs: list[Mapping[str, Any]] = []
        if resolve_pointers:
            for it in items[:3]:
                if it.ptr is None:
                    continue
                ref = f"{it.ptr.namespace}:{it.ptr.key}"
                try:
                    recs.append(self.dv.read_exact(ref))
                except Exception:
                    continue
        return ReadResult(
            mode=mode,
            path=TriagePath.FAST_SEMANTIC,
            decision=decision,
            semantic_items=items,
            vault_hits=[],
            resolved_records=recs,
            diagnostics=diags,
        )

    # -----------------
    # Maintenance API
    # -----------------

    def consolidate(self, window_seconds: int = 3600) -> ConsolidationResult:
        res = self.consolidator.consolidate(window_seconds=window_seconds)
        self.metrics.inc("consolidation.run")
        self.metrics.observe("consolidation.props_written", float(res.propositions_written))
        return res

    def forget(self, *, budget_hot: int | None = None, budget_dv: int | None = None) -> ForgetResult:
        bh = int(budget_hot if budget_hot is not None else self.cfg.budget_hot)
        res = forget_l1(self.aqsrl, budget_hot=bh)
        self.metrics.inc("forget.l1")
        return res

    def delete(self, scope: str, selector: str) -> bool:
        """Delete items.

        scope: "l1" | "dv" | "all"
        selector: item id for l1, or a DV ref (e.g., "fact:...", "episode:...", "doc:...")
        """
        scope = scope.lower().strip()
        if scope in {"l1", "aqsrl"}:
            return self.aqsrl.delete(selector)
        if scope in {"dv", "vault"}:
            return self.dv.delete(selector)
        if scope == "all":
            ok1 = self.aqsrl.delete(selector)
            ok2 = False
            try:
                ok2 = self.dv.delete(selector)
            except Exception:
                ok2 = False
            return bool(ok1 or ok2)
        raise ValidationError("unknown scope")


class AsyncSRMHGA:
    """Async wrapper around :class:`SRMHGA`.

    This is implemented using `asyncio.to_thread` to keep the core synchronous
    implementation simple and robust.
    """

    def __init__(self, inner: SRMHGA) -> None:
        self.inner = inner

    async def write_episodic(self, *args: Any, **kwargs: Any) -> Any:
        return await asyncio.to_thread(self.inner.write_episodic, *args, **kwargs)

    async def write_fact(self, *args: Any, **kwargs: Any) -> Any:
        return await asyncio.to_thread(self.inner.write_fact, *args, **kwargs)

    async def write_semantic(self, *args: Any, **kwargs: Any) -> Any:
        return await asyncio.to_thread(self.inner.write_semantic, *args, **kwargs)

    async def read(self, *args: Any, **kwargs: Any) -> Any:
        return await asyncio.to_thread(self.inner.read, *args, **kwargs)

    async def consolidate(self, *args: Any, **kwargs: Any) -> Any:
        return await asyncio.to_thread(self.inner.consolidate, *args, **kwargs)

    async def forget(self, *args: Any, **kwargs: Any) -> Any:
        return await asyncio.to_thread(self.inner.forget, *args, **kwargs)

    async def delete(self, *args: Any, **kwargs: Any) -> Any:
        return await asyncio.to_thread(self.inner.delete, *args, **kwargs)
