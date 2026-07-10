# Devpost Submission — Banker's Wrapped

Hackathon: [Backblaze Generative Media Hackathon 2026](https://devpost.com/submit-to/30205-backblaze-generative-media-hackathon-build-with-genblaze-on-b2/manage/submissions)
Deadline: **August 3, 2026 (5 PM ET)** · Judging: **Aug 5–11** · Winners: ~Aug 12
Target: **Grand Prize (top 1–3 of 300+ participants)**

> Per the [rules](https://backblaze-generative-media.devpost.com/rules): app stays live + free for
> judges through **Aug 11**; video **publicly visible** on YouTube/Vimeo/Youku, <3 min, **no
> copyrighted music**; no modifications after the deadline. Budget/runway: [`COSTS.md`](COSTS.md).

---

## Submission Checklist

### General Info
- [x] Project name: `Banker's Wrapped`
- [x] Elevator pitch: *The engagement layer missing from every banking app — AI-generated financial storytelling that makes people actually care about their money.*

### Project Story
- [x] Inspiration drafted
- [x] What it does drafted
- [x] How we built it drafted
- [x] Challenges drafted
- [x] Accomplishments drafted
- [x] What we learned drafted
- [x] What's next drafted
- [x] Built with list drafted

### Additional Info (Judges Only)
- [ ] App URL — fill in Railway/Vercel deployment URL
- [ ] GitHub Repo URL — fill in; grant `b2genblaze` contributor access if private
- [x] Providers and models drafted
- [x] B2 and Genblaze usage drafted

### Project Media
- [ ] Demo video (≤ 3 min) — record and upload (public; no copyrighted music)
- [ ] Screenshot: upload + live SSE progress UI
- [ ] Screenshot: share page (video player + B2 artifact list)
- [ ] Screenshot: personality result (one of the 4 types)
- [ ] Generated scene image(s) from a real run

### Feedback Prize (free extra — 10 winners, stackable with an overall prize)
- [ ] File genuine product feedback (bug report / feature request) via [Genblaze GitHub Issues](https://github.com/backblaze-labs/genblaze/issues) and reference it in the submission

---

## Content

### Elevator Pitch

> The engagement layer missing from every banking app — AI-generated financial storytelling that makes people actually care about their money.

---

### Project Story

#### Inspiration

Every bank app shows the same thing: a list of transactions and a bar chart you scroll past. Engagement data from fintechs consistently shows that users open their banking app once a month, glance at the balance, and leave. Yet Spotify Wrapped proves that when you package the same raw data as a *story*, people watch it, share it, and talk about it.

We wanted to bring that energy to personal finance — not a dashboard, but a cinematic recap. Something you'd actually want to show a friend.

#### What it does

Banker's Wrapped takes a transaction history — upload a CSV, or **connect a bank in one click via Plaid** (sandbox) — and runs it through a 4-agent AI pipeline to produce a **personalized, narrated MP4 recap video** — your financial year, told as a story.

In about 2–3 minutes you get:
- A **Financial Personality** classification (Builder, Explorer, Achiever, or Optimizer) based on your spending patterns
- A **5-scene cinematic video** with AI-generated imagery, voiceover narration, and dip-to-black transitions
- A **shareable public link** and a **ZIP download** of every artifact (video, images, audio, script, analytics, metadata) stored on Backblaze B2

#### How we built it

**Pipeline (Python / FastAPI)**
Four typed async agents chain together:
1. `DocumentAgent` — parses and normalises the CSV into structured transactions
2. `AnalyticsAgent` — computes insights and assigns a Financial Personality
3. `NarrativeAgent` — writes a structured 5-scene cinematic script via **Genblaze → GMI Cloud chat** (with automatic NVIDIA NIM Llama 3.1 70B fallback on invalid output)
4. `MediaAgent` — generates all imagery and audio via the Genblaze SDK, then composes the final video with FFmpeg

**AI orchestration (Genblaze)**
**Three of the four AI steps route through the Genblaze SDK**: scene images (Genblaze → GMI Cloud Seedream, 5 in parallel), the narrative LLM (Genblaze → GMI Cloud chat, NIM fallback), and narration audio (OpenAI TTS wrapped inside `GenblazeClient` — no direct provider calls anywhere else). Retry logic (tenacity, 3 attempts, exponential backoff) is built in at the Genblaze layer, and every step's provider, model, latency, retry count — and for the LLM, tokens and `cost_usd` — land in `generation.json`.

**Storage (Backblaze B2)**
**B2 is the source of truth, not just an output bucket.** Every artifact from every session is stored to B2 — **14 files across 10 artifact types** plus a flat session index: input CSV, script, analytics snapshot, image prompts, generation provenance manifest, 5 scene images, thumbnail, narration MP3, final MP4, and a **self-contained session manifest** that lets any share link survive a full backend redeploy (SQLite is just a read cache). `generation.json` records model, provider, latency, and retry count for each step **plus a SHA-256 for all 12 content artifacts**, and a committed 45-day lifecycle rule keeps storage bounded.

**Video composition (FFmpeg)**
A **memory-bounded segment + concat** compositor: each scene is rendered to its own short MP4 (one image in RAM at a time, with a dip-to-black fade), then the segments are joined with the concat demuxer using stream-copy (`-c:v copy` — no re-decode). Peak memory stays ~300 MB instead of the multiple GB a monolithic crossfade graph needs, so it runs even in a 0.5 GB container. Output is H.264 `yuv420p`, constant 25 fps, with `-movflags +faststart` for progressive browser streaming.

**Frontend (Next.js / Vercel)**
Live SSE progress with per-step latency display, video player with B2-backed poster thumbnail, personality badge, and share/download actions.

**Infrastructure**
Backend on Railway, frontend on Vercel. 98% test coverage, CI/CD, rate limiting (5 uploads/hr/IP), structured logging via structlog.

#### Challenges we ran into

**FFmpeg OOM-killed on Railway** — our first compositor was a single `xfade` filter graph. It worked locally but was SIGKILL'd (`returncode -9`, zero frames) on Railway. The cause: a monolithic crossfade buffers every looped input's frames until its staggered transition offset — several GB at 1792×1024 — which blows past a memory-limited container. The fix wasn't a flag; it was a redesign. We rewrote composition to **render each scene to its own segment, then concat-copy them** (dip-to-black between scenes), dropping peak memory from multiple GB to ~300 MB. It now runs in 0.5 GB.

**A frozen progress bar that wasn't actually frozen** — the live SSE progress stream would hang on "Writing narrative script" even though the backend completed the recap. The pipeline ran image generation and B2 uploads with synchronous calls *inside* async functions, blocking the event loop for minutes and starving the SSE stream until the connection dropped. We offloaded every blocking call to `asyncio.to_thread` — which, as a bonus, let the 5 image generations finally run **in parallel** via `asyncio.gather`, cutting a full run from ~5 min to ~2–3.

**Browser video compatibility** — Seedream outputs full-range 4:4:4 JPEGs. Without explicit `-pix_fmt yuv420p`, libx264 emits a High 4:4:4 profile that VLC plays fine but browsers reject as corrupt. We also force `-framerate 25` / `fps=25` for constant frame rate and `-movflags +faststart` for progressive streaming.

**Share links that quietly expired** — `GET /recap/{id}` returned the presigned URLs minted at generation time, which expire after an hour — so any shared recap went dead. We now regenerate presigned URLs from the stored B2 keys on every request, so links stay valid indefinitely.

**B2 provenance at scale** — designing a key layout that's both human-navigable and machine-parseable across 10 artifact types took a few iterations. The final layout (`{user_id}/{session_id}/...`) groups everything by session and makes the share page's artifact listing trivial.

#### Accomplishments that we're proud of

- A genuinely end-to-end generative media pipeline — one upload, one video out, every intermediate artifact preserved
- 14 files (10 artifact types) stored per B2 session, including full generation provenance (model, provider, latency, retry count per step)
- 98% test coverage with a hard CI gate at 80%
- A public share page that surfaces the full B2 artifact manifest — judges can inspect every step of what the pipeline produced
- A memory-bounded video compositor that renders a full narrated recap in ~300 MB of RAM — it runs in a 0.5 GB container, not just on a beefy laptop

#### What we learned

- Genblaze's SDK abstraction makes it easy to swap underlying image/audio providers without touching pipeline logic — the retry and backoff behavior is consistent regardless of which model is behind it
- Browser video is more fragile than it looks — pixel format, codec profile, and moov atom placement all matter
- "Async" code isn't non-blocking by default — one synchronous call inside an `async` function freezes the whole event loop, and the symptom (a hung progress bar) looks nothing like the cause
- Memory limits force better design — being OOM-killed on a 0.5 GB container pushed us to a streaming compositor that's simpler *and* more portable than the original
- SSE is a great fit for long-running AI pipelines: simple, stateless, and survives a page refresh better than WebSockets for this use case
- B2's S3-compatible API is production-ready with no meaningful friction — presigned URLs, structured key prefixes, and lifecycle rules all work exactly as documented

#### What's next for Banker's Wrapped

- **Bank integrations** — Plaid or Open Banking API so users skip the CSV export entirely
- **Multi-period recaps** — quarterly or monthly videos, not just annual
- **White-label for banks** — package as an embeddable widget fintechs can drop into their existing apps
- **Richer personalities** — more archetypes, trend detection across multiple periods, peer benchmarking

#### Built with

Python, FastAPI, Next.js, Genblaze SDK, GMI Cloud (Seedream + chat), NVIDIA NIM (Llama 3.1 70B), OpenAI TTS, Plaid (sandbox), FFmpeg, Backblaze B2, Railway, Vercel, SQLite, structlog, tenacity, pytest, k6

---

### Additional Info (Judges Only)

#### App URL

`https://bankers-wrapped.vercel.app` (frontend) · `https://bankers-wrapped-api-production.up.railway.app` (API)

#### GitHub Repo URL

`https://github.com/iarjunganesh/bankers-wrapped` (public — no judge access grant needed)

#### Providers and Models

| Role | Provider | Model |
|------|----------|-------|
| Script generation (LLM) | Genblaze → GMI Cloud (fallback: NVIDIA NIM) | `meta-llama/Llama-3.3-70B-Instruct` (fallback `meta/llama-3.1-70b-instruct`) |
| Image generation | Genblaze → GMI Cloud | `seedream-4-0-250828` |
| Narration audio (TTS) | Genblaze → OpenAI | `tts-1` |
| Bank ingestion (optional) | Plaid Sandbox | Transactions API |
| Video composition | FFmpeg | H.264 / AAC |

#### B2 and Genblaze Usage

**Backblaze B2** stores every artifact produced per session — 14 files across 10 types:

`input/transactions.csv` · `pipeline/script.json` · `pipeline/analytics.json` · `pipeline/prompts.json` · `pipeline/generation.json` (provenance: model, provider, latency, retry count per step) · `pipeline/narration.mp3` · `pipeline/thumbnail.jpg` · `pipeline/scenes/scene_00–04.jpg` · `output/recap_{session_id}.mp4` · `metadata/session_metadata.json`

Artifacts are served via presigned URLs on both the results page and a public share page (`/recap/{session_id}`), which lists the full B2 key manifest. Users can also download a ZIP of all artifacts via `GET /api/v1/recap/{session_id}/download`.

**Genblaze** orchestrates **3 of the 4 AI steps**. Image generation routes through `genblaze-gmicloud` → GMI Cloud Seedream (5 scenes in parallel). The narrative LLM routes through Genblaze → GMI Cloud chat (`generate_script_text()`), with automatic fallback to NVIDIA NIM on invalid structured output. Narration audio routes through `GenblazeClient.generate_narration_audio()` which wraps OpenAI TTS — no direct provider calls exist outside that wrapper. All paths include tenacity-based retry (3 attempts, exponential backoff 2–30 s); per-step provider, model, latency, retry counts — and LLM tokens + `cost_usd` — are recorded in `generation.json` on B2, alongside a SHA-256 for every content artifact.

---

## Demo Video Script (≤ 3 min)

Suggested beats:
1. **(0:00–0:20)** Problem: banking apps are boring, nobody engages with their data
2. **(0:20–0:40)** Ingest: click **"Connect a bank (sandbox)"** (Plaid Link) — mention CSV upload works too
3. **(0:40–1:20)** Watch the live SSE progress — call out each step and the per-step latency
4. **(1:20–1:50)** Play the generated recap video in-browser — personality badge, all 5 scenes
5. **(1:50–2:20)** Share page + **B2 console**: artifact layout, `generation.json` provenance (models, latency, retries, SHA-256 per artifact), lifecycle rule
6. **(2:20–2:40)** Durability punchline: redeploy the backend — the share link still works (B2 is the source of truth)
7. **(2:40–3:00)** Close: "One connection. Five scenes. Your financial story." + Genblaze/B2 architecture one-liner

---

## Screenshot Targets

| # | What to capture | Where in UI |
|---|-----------------|-------------|
| 1 | Upload portal (pre-upload) | `/` — drag-drop zone |
| 2 | Live SSE progress mid-run | `/` — step tracker with latency |
| 3 | Results: video player + personality badge | `/` — post-complete |
| 4 | Share page: video + B2 artifact list | `/recap/{session_id}` |
| 5 | A generated scene image (cinematic) | Download ZIP → scenes/ |
