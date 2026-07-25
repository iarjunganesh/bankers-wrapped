# Hackathon Submission — Backblaze Generative Media Hackathon 2026

> Submission deadline: **August 3, 2026 (5 PM ET)** · Judging: **August 5–11** · Winners: ~August 12
> Required deliverables: working hosted URL + ≤ 3-min demo video (public on YouTube/Vimeo/Youku)
> ⚠️ Per the [official rules](https://backblaze-generative-media.devpost.com/rules), the app must stay
> **live, free, and unrestricted for judges until the Judging Period ends (Aug 11)** — keep Railway,
> Vercel, B2, and all API keys funded through Aug 12 (see [`COSTS.md`](COSTS.md)).
> **Originality:** built new during the Hackathon Submission Period — all B2 + Genblaze
> integration was created within it; no pre-existing codebase was reused.

---

## Judging Alignment

Every cell below carries how to verify it yourself — no claim here should be taken on faith.

| Criterion | How Banker's Wrapped Addresses It | Verify |
| --- | --- | --- |
| **Real-World Utility** | Solves chronically low engagement in banking apps — turns opaque data into a story people want to share. Zero-friction ingestion: **"Connect a bank" via Plaid Sandbox** (ADR-010) or CSV upload. Clear target market: retail banks and fintechs. | Live: click "Connect a bank (sandbox)" on the app, or upload either file in `data/synthetic/` |
| **Production Readiness** | CI/CD with 80%+ coverage gate, structured JSON logging, health endpoint, rate limiting (5 req/hr/IP), binary CSV validation, 11 ADRs (all accepted and implemented), k6 load-test script, synthetic demo data committed. Sessions survive redeploys — B2 is the source of truth (ADR-008), SQLite is a cache. Memory-bounded compositor + non-blocking event loop — battle-tested under a 0.5 GB container. | `uv run pytest tests/ --cov=backend` → **148 passed, 99.61% coverage** (measured 2026-07-25, `coverage.xml`); CI badge in README; `ls docs/adr/*.md` → 11 files |
| **B2 Storage + Orchestration** | **B2 is the source of truth** (ADR-008): share links survive full backend redeploys via the self-contained session manifest + flat `index/` lookup; SQLite is only a read cache. **14 files across 10 artifact types** per session, each with a **SHA-256 in `generation.json`** (ADR-009); a committed **45-day lifecycle rule** (`infra/b2-lifecycle.json`) bounds storage. Presigned URLs regenerated per request; `/download` streams a full ZIP. | `assets/csv-run/` and `assets/plaid-run/` — two full captured sessions (raw B2 JSON + numbered screenshots); or browse the live B2 bucket console directly |
| **Genblaze Usage** | **3 of 4 AI steps route through Genblaze**: images (GMI Cloud Seedream, 5 in parallel), the narrative LLM (GMI Cloud chat with automatic NVIDIA NIM fallback, ADR-007), and narration audio (OpenAI TTS wrapped in `GenblazeClient`). No provider is called directly outside `genblaze_client.py`; per-step provenance incl. tokens + cost recorded in `generation.json`. | `grep -rn "openai\.\|anthropic\." backend/ --include=*.py \| grep -v genblaze_client.py` → no hits; `assets/*/evidence/*_generation.json` → `models_used` block |

---

## Required before submitting

- [x] Working hosted URL — `https://bankers-wrapped.vercel.app` live as of 2026-07-14 (last verified deploy). **Migrating to `https://bankers-wrapped.arjunganesh.dev`** — see the pending-migration note below; do not cite the new domain as live until this line is updated with a verification date.
- [x] `make demo` runs clean on a fresh clone — verified 2026-07-25 against the current dependency lock (`genblaze-core` 0.3.7 / `genblaze-s3` 0.3.6 / `genblaze-gmicloud` 0.3.4)
- [ ] Demo video ≤ 3 min uploaded to YouTube — **public**, no copyrighted music (rules). Shooting script + measured narration ready: [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md)
- [ ] Devpost submission form completed
- [ ] README links to demo video and hosted URL
- [ ] Product feedback filed via [Genblaze GitHub Issues](https://github.com/backblaze-labs/genblaze/issues) — qualifies for one of 10 **Feedback Prizes** (mentorship), winnable in addition to an overall prize
- [ ] App + APIs stay funded and live through **Aug 11** (end of judging) — see [`COSTS.md`](COSTS.md)

## Do not claim until verified

- Do not cite `bankers-wrapped.arjunganesh.dev` as the live app URL anywhere (README, Devpost form,
  video) until it has actually been added in Vercel, DNS has propagated, and a live pipeline run
  has been completed against it — a domain "added" in a dashboard is not the same fact as "live."
- Do not state a test count or coverage percentage without having just run `make test` — both
  numbers move with the codebase and the last-known value goes stale within a session.
- Do not describe the demo video or Devpost form as "complete" based on this document's checklist
  alone — both boxes above are unchecked for a reason; check them only after the artifact exists
  at a real, public URL.
- Do not claim PostgreSQL, MCP, or any integration this repo doesn't implement — see `CLAUDE.md`'s
  "Critical Constraints" for the exhaustive list of what's real vs. documented-as-future-only.

---

## Pipeline Artifacts Stored in B2 (14 files / 10 types per session)

```text
index/{session_id}.json                                ← flat session→user index (ADR-008)
{user_id}/{session_id}/input/transactions.csv
{user_id}/{session_id}/pipeline/script.json            ← 5-scene narrative
{user_id}/{session_id}/pipeline/analytics.json         ← financial insights snapshot
{user_id}/{session_id}/pipeline/prompts.json           ← image prompts + SHA-256 hashes
{user_id}/{session_id}/pipeline/generation.json        ← model, latency, retry per step
{user_id}/{session_id}/pipeline/thumbnail.jpg          ← scene 0 preview image
{user_id}/{session_id}/pipeline/narration.mp3          ← OpenAI TTS via GenblazeClient
{user_id}/{session_id}/pipeline/scenes/scene_00.jpg … scene_04.jpg
{user_id}/{session_id}/output/recap_{session_id}.mp4
{user_id}/{session_id}/metadata/session_metadata.json
```

---

## Demo Script (for video recording)

1. Open `https://bankers-wrapped.vercel.app`
2. Upload `data/synthetic/transactions_jan_2026.csv` (Financial Builder personality)
3. Show the **live 7-step SSE progress** while the 4-agent pipeline runs — per-step latency visible next to each completed stage *(jump-cut the ~2–4 min generation wait)*
4. Play the generated **narrated MP4 recap video** (H.264 + AAC, dip-to-black transitions, OpenAI TTS voice)
5. Click **"Share your recap →"** — open the public share page at `/recap/{session_id}` showing thumbnail + artifact list
6. Click **"Download full package"** — show the ZIP download of all 14 B2 files
7. Open the **B2 bucket** in the Backblaze console — show the 14-file (10-type) structured layout per session
8. Open `generation.json` — show per-step model, latency, retry counts **+ SHA-256 per artifact + the LLM tokens/cost block**; open `session_metadata.json` for the self-contained manifest
9. *(Optional but high-impact)* Trigger a Railway redeploy, reload the share link — **it still works** (B2 is the source of truth)
10. *(Optional)* Click **"Connect a bank (sandbox)"** — Plaid Link → same pipeline, no CSV needed
11. *(Optional)* Repeat with `data/synthetic/transactions_q4_2025.csv` to show a different personality

---

## Submission Links

| | |
| --- | --- |
| **App** | `https://bankers-wrapped.vercel.app` ✅ live (verified 2026-07-14) · migration to `bankers-wrapped.arjunganesh.dev` in progress — not yet verified live |
| **API** | `https://bankers-wrapped-api-production.up.railway.app` ✅ live |
| **Demo Video** | `https://youtu.be/TBD` — not recorded yet |
| **Devpost** | `https://devpost.com/TBD` — not submitted yet |
| **GitHub** | `https://github.com/iarjunganesh/bankers-wrapped` |
