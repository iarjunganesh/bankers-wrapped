# Running Costs & Budget — keep everything live through judging

> **Rule-driven requirement** ([official rules](https://backblaze-generative-media.devpost.com/rules)):
> the project must be available **free of charge and without restriction for testing by the
> Sponsor, Administrator and Judges until the Judging Period ends**.
> Submission deadline **Aug 3, 2026 (5 PM ET)** · Judging **Aug 5–11** · Winners **~Aug 12**.
> **Budget target: everything stays up through Aug 12, 2026 — not just Aug 3.**

Last verified: 2026-07-02.

---

## Component sweep

| Component | Role | Plan / price | Balance today | Est. need → Aug 12 | Action |
| --- | --- | --- | --- | --- | --- |
| **Railway** | Backend (FastAPI + FFmpeg) | Hobby **$5/mo**, includes $5 usage credit | Subscribed | ~$2–4 usage/mo (well inside the $5 credit) | ✅ Keep. **Do not cancel before Aug 12** — the cycle renews ~Aug 2 and must cover judging week (≈ $5 more) |
| **Vercel** | Frontend (Next.js) | Hobby — **free** | — | Tiny fraction of the 100 GB bandwidth / 1M requests | ✅ **No paid plan needed.** Hackathon use is non-commercial, which is exactly what Hobby allows |
| **Backblaze B2** | All session artifacts (14 files + session index) | First **10 GB free**; egress free up to 3× stored; 2,500 free class B/C calls/day | Free tier | ~25–40 MB per session → even 100+ sessions ≈ 3–4 GB | ✅ Free at our scale. WS-3 lifecycle rule keeps it bounded (protect the pinned demo session) |
| **NVIDIA NIM** | Narrative LLM (Llama 3.1 70B) | **Free** via build.nvidia.com Developer Program; ~40 requests/min rate limit, no billing | Free | 1 request per pipeline run | ✅ Free. Caveat: no SLA — WS-1's Genblaze routing with NIM as fallback reduces this single point of failure |
| **OpenAI** | TTS narration (`tts-1`) | $15 / 1M characters | **$9.52** | ~$0.015/run (≈ 1,000 chars) → 40 runs ≈ $0.60 | ✅ Covered ~600×. No top-up needed |
| **GMI Cloud** | Scene images (Seedream 4.0 via Genblaze) | **$0.05 / image** (`seedream-4-0-250828`) | **$0.11** (promo spent) | **$0.25/run** (5 images) — see spend plan below | ⚠️ **The binding constraint.** Buy the $10 top-up; follow the spend plan |
| GitHub Actions / Codecov | CI + coverage | Free for public repos | — | — | ✅ Free |
| SQLite / FFmpeg / uv | In-container | Free / OSS | — | — | ✅ Free |

**Cash still to spend from today: ~$15** — the $10 GMI top-up + Railway's ~Aug 2 renewal ($5).
Total project cash cost end-to-end: ~$30 (2× Railway + $10 OpenAI + $10 GMI).

---

## Per-run marginal cost (full 5-scene pipeline)

| Step | Provider | Cost |
| --- | --- | --- |
| CSV parse + analytics | local | $0 |
| Narrative script | NVIDIA NIM | $0 (free tier) |
| 5 scene images | GMI Seedream @ $0.05 | **$0.25** |
| Narration (~1,000 chars) | OpenAI tts-1 | ~$0.015 |
| Compose + store + serve | FFmpeg / B2 / Railway | ~$0 |
| **Total** | | **≈ $0.27 per run** |

---

## GMI $10 spend plan (~40 runs total)

| Purpose | Budget | Runs |
| --- | --- | --- |
| WS-1 live validation (Genblaze LLM routing — chat tokens are ~$0.002/run, i.e. noise) | $1.50 | ~6 |
| Iteration slack / retries / prompt tweaks | $2.00 | ~8 |
| Final pinned demo sessions + demo-video recording (regenerate **after** WS-2/WS-3 so manifests carry the new fields) | $2.50 | ~10 |
| **Judging-week reserve (Aug 5–11)** — judges will run live pipelines; the 5/hr/IP rate limiter caps drive-by burn | **$4.00** | ~16 |

Rules of thumb:

- **Never generate live during development** — everything is mocked in tests; `make test` costs $0.
- **The optional Genblaze video scene stays cut** (~$0.50–2.00 per clip — the only thing that can eat the budget).
- If the reserve dips below ~$2 during judging week, temporarily tighten the rate limit rather than topping up.

---

## What we do NOT need

- ❌ Vercel Pro ($20/mo) — Hobby limits are ~100× our traffic; if a limit is ever hit the project pauses, it never bills.
- ❌ Railway Pro — usage stays inside the Hobby credit; the app must simply not be scaled up.
- ❌ B2 paid storage — we stay under 10 GB (lifecycle rule enforces it).
- ❌ NVIDIA AI Enterprise — hackathon evaluation use is squarely inside the free developer tier.
- ❌ Paid OpenAI top-up — $9.52 outlasts the hackathon by an order of magnitude.

---

## Rule-compliance notes that touch cost/uptime

1. **Availability window**: keep Railway + Vercel + B2 + all API keys live **through Aug 11** (judging ends), safest Aug 12.
2. **Free access**: no auth in front of the app (already true); judges must not need credentials.
3. **Demo video**: <3 min, publicly on YouTube/Vimeo/Youku, **no copyrighted music** — use silence or licensed audio only.
4. **Feedback Prize** (free +EV): submitting product feedback via Genblaze GitHub Issues makes us eligible for one of 10 mentorship prizes, winnable *in addition to* an overall prize.
5. **Originality window**: project must be newly created or significantly updated during the submission period (Jun 22 – Aug 3) to use B2 + Genblaze — our v1.6.0/v1.7.0 work satisfies this; keep committing.
