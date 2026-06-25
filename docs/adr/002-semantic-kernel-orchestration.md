# ADR-002: Semantic Kernel for Agent Orchestration
**Status:** Accepted | **Date:** 2026-06-25

## Decision
Each agent implements the BaseAgent contract (SK Plugin-compatible).

## Rationale
- Proven in ARGUS hackathon project
- Typed plugin contracts, native async, Azure OpenAI first-class
- Zero cold-start vs LangGraph/CrewAI
