# Banker's Wrapped — Claude Code Context

## Project

AI-powered financial storytelling platform entered in the **Backblaze Generative Media Hackathon 2026**. Target: Grand Prize.

Upload a CSV → 4-agent pipeline → personalized 60-second MP4 recap video stored on Backblaze B2.

## Key Commands

```bash
make install   # poetry install
make dev       # uvicorn :8000 (hot-reload)
make test      # pytest tests/unit --cov=backend --cov-fail-under=70
make lint      # ruff check . && mypy backend/
make demo      # full pipeline with data/synthetic/transactions_jan_2026.csv
```

## Architecture

4-agent Semantic Kernel pipeline — each agent is a typed async `BaseAgent`:

1. `DocumentAgent` — CSV parse + normalise → `List[Transaction]`
2. `AnalyticsAgent` — insights + Financial Personality → `FinancialInsights`
3. `NarrativeAgent` — NVIDIA NIM (Llama 3.1 70B) structured script → `NarrativeScript` (4 scenes)
4. `MediaAgent` — Genblaze → ElevenLabs (TTS) + GMI Cloud FLUX (images) + FFmpeg → `recap.mp4` → B2

All AI media calls route through the **Genblaze SDK** (`genblaze-core`, `genblaze-gmicloud`, `genblaze-elevenlabs`). No direct provider calls for media generation.

## Critical Constraints

- **Genblaze is mandatory** — sole media generation layer; judges score on this
- **B2 stores everything** — input CSV, script, audio, images, video, metadata
- `get_settings()` uses `@lru_cache` — call `get_settings.cache_clear()` in tests that need different env vars
- FFmpeg must be installed on the host (`sudo apt-get install ffmpeg`)
- SQLite for MVP; PostgreSQL is the documented upgrade path (ADR-004)
- `FFmpegComposer.compose()` is `async def` — always `await` it

## Testing Strategy

- `tests/unit/` — per-agent unit tests; Genblaze, B2, FFmpeg are all mocked
- `tests/integration/` — API end-to-end with mocked pipeline deps
- `data/synthetic/` — two CSV files committed; use instead of real bank data
- Coverage gate: ≥ 70% enforced in CI

## B2 Key Layout

```
{user_id}/{session_id}/input/transactions.csv
{user_id}/{session_id}/pipeline/script.json
{user_id}/{session_id}/pipeline/narration.mp3
{user_id}/{session_id}/pipeline/scenes/scene_00.png … scene_03.png
{user_id}/{session_id}/output/recap_{session_id}.mp4
{user_id}/{session_id}/metadata/session_metadata.json
```

## Hackathon Deadline

Submission due: **August 3, 2026**. Required deliverables: working hosted URL + ≤ 3-min demo video.
