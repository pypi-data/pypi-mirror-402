# SRM-HGA

SRM-HGA is a production-oriented Python library that implements a **three-layer hybrid memory architecture** for long-lived LLM agents.

- **L1 — AQSRL:** vector-quantized semantic routing (fast path)
- **L2 — DV:** deterministic vault for exact and auditable records
- **L3 — PM:** stable profile memory for user preferences and constraints

This repository vendors a compatible SRM implementation under `src/srm/`.
