# ADR-007: Route the Narrative LLM Through Genblaze (Genblaze as Sole AI Layer)
**Status:** Accepted — implemented in v1.7.0 WS-1 (code + tests complete; `NARRATIVE_PROVIDER` defaults to `nvidia-nim` until the GMI credit top-up, then flips to `genblaze` via env var; automatic NIM fallback on invalid JSON or provider failure). The optional video scene (§ below) is **cut for cost** — see docs/COSTS.md. | **Date:** 2026-06-30

## Decision
Route the `NarrativeAgent` LLM call through the Genblaze SDK (GMI Cloud chat/reasoning model)
instead of calling NVIDIA NIM directly. After this, **3 of 4 AI steps** (script + image + audio)
go through Genblaze; only deterministic analytics stays local. Optionally add one Genblaze
**video** scene to demonstrate a third modality.

## Rationale
- Judging scores "Use of Genblaze." Today only image + TTS route through it; the LLM is direct
  NVIDIA NIM, weakening the "sole media/AI layer" claim.
- Genblaze already abstracts retry/backoff and provider-swap — extending it to the LLM keeps
  `generation.json` provenance uniform across every AI step.
- GMI Cloud exposes chat/reasoning + video models; using a second/third modality showcases the
  platform breadth the hackathon explicitly highlights (image, video, audio, chat, reasoning).

## Consequences / risks
- **Costs credits** — gated on the GMI credit top-up.
- Output quality of the GMI chat model for structured 5-scene JSON must be validated against the
  current Llama-3.1-70B output; keep NVIDIA NIM behind a feature flag as a fallback.
- Structured-output reliability (valid JSON) is the main risk — add schema validation + 1 retry.

## Alternatives considered
- Keep NIM direct (status quo) — simplest, but leaves the Genblaze score on the table.
- Wrap NIM inside `GenblazeClient` without changing the provider — cosmetic only; judges can tell.
