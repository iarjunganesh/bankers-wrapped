# Hackathon Submission — Backblaze Generative Media Hackathon 2026

> Submission deadline: **August 3, 2026**
> Required deliverables: working hosted URL + ≤ 3-min demo video

---

## Judging Alignment

| Criterion | How Banker's Wrapped Addresses It |
| --- | --- |
| **Real-World Utility** | Solves chronically low engagement in banking apps — turns opaque data into a story people want to share. Clear target market: retail banks and fintechs. |
| **Production Readiness** | CI/CD with 70%+ coverage gate, structured JSON logging, health endpoint, error handling, 6 ADRs, synthetic demo data committed to repo. Not a prototype — a deployable system. |
| **B2 Storage + Orchestration** | B2 stores every pipeline artifact under a structured `{user_id}/{session_id}/` hierarchy with full provenance metadata per session. Presigned URLs serve the final video. |
| **Genblaze Usage** | Genblaze is the **sole** media generation layer — every image generation call routes through the Genblaze Pipeline SDK. No provider is called directly. |

---

## Deliverables Checklist

- [ ] Working hosted URL (`https://bankers-wrapped.vercel.app`)
- [ ] Demo video ≤ 3 min uploaded to YouTube
- [ ] Devpost submission form completed
- [ ] README links to demo video and hosted URL
- [ ] `make demo` runs clean on a fresh clone

---

## Demo Script (for video recording)

1. Open `https://bankers-wrapped.vercel.app`
2. Upload `data/synthetic/transactions_jan_2026.csv` (Financial Builder personality)
3. Show the progress indicator while the 4-agent pipeline runs
4. Play the generated MP4 recap video
5. Open the B2 bucket in the Backblaze console — show the structured artifact layout
6. Open `session_metadata.json` — show provenance trail (models used, SHA-256 hash, processing time)
7. Repeat with `transactions_q4_2025.csv` to show a different personality (Financial Explorer)

---

## Submission Links

| | |
| --- | --- |
| **App** | `https://bankers-wrapped.vercel.app` *(deploy in progress)* |
| **Demo Video** | `https://youtu.be/TBD` |
| **Devpost** | `https://devpost.com/TBD` |
| **GitHub** | `https://github.com/iarjunganesh/bankers-wrapped` |
