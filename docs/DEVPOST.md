# Devpost Submission — Banker's Wrapped

Hackathon: [Backblaze Generative Media Hackathon 2026](https://devpost.com/submit-to/30205-backblaze-generative-media-hackathon-build-with-genblaze-on-b2/manage/submissions)
Deadline: **August 3, 2026**
Target: **Grand Prize (top 1–3 of 300+ participants)**

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
- [ ] Demo video (≤ 3 min) — record and upload
- [ ] Screenshot: upload + live SSE progress UI
- [ ] Screenshot: share page (video player + B2 artifact list)
- [ ] Screenshot: personality result (one of the 4 types)
- [ ] Generated scene image(s) from a real run

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

Banker's Wrapped takes a transaction history CSV (the kind any bank lets you export) and runs it through a 4-agent AI pipeline to produce a **personalized, narrated MP4 recap video** — your financial year, told as a story.

In about 2–3 minutes you get:
- A **Financial Personality** classification (Builder, Explorer, Achiever, or Optimizer) based on your spending patterns
- A **5-scene cinematic video** with AI-generated imagery, voiceover narration, and dip-to-black transitions
- A **shareable public link** and a **ZIP download** of every artifact (video, images, audio, script, analytics, metadata) stored on Backblaze B2

#### How we built it

**Pipeline (Python / FastAPI)**
Four typed async agents chain together:
1. `DocumentAgent` — parses and normalises the CSV into structured transactions
2. `AnalyticsAgent` — computes insights and assigns a Financial Personality
3. `NarrativeAgent` — calls NVIDIA NIM (Llama 3.1 70B) to write a structured 5-scene cinematic script
4. `MediaAgent` — generates all imagery and audio via the Genblaze SDK, then composes the final video with FFmpeg

**Media generation (Genblaze)**
All AI media routes through the Genblaze SDK. Images are generated via Genblaze → GMI Cloud Seedream (5 scenes in parallel). Narration audio is generated via OpenAI TTS wrapped inside `GenblazeClient.generate_narration_audio()`. Retry logic (tenacity, 3 attempts, exponential backoff) is built in at the Genblaze layer.

**Storage (Backblaze B2)**
Every artifact from every session is stored to B2 — **14 files across 10 artifact types** per session: input CSV, script, analytics snapshot, image prompts, generation provenance manifest, 5 scene images, thumbnail, narration MP3, final MP4, and session metadata. The provenance manifest (`generation.json`) records model, provider, latency, and retry count for each step.

**Video composition (FFmpeg)**
A **memory-bounded segment + concat** compositor: each scene is rendered to its own short MP4 (one image in RAM at a time, with a dip-to-black fade), then the segments are joined with the concat demuxer using stream-copy (`-c:v copy` — no re-decode). Peak memory stays ~300 MB instead of the multiple GB a monolithic crossfade graph needs, so it runs even in a 0.5 GB container. Output is H.264 `yuv420p`, constant 25 fps, with `-movflags +faststart` for progressive browser streaming.

**Frontend (Next.js / Vercel)**
Live SSE progress with per-step latency display, video player with B2-backed poster thumbnail, personality badge, and share/download actions.

**Infrastructure**
Backend on Railway, frontend on Vercel. 93% test coverage, CI/CD, rate limiting (5 uploads/hr/IP), structured logging via structlog.

#### Challenges we ran into

**FFmpeg OOM-killed on Railway** — our first compositor was a single `xfade` filter graph. It worked locally but was SIGKILL'd (`returncode -9`, zero frames) on Railway. The cause: a monolithic crossfade buffers every looped input's frames until its staggered transition offset — several GB at 1792×1024 — which blows past a memory-limited container. The fix wasn't a flag; it was a redesign. We rewrote composition to **render each scene to its own segment, then concat-copy them** (dip-to-black between scenes), dropping peak memory from multiple GB to ~300 MB. It now runs in 0.5 GB.

**A frozen progress bar that wasn't actually frozen** — the live SSE progress stream would hang on "Writing narrative script" even though the backend completed the recap. The pipeline ran image generation and B2 uploads with synchronous calls *inside* async functions, blocking the event loop for minutes and starving the SSE stream until the connection dropped. We offloaded every blocking call to `asyncio.to_thread` — which, as a bonus, let the 5 image generations finally run **in parallel** via `asyncio.gather`, cutting a full run from ~5 min to ~2–3.

**Browser video compatibility** — Seedream outputs full-range 4:4:4 JPEGs. Without explicit `-pix_fmt yuv420p`, libx264 emits a High 4:4:4 profile that VLC plays fine but browsers reject as corrupt. We also force `-framerate 25` / `fps=25` for constant frame rate and `-movflags +faststart` for progressive streaming.

**Share links that quietly expired** — `GET /recap/{id}` returned the presigned URLs minted at generation time, which expire after an hour — so any shared recap went dead. We now regenerate presigned URLs from the stored B2 keys on every request, so links stay valid indefinitely.

**B2 provenance at scale** — designing a key layout that's both human-navigable and machine-parseable across 10 artifact types took a few iterations. The final layout (`{user_id}/{session_id}/...`) groups everything by session and makes the share page's artifact listing trivial.

#### Accomplishments that we're proud of

- A genuinely end-to-end generative media pipeline — one upload, one video out, every intermediate artifact preserved
- 14 files (10 artifact types) stored per B2 session, including full generation provenance (model, provider, latency, retry count per step)
- 93% test coverage with a hard CI gate at 80%
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

Python, FastAPI, Next.js, Genblaze SDK, GMI Cloud Seedream, NVIDIA NIM (Llama 3.1 70B), OpenAI TTS, FFmpeg, Backblaze B2, Railway, Vercel, SQLite, structlog, tenacity, pytest

---

### Additional Info (Judges Only)

#### App URL
<!-- Fill in: your Railway/Vercel deployment URL -->

#### GitHub Repo URL
<!-- Fill in: public or private repo URL -->
<!-- If private: grant GitHub user `b2genblaze` contributor access -->

#### Providers and Models

| Role | Provider | Model |
|------|----------|-------|
| Script generation (LLM) | NVIDIA NIM | `meta/llama-3.1-70b-instruct` |
| Image generation | Genblaze → GMI Cloud | `seedream-4-0-250828` |
| Narration audio (TTS) | Genblaze → OpenAI | `tts-1` |
| Video composition | FFmpeg | H.264 / AAC |

#### B2 and Genblaze Usage

**Backblaze B2** stores every artifact produced per session — 14 files across 10 types:

`input/transactions.csv` · `pipeline/script.json` · `pipeline/analytics.json` · `pipeline/prompts.json` · `pipeline/generation.json` (provenance: model, provider, latency, retry count per step) · `pipeline/narration.mp3` · `pipeline/thumbnail.jpg` · `pipeline/scenes/scene_00–04.jpg` · `output/recap_{session_id}.mp4` · `metadata/session_metadata.json`

Artifacts are served via presigned URLs on both the results page and a public share page (`/recap/{session_id}`), which lists the full B2 key manifest. Users can also download a ZIP of all artifacts via `GET /api/v1/recap/{session_id}/download`.

**Genblaze** is the sole media generation layer. Image generation routes through `genblaze-gmicloud` → GMI Cloud Seedream (5 scenes generated in parallel). Narration audio routes through `GenblazeClient.generate_narration_audio()` which wraps OpenAI TTS — no direct provider calls exist outside that wrapper. Both paths include tenacity-based retry (3 attempts, exponential backoff 2–30 s), and retry counts per step are recorded in `generation.json` on B2.

---

## Demo Video Script (≤ 3 min)

Suggested beats:
1. **(0:00–0:20)** Problem: banking apps are boring, nobody engages with their data
2. **(0:20–0:40)** Upload a CSV — show the drag-and-drop UI
3. **(0:40–1:30)** Watch the live SSE progress — call out each step and the per-step latency
4. **(1:30–2:00)** Play the generated recap video in-browser — personality badge, all 5 scenes
5. **(2:00–2:30)** Show the share page — B2 artifact list, ZIP download, public link
6. **(2:30–3:00)** Architecture one-liner + close: "One CSV. Five scenes. Your financial story."

---

## Screenshot Targets

| # | What to capture | Where in UI |
|---|-----------------|-------------|
| 1 | Upload portal (pre-upload) | `/` — drag-drop zone |
| 2 | Live SSE progress mid-run | `/` — step tracker with latency |
| 3 | Results: video player + personality badge | `/` — post-complete |
| 4 | Share page: video + B2 artifact list | `/recap/{session_id}` |
| 5 | A generated scene image (cinematic) | Download ZIP → scenes/ |
