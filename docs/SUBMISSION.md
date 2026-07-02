# Hackathon Submission — Backblaze Generative Media Hackathon 2026

> Submission deadline: **August 3, 2026 (5 PM ET)** · Judging: **August 5–11** · Winners: ~August 12
> Required deliverables: working hosted URL + ≤ 3-min demo video (public on YouTube/Vimeo/Youku)
> ⚠️ Per the [official rules](https://backblaze-generative-media.devpost.com/rules), the app must stay
> **live, free, and unrestricted for judges until the Judging Period ends (Aug 11)** — keep Railway,
> Vercel, B2, and all API keys funded through Aug 12 (see [`docs/COSTS.md`](COSTS.md)).

---

## Judging Alignment

| Criterion | How Banker's Wrapped Addresses It |
| --- | --- |
| **Real-World Utility** | Solves chronically low engagement in banking apps — turns opaque data into a story people want to share. Clear target market: retail banks and fintechs. |
| **Production Readiness** | CI/CD with 80%+ coverage gate (currently 93%), structured JSON logging, health endpoint, rate limiting (5 req/hr/IP), binary CSV validation, 10 ADRs (7 accepted), synthetic demo data committed. Sessions survive redeploys — B2 is the source of truth (ADR-008), SQLite is a cache. Memory-bounded compositor + non-blocking event loop — battle-tested under a 0.5 GB container. Not a prototype — a deployable system. |
| **B2 Storage + Orchestration** | B2 stores **14 files across 10 artifact types** per session under `{user_id}/{session_id}/`: input CSV, script, analytics, prompts, generation telemetry, thumbnail, 5 scene images, narration audio, video, and session metadata. All artifact keys returned in API response. Presigned URLs (regenerated per request, never expire) serve video + thumbnail; `/download` endpoint streams a full ZIP. |
| **Genblaze Usage** | Genblaze is the **sole** media generation layer — image generation (GMI Cloud Seedream) and narration audio (OpenAI TTS) both route exclusively through `GenblazeClient`. No provider is called directly outside `genblaze_client.py`. |

---

## Deliverables Checklist

- [x] Working hosted URL (`https://bankers-wrapped.vercel.app`)
- [ ] Demo video ≤ 3 min uploaded to YouTube — **public**, no copyrighted music (rules)
- [ ] Devpost submission form completed
- [ ] README links to demo video and hosted URL
- [ ] `make demo` runs clean on a fresh clone
- [ ] Product feedback filed via [Genblaze GitHub Issues](https://github.com/backblaze-labs/genblaze/issues) — qualifies for one of 10 **Feedback Prizes** (mentorship), winnable in addition to an overall prize
- [ ] App + APIs stay funded and live through **Aug 11** (end of judging) — see [`COSTS.md`](COSTS.md)

---

## Pipeline Artifacts Stored in B2 (14 files / 10 types per session)

```text
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
8. Open `generation.json` — show per-step model, latency, retry counts; open `session_metadata.json` for top-level provenance
9. *(Optional)* Repeat with `data/synthetic/transactions_q4_2025.csv` to show a different personality

---

## Submission Links

| | |
| --- | --- |
| **App** | `https://bankers-wrapped.vercel.app` ✅ live |
| **API** | `https://bankers-wrapped-api-production.up.railway.app` ✅ live |
| **Demo Video** | `https://youtu.be/TBD` |
| **Devpost** | `https://devpost.com/TBD` |
| **GitHub** | `https://github.com/iarjunganesh/bankers-wrapped` |
