# ADR-009: B2 Lifecycle Rules + Per-Artifact Integrity Hashes
**Status:** Accepted (implemented in v1.7.0 WS-3) | **Date:** 2026-06-30

## Decision
1. Apply a **B2 Lifecycle Rule** that retains demo/session artifacts for a bounded window
   (e.g. `keep last version, hide after 30 days, delete after 37`) to control storage cost.
2. Record a **SHA-256 per stored artifact** in `generation.json` (extending the existing
   prompt-hash pattern) so the manifest is independently verifiable.

## Rationale
- Demonstrates production-grade B2 *data orchestration* beyond plain uploads — lifecycle and
  integrity are exactly the operational concerns the B2 criterion rewards.
- Integrity hashes make the provenance trail tamper-evident and let the share page / ZIP verify
  what it serves; cheap to compute (we already hash prompts).
- Bounded retention keeps storage near-zero for a hackathon while showing cost-awareness.

## Consequences / risks
- Lifecycle is a bucket-level config (documented + scripted via B2 API / console), not app code —
  capture it as `infra/b2-lifecycle.json` so it's reproducible and visible to judges.
- Hashing adds a few ms per artifact (in-memory bytes already on hand) — negligible.
- A pinned demo session must be **excluded** from auto-delete before judging (separate prefix or
  a longer rule), or the lifecycle window must outlast Aug 3.

## Alternatives considered
- No lifecycle (status quo) — fine for cost at this scale, but misses an easy B2 orchestration win.
- B2 Object Lock / versioning — overkill for a hackathon; note as a production follow-up.
