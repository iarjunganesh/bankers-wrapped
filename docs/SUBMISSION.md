# Hackathon Submission — Backblaze Generative Media Hackathon 2026

> Submission deadline: **August 3, 2026**
> Required deliverables: working hosted URL + ≤ 3-min demo video

---

## Judging Alignment

| Criterion | How Banker's Wrapped Addresses It |
| --- | --- |
| **Real-World Utility** | Solves chronically low engagement in banking apps — turns opaque data into a story people want to share. Clear target market: retail banks and fintechs. |
| **Production Readiness** | CI/CD with 80%+ coverage gate (currently 94%), structured JSON logging, health endpoint, rate limiting (5 req/hr/IP), binary CSV validation, 6 ADRs, synthetic demo data committed. Not a prototype — a deployable system. |
| **B2 Storage + Orchestration** | B2 stores all **10 artifact types** per session under `{user_id}/{session_id}/`: input CSV, script, analytics, prompts, generation telemetry, thumbnail, 5 scene images, narration audio, video, and session metadata. All artifact keys returned in API response. Presigned URLs serve video + thumbnail; `/download` endpoint streams a full ZIP. |
| **Genblaze Usage** | Genblaze is the **sole** media generation layer — image generation (GMI Cloud Seedream) and narration audio (OpenAI TTS) both route exclusively through `GenblazeClient`. No provider is called directly outside `genblaze_client.py`. |

---

## Deliverables Checklist

- [x] Working hosted URL (`https://bankers-wrapped.vercel.app`)
- [ ] Demo video ≤ 3 min uploaded to YouTube
- [ ] Devpost submission form completed
- [ ] README links to demo video and hosted URL
- [ ] `make demo` runs clean on a fresh clone

---

## Pipeline Artifacts Stored in B2 (10 artifacts / session)

```text
{user_id}/{session_id}/input/transactions.csv
{user_id}/{session_id}/pipeline/script.json            ← 5-scene narrative
{user_id}/{session_id}/pipeline/analytics.json         ← financial insights snapshot
{user_id}/{session_id}/pipeline/prompts.json           ← image prompts + SHA-256 hashes
{user_id}/{session_id}/pipeline/generation.json        ← model, latency, retry per step
{user_id}/{session_id}/pipeline/thumbnail.png          ← scene 0 preview image
{user_id}/{session_id}/pipeline/narration.mp3          ← OpenAI TTS via GenblazeClient
{user_id}/{session_id}/pipeline/scenes/scene_00.png … scene_04.png
{user_id}/{session_id}/output/recap_{session_id}.mp4
{user_id}/{session_id}/metadata/session_metadata.json
```

---

## Demo Script (for video recording)

1. Open `https://bankers-wrapped.vercel.app`
2. Upload `data/synthetic/transactions_jan_2026.csv` (Financial Builder personality)
3. Show the **live 7-step SSE progress** while the 4-agent pipeline runs *(jump-cut the ~4 min generation wait)*
4. Play the generated **narrated MP4 recap video** (H.264 + AAC, xfade transitions, OpenAI TTS voice)
5. Click **"Share your recap →"** — open the public share page at `/recap/{session_id}` showing thumbnail + artifact list
6. Click **"Download full package"** — show the ZIP download of all 10 B2 artifacts
7. Open the **B2 bucket** in the Backblaze console — show the 10-artifact structured layout per session
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
