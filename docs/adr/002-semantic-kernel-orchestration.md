# ADR-002: Lightweight Typed Async Agents (no orchestration framework)
**Status:** Accepted (Semantic Kernel considered, not adopted) | **Date:** 2026-06-25

## Decision
Each agent is a hand-rolled `BaseAgent` (an `ABC`): a typed input → typed output
transformation with a single `async run()` entry point, composed as a plain linear
async pipeline. No external agent-orchestration framework is used.

## Context
Semantic Kernel was initially considered — its plugin contract inspired the typed
input/output shape of `BaseAgent`. LangGraph and CrewAI were also evaluated. None were
adopted; there is no `semantic-kernel` (or other framework) dependency.

## Rationale
- The pipeline is a fixed, linear 4-agent sequence (Document → Analytics → Narrative →
  Media). A framework's routing/planning layer adds dependency weight and cold-start
  cost with no benefit at this scope.
- A plain typed `ABC` keeps every agent trivially unit-testable (all providers mocked)
  and keeps the dependency surface minimal — a production-readiness win.
- Zero cold-start and no framework version lock-in vs LangGraph / CrewAI / Semantic Kernel.

## Consequences
- Orchestration is ~40 lines in [`backend/agents/base.py`](../../backend/agents/base.py)
  plus the API layer; no framework to upgrade or pin.
- If dynamic routing or planning is ever needed, revisit adopting a framework.
