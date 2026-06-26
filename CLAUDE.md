# Banker's Wrapped — Claude Code Context

## Project

AI-powered financial storytelling platform entered in the **Backblaze Generative Media Hackathon 2026**. Target: Grand Prize (top 1–3 of 300+ participants).

Upload a CSV → 4-agent pipeline → personalized 60-second narrated MP4 recap video stored on Backblaze B2.

**Current phase**: Phase 2 — Submission hardening. Core pipeline is complete (89% test coverage). Now adding voice narration, SSE progress, frontend polish, production hardening, and deployment.

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

4-agent Semantic Kernel pipeline — each agent is a typed async `BaseAgent`:

1. `DocumentAgent` — CSV parse + normalise → `List[Transaction]`
2. `AnalyticsAgent` — insights + Financial Personality → `FinancialInsights`
3. `NarrativeAgent` — NVIDIA NIM (Llama 3.1 70B) structured script → `NarrativeScript` (4 scenes)
4. `MediaAgent` — Genblaze → GMI Cloud Seedream (images, parallel) + OpenAI TTS (narration) + FFmpeg → `recap.mp4` → B2

All AI media calls route through the **Genblaze SDK** (`genblaze-core`, `genblaze-gmicloud`).  
OpenAI TTS is wrapped inside `GenblazeClient.generate_narration_audio()` — no direct provider calls outside that wrapper.

## Critical Constraints

- **Genblaze is mandatory** — sole media generation layer; judges score on this. Image generation: Genblaze → GMI Cloud Seedream. Audio: OpenAI TTS wrapped in GenblazeClient (no direct openai.audio calls outside genblaze_client.py).
- **B2 stores everything** — input CSV, script, images, narration audio, video, metadata
- `get_settings()` uses `@lru_cache` — call `get_settings.cache_clear()` in tests that need different env vars
- FFmpeg must be installed on the host: Linux `sudo apt-get install ffmpeg` · Windows `winget install ffmpeg`
- SQLite for MVP; PostgreSQL via `DATABASE_URL` env var is the documented upgrade path (ADR-004)
- `FFmpegComposer.compose()` is `async def` — always `await` it; `audio_path` param is now used
- Coverage gate: ≥ **80%** enforced in CI (raised from 70%)

## Testing Strategy

- `tests/unit/` — per-agent unit tests; Genblaze, B2, FFmpeg, OpenAI are all mocked
- `tests/integration/` — API end-to-end with mocked pipeline deps
- `data/synthetic/` — two CSV files committed; use instead of real bank data
- Mock OpenAI TTS in tests: `mocker.patch("backend.media.genblaze_client.OpenAI")` or patch `openai.audio.speech.create`

## B2 Key Layout

```
{user_id}/{session_id}/input/transactions.csv
{user_id}/{session_id}/pipeline/script.json
{user_id}/{session_id}/pipeline/narration.mp3       ← NEW (Phase 2)
{user_id}/{session_id}/pipeline/scenes/scene_00.png … scene_03.png
{user_id}/{session_id}/output/recap_{session_id}.mp4
{user_id}/{session_id}/metadata/session_metadata.json
```

## Session Metadata — models_used (Phase 2)

```json
{
  "llm":        "nvidia-nim/meta/llama-3.1-70b-instruct",
  "image":      "gmi-cloud/seedream-4-0-250828",
  "audio":      "openai/tts-1",
  "compositor": "ffmpeg"
}
```

## SSE Progress Endpoint (Phase 2)

`GET /api/v1/recap/{session_id}/progress` — Server-Sent Events stream.  
Events emitted (in order): `parsing` → `analyzing` → `scripting` → `generating_images` → `composing` → `uploading` → `complete` / `failed`.  
SessionStore has a new `events` JSON column storing the event log.

## Frontend Routes (Phase 2)

- `/` — CSV upload portal (existing, polished with Tailwind)
- `/recap/{session_id}` — Share page: personality, stats, video player, B2 artifact links

## Personality Themes (for UI)

| Personality         | Color             | Icon |
| ------------------- | ----------------- | ---- |
| Financial Builder   | Amber (#F59E0B)   | 🏗️  |
| Financial Explorer  | Teal (#14B8A6)    | 🌍  |
| Financial Achiever  | Purple (#8B5CF6)  | 🏆  |
| Financial Optimizer | Blue (#3B82F6)    | ⚙️  |

## Production Hardening (Phase 2)

- Rate limiting: `slowapi` — 5 uploads per hour per IP on `POST /api/v1/recap/generate`
- CSV byte-level validation: check for printable ASCII / UTF-8 headers, reject binary files
- PostgreSQL: `DATABASE_URL` env var in `config.py`; `SessionStore` uses SQLAlchemy if set, SQLite otherwise
- Coverage gate: 80% (update `pyproject.toml [tool.coverage.report] fail_under = 80`)

## Deployment (Phase 2)

- Backend: Railway (Dockerfile or Procfile) or Render (`render.yaml`)
- Frontend: Vercel (`vercel.json`)
- Env vars required: `GMI_API_KEY`, `NVIDIA_NIM_API_KEY`, `OPENAI_API_KEY`, `B2_KEY_ID`, `B2_APPLICATION_KEY`, `B2_ENDPOINT_URL`, `B2_BUCKET_NAME`, `DATABASE_URL` (optional)

## Hackathon Deadline

Submission due: **August 3, 2026**. Required deliverables: working hosted URL + ≤ 3-min demo video + Devpost form.

## Judging Criteria (all equally weighted)

1. **Real-World Utility** — solves low engagement in banking; clear market (retail banks / fintechs)
2. **Production Readiness** — CI/CD, 80% coverage, rate limiting, structured logging, health endpoint, 6 ADRs
3. **B2 Storage & Data Orchestration** — all artifacts stored + provenance metadata; share page shows B2 layout
4. **Use of Genblaze** — image generation (Genblaze → GMI Cloud) + narration audio (OpenAI TTS via GenblazeClient); two provider types
