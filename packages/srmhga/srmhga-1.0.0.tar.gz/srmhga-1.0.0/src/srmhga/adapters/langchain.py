"""Optional LangChain integration.

This module avoids importing LangChain at import time.
"""

from __future__ import annotations

from typing import Any

from ..stack import SRMHGA


def as_langchain_memory(hga: SRMHGA) -> Any:
    """Return a LangChain BaseMemory adapter.

    This function requires `langchain` to be installed.
    """
    try:
        from langchain.memory import BaseMemory  # type: ignore
    except Exception as e:  # pragma: no cover
        raise ImportError("langchain is not installed") from e

    class SRMHGAMemory(BaseMemory):  # type: ignore
        @property
        def memory_variables(self) -> list[str]:
            return ["srmhga_context"]

        def load_memory_variables(self, inputs: dict[str, Any]) -> dict[str, Any]:
            q = inputs.get("input") or inputs.get("query") or ""
            if not q:
                return {"srmhga_context": ""}
            res = hga.read(str(q), mode="auto", resolve_pointers=True, limit=5)
            # Lightweight textual context
            lines: list[str] = []
            for rec in res.resolved_records:
                if rec.get("kind") == "fact":
                    lines.append(f"{rec.get('key')}: {rec.get('value')}")
                elif rec.get("kind") == "episode":
                    lines.append(str(rec.get("event")))
                elif rec.get("kind") == "doc":
                    lines.append(str(rec.get("content")))
            return {"srmhga_context": "\n".join(lines)}

        def save_context(self, inputs: dict[str, Any], outputs: dict[str, Any]) -> None:
            # Store the interaction as episodic memory.
            hga.write_episodic({"inputs": inputs, "outputs": outputs}.__repr__())

        def clear(self) -> None:
            # No-op by default.
            return

    return SRMHGAMemory()
