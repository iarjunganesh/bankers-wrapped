# Hackathon Submission — Backblaze Generative Media Hackathon 2026

> Submission deadline: **August 3, 2026**
> Required deliverables: working hosted URL + ≤ 3-min demo video

---

## Judging Alignment

| Criterion | How Banker's Wrapped Addresses It |
| --- | --- |
| **Real-World Utility** | Solves chronically low engagement in banking apps — turns opaque data into a story people want to share. Clear target market: retail banks and fintechs. |
| **Production Readiness** | CI/CD with 80%+ coverage gate (currently 94%), structured JSON logging, health endpoint, rate limiting (5 req/hr/IP), binary CSV validation, 6 ADRs, synthetic demo data committed. Not a prototype — a deployable system. |
| **B2 Storage + Orchestration** | B2 stores every pipeline artifact under a structured `{user_id}/{session_id}/` hierarchy with full provenance metadata. All 7 artifact keys returned in API response. Presigned URLs serve the final video. |
| **Genblaze Usage** | Genblaze is the **sole** media generation layer — image generation (GMI Cloud Seedream) and narration audio (OpenAI TTS) both route exclusively through `GenblazeClient`. No provider is called directly outside `genblaze_client.py`. |

---

## Deliverables Checklist

- [x] Working hosted URL (`https://bankers-wrapped.vercel.app`)
- [ ] Demo video ≤ 3 min uploaded to YouTube
- [ ] Devpost submission form completed
- [ ] README links to demo video and hosted URL
- [ ] `make demo` runs clean on a fresh clone

---

## Pipeline Artifacts Stored in B2

```text
{user_id}/{session_id}/input/transactions.csv
{user_id}/{session_id}/pipeline/script.json
{user_id}/{session_id}/pipeline/narration.mp3       ← OpenAI TTS via GenblazeClient
{user_id}/{session_id}/pipeline/scenes/scene_00.png … scene_03.png
{user_id}/{session_id}/output/recap_{session_id}.mp4
{user_id}/{session_id}/metadata/session_metadata.json
```

---

## Demo Script (for video recording)

1. Open `https://bankers-wrapped.vercel.app`
2. Upload `data/synthetic/transactions_jan_2026.csv` (Financial Builder personality)
3. Show the **live SSE step-by-step progress** while the 4-agent pipeline runs *(jump-cut the 3-min generation wait)*
4. Play the generated **narrated MP4 recap video** (H.264 + AAC audio with OpenAI TTS voice)
5. Click **"Share your recap →"** — open the public share page at `/recap/{session_id}`
6. Open the **B2 bucket** in the Backblaze console — show the structured artifact layout (7 artifacts)
7. Open `session_metadata.json` — show provenance trail (models used, SHA-256 hash, processing time)
8. *(Optional)* Repeat with `data/synthetic/transactions_q4_2025.csv` to show a different personality

---

## Submission Links

| | |
| --- | --- |
| **App** | `https://bankers-wrapped.vercel.app` ✅ live |
| **API** | `https://bankers-wrapped-api-production.up.railway.app` ✅ live |
| **Demo Video** | `https://youtu.be/TBD` |
| **Devpost** | `https://devpost.com/TBD` |
| **GitHub** | `https://github.com/iarjunganesh/bankers-wrapped` |
