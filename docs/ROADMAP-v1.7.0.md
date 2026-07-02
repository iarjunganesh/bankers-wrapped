# Roadmap — v1.7.0 ("Push to >9.5 across all judging criteria")

> **Status:** Planned (no code yet) · **Target window:** 2026-06-30 → 2026-08-03 (judging)
> **Goal:** lift every judging criterion from its current honest estimate toward >9.5.
> **Hard constraints:** ~1 month, GMI Cloud credits capped at a **one-time $10 top-up** (≈ $0.15–0.25
> per full pipeline run at 5 Seedream images; LLM chat is pennies — the optional video scene is the
> only real credit risk and is cut), Railway Hobby (8 GB).

This document is the master plan. Each workstream has a decision record (ADR) and a build
spec (prompt). **Nothing here is implemented yet** — v1.7.0 ships as the work lands.

---

## Current → target (honest self-assessment)

| Criterion | Now | Target | Primary gap |
| --- | --- | --- | --- |
| Real-World Utility | 7.5 | 9+ | CSV friction; unvalidated; generic advice |
| Production Readiness | 8.5 | 9.5 | Ephemeral sessions; Postgres claim is aspirational; no load test |
| B2 Storage + Orchestration | 8.5 | 9.5 | Rich *output* storage, but no lifecycle / integrity / B2-as-truth |
| Genblaze Usage | 7.5 | 9 | Only 2 of 4 AI steps route through Genblaze (LLM is direct NVIDIA NIM) |

**Cross-cutting lever (affects all four):** the ≤3-min demo video. Judges experience every
criterion through it — it is the single highest-ROI deliverable and is owned by the human.

---

## Workstreams

| WS | Name | Lifts | Credits? | ADR | Prompt |
| --- | --- | --- | --- | --- | --- |
| WS-1 | Genblaze LLM routing (narrative via Genblaze) | Genblaze | **Yes** | [007](adr/007-genblaze-sole-ai-layer.md) | [12](../.github/prompts/12.Genblaze%20LLM%20Routing%20(Narrative%20via%20Genblaze).md) |
| WS-2 | B2 as source of truth (durable sessions) | B2 + Production | No | [008](adr/008-b2-source-of-truth.md) | [13](../.github/prompts/13.B2%20as%20Source%20of%20Truth%20(Durable%20Sessions).md) |
| WS-3 | B2 lifecycle rules + artifact integrity | B2 | No | [009](adr/009-b2-lifecycle-integrity.md) | [14](../.github/prompts/14.B2%20Lifecycle%20Rules%20+%20Artifact%20Integrity.md) |
| WS-4 | Plaid sandbox connector (kill CSV friction) | Utility | No | [010](adr/010-plaid-sandbox-ingestion.md) | [15](../.github/prompts/15.Plaid%20Sandbox%20Connector.md) |
| WS-5 | Submission polish + production hardening++ | All | Minimal | — | [16](../.github/prompts/16.Submission%20Polish%20+%20Production%20Hardening.md) |

---

## Prioritized sequence (1 month, credit-aware)

1. **WS-2 — B2 as source of truth** *(free, this week)* — biggest two-for-one: deepens B2
   orchestration **and** fixes the session-persistence gap (share links survive any redeploy).
2. **WS-3 — B2 lifecycle + integrity** *(free)* — auto-expire old sessions, SHA-256 per artifact.
3. **WS-5 — hardening++ & submission polish** *(free)* — k6 load test, `/security-review`,
   green CI badge, 7th-ADR provenance, demo-video script, testimonials, market stat.
4. **WS-4 — Plaid sandbox** *(free; Plaid sandbox is no-cost)* — reframes "export a CSV" into
   "connect any bank, zero setup."
5. **WS-1 — Genblaze LLM routing** *(needs the credit top-up)* — route the narrative LLM through
   Genblaze so **3 of 4** AI steps go through it; optionally add one Genblaze video scene.

WS-1 is gated on credits; everything else is free and can start immediately.

---

## Out of scope for v1.7.0

- Multi-period (monthly/quarterly) recaps — post-hackathon.
- Real bank production integration (only Plaid **sandbox** in scope).
- OpenTelemetry / distributed tracing (see ADR-006 — still out of scope).
- White-label embedding — listed under "what's next," not built.

---

## Definition of done (v1.7.0)

- Share page + notebook Scenario C survive a Railway redeploy (B2-backed).
- B2 lifecycle rule documented + applied; every artifact carries a SHA-256 in `generation.json`.
- ≥3 of 4 AI steps route through Genblaze (or a documented, honest reason if WS-1 is deferred).
- Plaid sandbox path demoable (or cleanly behind a flag if deferred).
- Load test + security review committed; CI badge green in README.
- All docs (README, SUBMISSION, DEVPOST, CLAUDE) consistent with shipped reality.
- Coverage gate still ≥80% (target: hold ~93%).
