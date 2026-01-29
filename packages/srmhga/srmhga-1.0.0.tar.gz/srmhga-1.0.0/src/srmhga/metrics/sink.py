"""Observability hooks.

This module provides a lightweight metrics sink interface.
You can plug in Prometheus, OpenTelemetry, or your logging system.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping


class MetricsSink(ABC):
    """Abstract metrics sink."""

    @abstractmethod
    def inc(self, name: str, value: float = 1.0, **labels: str) -> None:
        """Increment a counter."""

    @abstractmethod
    def observe(self, name: str, value: float, **labels: str) -> None:
        """Observe a value (histogram/gauge)."""


class NullMetrics(MetricsSink):
    def inc(self, name: str, value: float = 1.0, **labels: str) -> None:  # pragma: no cover
        return

    def observe(self, name: str, value: float, **labels: str) -> None:  # pragma: no cover
        return
