# Running Costs & Budget — keep everything live through judging

> **Rule-driven requirement** ([official rules](https://backblaze-generative-media.devpost.com/rules)):
> the project must be available **free of charge and without restriction for testing by the
> Sponsor, Administrator and Judges until the Judging Period ends**.
> Submission deadline **Aug 3, 2026 (5 PM ET)** · Judging **Aug 5–11** · Winners **~Aug 12**.
> **Budget target: everything stays up through Aug 12, 2026 — not just Aug 3.**

Last verified: **2026-07-28** for GMI Cloud (measured against the console — see
[`assets/gmi-cloud/`](../assets/gmi-cloud/)) and for OpenAI (project-scoped spend read from the
usage console on 07-27). Railway / Vercel / B2 rows still carry the 2026-07-02 check.

---

## Component sweep

| Component | Role | Plan / price | Balance today | Est. need → Aug 12 | Action |
| --- | --- | --- | --- | --- | --- |
| **Railway** | Backend (FastAPI + FFmpeg) | Hobby **$5/mo**, includes $5 usage credit | Subscribed | ~$2–4 usage/mo (well inside the $5 credit) | ✅ Keep. **Do not cancel before Aug 12** — the cycle renews ~Aug 2 and must cover judging week (≈ $5 more) |
| **Vercel** | Frontend (Next.js) | Hobby — **free** | — | Tiny fraction of the 100 GB bandwidth / 1M requests | ✅ **No paid plan needed.** Hackathon use is non-commercial, which is exactly what Hobby allows |
| **Backblaze B2** | All session artifacts (14 files + session index) | First **10 GB free**; egress free up to 3× stored; 2,500 free class B/C calls/day | Free tier | ~25–40 MB per session → even 100+ sessions ≈ 3–4 GB | ✅ Free at our scale. WS-3 lifecycle rule keeps it bounded (protect the pinned demo session) |
| **NVIDIA NIM** | Narrative LLM **fallback** (Llama 3.1 70B) | **Free** via build.nvidia.com Developer Program; ~40 requests/min rate limit, no billing | Free | Only when GMI chat fails or returns invalid JSON | ✅ Free. Primary LLM is GMI `openai/gpt-5.4-mini` (**$0.003/run measured**, in the GMI budget) |
| **OpenAI** | TTS narration (`tts-1`) | $15 / 1M characters | **$0.686 spent** on this project, project-to-date *(usage console, 07-27)* | ~$0.015/run (≈ 1,000 chars) → 40 runs ≈ $0.60 | ✅ Lifetime spend is under **$0.70**. No top-up needed |
| **GMI Cloud** | Scene images (Seedream 4.0 via Genblaze) | **~$0.03 / image** measured (`seedream-4-0-250828`) | **$8.59** *(console, 07-27)* | **$0.15/run** (5 images) — see spend plan below | ✅ **$10 top-up already purchased.** Balance covers ~50 further runs; follow the spend plan |
| GitHub Actions / Codecov | CI + coverage | Free for public repos | — | — | ✅ Free |
| SQLite / FFmpeg / uv | In-container | Free / OSS | — | — | ✅ Free |

**Cash still to spend from today: ~$5** — Railway's ~Aug 2 renewal. The $10 GMI top-up has already
been purchased ($8.59 of it still unspent as of 2026-07-27).
Total project cash cost end-to-end: ~$30 (2× Railway + $10 OpenAI + $10 GMI).

---

## Per-run marginal cost (full 5-scene pipeline)

**Measured**, not estimated — from the GMI Cloud spend chart for `07/27/2026`, a day on which a
single 5-scene run was executed ([`assets/gmi-cloud/01-models-and-spend.png`](../assets/gmi-cloud/01-models-and-spend.png)).

| Step | Provider | Cost |
| --- | --- | --- |
| CSV parse + analytics | local | $0 |
| Narrative script | GMI `openai/gpt-5.4-mini` via Genblaze (NIM fallback: $0) | **$0.003** |
| 5 scene images | GMI Seedream (~$0.03/image implied) | **$0.150** |
| Narration (~1,000 chars) | OpenAI tts-1 | ~$0.015 |
| Compose + store + serve | FFmpeg / B2 / Railway | ~$0 |
| **Total** | | **≈ $0.17 per run** |

The GMI portion (**$0.153**) is read directly off the console tooltip. An earlier planning estimate
in this document assumed `$0.05/image` and put the total at ≈ $0.27 — the measured figure is
**~37% lower**. The per-image rate is inferred by dividing the day's Seedream spend by the five
images that run generated, so treat `$0.03/image` as an implied rate rather than a published price.

---

## GMI spend plan — remaining budget

$10 top-up purchased; **$8.59 unspent** as of 2026-07-27, i.e. roughly **56 further runs** at the
measured $0.153/run. Spent to date: ~$1.41 across development validation and the two committed
demo sessions.

| Purpose | Budget | Runs |
| --- | --- | --- |
| Demo-video recording — one CSV run, plus slack for a retake | $0.50 | ~3 |
| Iteration slack / retries | $1.09 | ~7 |
| **Judging-week reserve (Aug 5–11)** — judges will run live pipelines; the 5/hr/IP rate limiter caps drive-by burn | **$7.00** | ~45 |

The reserve is far more comfortable than the original plan assumed, because the measured per-run
cost came in ~37% under the $0.05/image estimate it was built on.

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
5. **Originality window**: project must be newly created or significantly updated during the submission period (Jun 22 – Aug 3) to use B2 + Genblaze — the v1.6.0 → v1.9.2 work all lands inside it; keep committing.
