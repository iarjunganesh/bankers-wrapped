# Banker's Wrapped — Claude Code Context

## Project

AI-powered financial storytelling platform entered in the **Backblaze Generative Media Hackathon 2026**. Target: Grand Prize (top 1–3 of 300+ participants).

Upload a CSV → 4-agent pipeline → personalized narrated MP4 recap video stored on Backblaze B2.

**Current phase**: v1.5.0 — FFmpeg ending card (fixed 0-frame bug), SSE race condition fixed, per-step latency in UI, `FFMPEG_BIN` config, README notebook section. Remaining work: demo video (≤3 min) + Devpost form submission + seed Scenario C session ID in notebook.

## Key Commands

```bash
make install      # uv sync --group dev
make dev          # uvicorn :8000 (hot-reload)
make test         # pytest tests/ --cov=backend --cov-fail-under=80
make lint         # ruff check . && mypy backend/
make demo         # full pipeline with data/synthetic/transactions_jan_2026.csv
make demo-start   # start backend + frontend (bash scripts/start_demo.sh)
make demo-stop    # stop all services
```

## Architecture

4-agent pipeline — each agent is a typed async `BaseAgent`:

1. `DocumentAgent` — CSV parse + normalise → `List[Transaction]`
2. `AnalyticsAgent` — insights + Financial Personality → `FinancialInsights`
3. `NarrativeAgent` — NVIDIA NIM (Llama 3.1 70B) structured script → `NarrativeScript` (**5 scenes**)
4. `MediaAgent` — Genblaze → GMI Cloud Seedream (images, parallel) + OpenAI TTS (narration) + FFmpeg (xfade) → `recap.mp4` → B2

All AI media calls route through the **Genblaze SDK** (`genblaze-core`, `genblaze-gmicloud`).  
OpenAI TTS is wrapped inside `GenblazeClient.generate_narration_audio()` — no direct provider calls outside that wrapper.

## Critical Constraints

- **Genblaze is mandatory** — sole media generation layer; judges score on this. Image generation: Genblaze → GMI Cloud Seedream. Audio: OpenAI TTS wrapped in GenblazeClient (no direct openai.audio calls outside genblaze_client.py).
- **B2 stores everything** — input CSV, script, analytics, prompts, generation provenance, images, thumbnail, narration audio, video, metadata
- `get_settings()` uses `@lru_cache` — call `get_settings.cache_clear()` in tests that need different env vars
- FFmpeg must be installed on the host: Linux `sudo apt-get install ffmpeg` · Windows `winget install ffmpeg`
- SQLite for MVP; PostgreSQL via `DATABASE_URL` env var is the documented upgrade path (ADR-004)
- `FFmpegComposer.compose()` is `async def` — always `await` it; `audio_path` param is now used
- Coverage gate: ≥ **80%** enforced in CI (currently at 93%)
- `MediaAgentOutput` now has `thumbnail_url` field — always populated
- `MediaAgentInput` now has optional `analytics_output` field — pass it from the API layer
- Retry: `GenblazeClient` wraps image + audio generation with tenacity (3 attempts, exponential backoff 2–30 s)
- `MediaAgent` accepts `progress_callback: Callable[[str, str], None]` — used by API to emit mid-agent SSE events

## Testing Strategy

- `tests/unit/` — per-agent unit tests; Genblaze, B2, FFmpeg, OpenAI are all mocked
- `tests/integration/` — API end-to-end with mocked pipeline deps
- `data/synthetic/` — two CSV files committed; use instead of real bank data
- Mock OpenAI TTS in tests: `mocker.patch("backend.media.genblaze_client.OpenAI")` or patch `openai.audio.speech.create`
- Patch ALL 10 B2Client static key methods when testing MediaAgent (input_key, pipeline_key, scene_key, narration_key, output_key, metadata_key, analytics_key, prompts_key, generation_key, thumbnail_key)

## B2 Key Layout (Full Asset Manifest)

```
{user_id}/{session_id}/input/transactions.csv
{user_id}/{session_id}/pipeline/script.json          ← narrative script
{user_id}/{session_id}/pipeline/analytics.json       ← financial insights snapshot
{user_id}/{session_id}/pipeline/prompts.json         ← all image prompts + hashes
{user_id}/{session_id}/pipeline/generation.json      ← model, provider, latency, retry per step
{user_id}/{session_id}/pipeline/narration.mp3
{user_id}/{session_id}/pipeline/thumbnail.jpg        ← scene 0 (a JPEG) reused as recap preview
{user_id}/{session_id}/pipeline/scenes/scene_00.jpg … scene_04.jpg
{user_id}/{session_id}/output/recap_{session_id}.mp4
{user_id}/{session_id}/metadata/session_metadata.json
```

## Session Metadata — models_used

```json
{
  "llm":        "nvidia-nim/meta/llama-3.1-70b-instruct",
  "image":      "gmi-cloud/seedream-4-0-250828",
  "audio":      "openai/tts-1",
  "compositor": "ffmpeg"
}
```

## SSE Progress Endpoint

`GET /api/v1/recap/{session_id}/progress` — Server-Sent Events stream.  
Events emitted (in order, 12 steps + terminal):
`parsing` → `analyzing` → `scripting` → `generating_images` → `scene_0_done` … `scene_4_done` → **`composing_video`** → **`uploading_to_b2`** → `uploading` → `complete` / `failed`

`composing_video` and `uploading_to_b2` are emitted from inside `MediaAgent` via `progress_callback`.  
The endpoint waits up to 10 s for the session to be created (SSE race-condition fix). Each event carries a real `ts` (Unix timestamp) used by the frontend to calculate per-step latency.

## API Endpoints

- `POST /api/v1/recap/generate` — run full pipeline; rate-limited 5/hr/IP; returns `RecapResponse`
- `GET  /api/v1/recap/{session_id}` — fetch completed recap by session ID (used by share page)
- `GET  /api/v1/recap/{session_id}/progress` — SSE stream of pipeline stage events
- `GET  /api/v1/recap/{session_id}/download` — **Download ZIP** of all B2 artifacts (video, images, audio, metadata, prompts)
- `GET  /api/v1/health` — health check; returns version + status

## Narrative — 5-Scene Cinematic Structure

1. **Opening / Personality Reveal** — announce Financial Personality, set tone, total income
2. **Big Achievement** — celebrate savings rate, debt payoff, or investment milestone
3. **Spending Insight** — top spending category with positive framing
4. **Personalized Advice** — one concrete, actionable tip for this personality
5. **Motivational Close** — forward-looking encouragement, warm sign-off

## FFmpeg Composition — Visual Effects

- xfade crossfade (0.5 s) between every consecutive scene pair
- Global fade-in from black (0.5 s at start)
- Global fade-out to black (0.5 s at end)
- Scene duration auto-stretches from probed audio length so video always covers the full narration; `-shortest` trims to exact audio end
- **Constant frame rate is mandatory** — each scene input sets `-framerate 25` and the filter chain ends with `fps=25`. Looped images default to rate `1/0`, which stricter ffmpeg builds (Railway) reject in xfade (*"inputs needs to be a constant frame rate"*)
- H.264 libx264, **`-pix_fmt yuv420p`** (REQUIRED — seedream JPEGs are full-range 4:4:4; without this libx264 emits High 4:4:4 / `yuvj444p`, which plays in VLC but is "corrupt" in browsers), 1792×1024 (16:9), AAC 192 kbps audio
- **`-movflags +faststart`** — moves the `moov` atom to the front for progressive browser streaming
- `FFmpegComposer` derives `ffprobe` from `ffmpeg_bin` by replacing only the **filename** (not directory segments like `ffmpeg-8.1.1-full_build`)

## Frontend Routes

- `/` — CSV upload portal with 7-step live SSE progress (scene events collapsed into a "Generating scenes + narration — X/5 scenes" sub-label; per-step latency; ~5 min ETA) + thumbnail (also set as `<video poster>`) + personality result + download ZIP + share button
- `/recap/{session_id}` — Public share page: thumbnail, personality badge, stats, video player, download ZIP, full B2 artifact list with paths

## Personality Themes (for UI)

| Personality         | Color             | Icon |
| ------------------- | ----------------- | ---- |
| Financial Builder   | Amber (#F59E0B)   | 🏗️  |
| Financial Explorer  | Teal (#14B8A6)    | 🌍  |
| Financial Achiever  | Purple (#8B5CF6)  | 🏆  |
| Financial Optimizer | Blue (#3B82F6)    | ⚙️  |

## Production Hardening

- Rate limiting: `slowapi` — 5 uploads per hour per IP on `POST /api/v1/recap/generate`
- CSV byte-level validation: check for printable ASCII / UTF-8 headers, reject binary files
- PostgreSQL: `DATABASE_URL` env var in `config.py`; `SessionStore` uses SQLAlchemy if set, SQLite otherwise
- Coverage gate: 80% (currently 93%)
- Retry: tenacity-based, 3 attempts, exponential backoff 2–30 s on all media generation calls
- Structured logging via structlog on every pipeline step

## Deployment

- Backend: Railway (Dockerfile or Procfile) or Render (`render.yaml`)
- Frontend: Vercel (`vercel.json`)
- Env vars required: `GMI_API_KEY`, `NVIDIA_NIM_API_KEY`, `OPENAI_API_KEY`, `B2_KEY_ID`, `B2_APPLICATION_KEY`, `B2_ENDPOINT_URL`, `B2_BUCKET_NAME`, `DATABASE_URL` (optional)

## Hackathon Deadline

Submission due: **August 3, 2026**. Required deliverables: working hosted URL + ≤ 3-min demo video + Devpost form.

## Judging Criteria (all equally weighted)

1. **Real-World Utility** — solves low engagement in banking; clear market (retail banks / fintechs)
2. **Production Readiness** — CI/CD, 93% coverage, rate limiting, structured logging, health endpoint, retry logic, 6 ADRs
3. **B2 Storage & Data Orchestration** — 10 artifact types stored per session; complete provenance manifest; share page + ZIP download show full B2 layout
4. **Use of Genblaze** — image generation (Genblaze → GMI Cloud) + narration audio (OpenAI TTS via GenblazeClient); two provider types; retry tracking in generation.json
