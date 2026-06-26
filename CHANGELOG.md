# Changelog

All notable changes to Banker's Wrapped are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [Unreleased]

---

## [1.1.0] — 2026-06-26

### Added

- NVIDIA NIM integration — NarrativeAgent uses Llama 3.1 70B via `integrate.api.nvidia.com/v1`; falls back to OpenAI GPT-4o when key is absent
- GMI Cloud image generation via `genblaze-gmicloud` — scene images via Seedream 4.0 (1344×768)
- `gmi_api_key` and `gmi_image_model` settings in `config.py`
- Parallel image generation — all 4 scenes generated concurrently via `asyncio.gather` (4× speedup)
- NVIDIA NIM and GMI Cloud badges in README
- Mermaid architecture diagrams replacing ASCII art
- Pipeline timing table in README (measured: ~195 s end-to-end on live providers)
- `CLAUDE.md` project context file for Claude Code
- `.claude/settings.json` pre-approved command allowlist
- `LICENSE` (MIT), `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`
- `scripts/start_demo.ps1` / `stop_demo.ps1` — Windows demo stack launcher
- `notebooks/DEMO_RUNBOOK.ipynb` — interactive demo with multiple scenario walkthroughs

### Changed

- Image model: `Flux2-Dev` → `seedream-4-0-250828` (Seedream 4.0) — 40 s vs >300 s per image
- `pipeline_timeout_image`: 120 s → 300 s to match actual GMI Cloud queue latency
- `FFmpegComposer.compose()` made `async def` — FFmpeg subprocess wrapped with `asyncio.to_thread`
- FFmpeg concat file uses `.as_posix()` paths — fixes Windows backslash encoding bug
- `get_settings()` decorated with `@lru_cache()` — `.env` parsed once per process
- `logging.basicConfig(force=True)` — all stdlib logging routed to stdout; `start_demo.ps1` merges stderr→stdout via `2>&1`
- CORS: removed `allow_credentials=True`; origins now configurable via `cors_allow_origins` setting
- `SessionStore` lifted to module-level singleton in `recap.py` — `init_db()` runs once on startup
- Genblaze provider: `genblaze-openai` → `genblaze-gmicloud` for image generation
- README rewritten to competition quality for Backblaze Generative Media Hackathon 2026
- Dependency manager: poetry → **uv** (`uv sync --group dev`)

### Removed

- **ElevenLabs TTS** — removed entirely (`genblaze-elevenlabs`, `elevenlabs` packages uninstalled)
  - `synthesize_narration()` and `AudioResult` removed from `GenblazeClient`
  - Audio track removed from FFmpeg compose step (video is now a silent slideshow)
  - `elevenlabs_api_key`, `elevenlabs_voice_id`, `elevenlabs_model`, `pipeline_timeout_audio` removed from `Settings`
  - Narration MP3 removed from B2 key layout
- `data/synthetic/README.md` — content merged into main README

### Fixed

- Genblaze SDK usage: `GMICloudImageProvider` constructor takes no `output_dir`; assets expose `.url` not `.path`; `Pipeline.run()` returns `PipelineResult`, not a tuple
- `raise_on_failure=True` added to all `Pipeline.run()` calls — surfaces real SDK errors instead of `list index out of range`
- SQLite connection leak — all `_conn()` calls wrapped with `contextlib.closing()`
- SAVINGS double-counting — `_savings_amount` now filters `amount < 0` to exclude income-side entries
- Empty LLM scene response — `_parse_script` raises `ValueError` immediately rather than crashing FFmpeg later
- Duplicate scene file collision — scene images keyed by `enumerate` index, not LLM-supplied `scene.id`
- Stale CI environment variables aligned with current `config.py` fields
- Windows console `UnicodeEncodeError` in `demo_run.py` — replaced `✓`/`✗` with ASCII `[OK]`/`[MISMATCH]`

## [1.0.0] — 2026-06-01

### Added

- Initial project scaffold — FastAPI backend with 4-agent Semantic Kernel pipeline
- `DocumentAgent` — CSV parse + normalise → `List[Transaction]`
- `AnalyticsAgent` — financial metrics + Financial Personality classification
- `NarrativeAgent` — GPT-4o structured JSON script (4 scenes)
- `MediaAgent` — Genblaze orchestration → ElevenLabs TTS + DALL·E 3 images + FFmpeg → MP4
- Backblaze B2 storage — structured `{user_id}/{session_id}/` key layout with provenance metadata
- Financial Personality system — Builder · Optimizer · Explorer · Achiever
- Synthetic demo datasets committed to `data/synthetic/`
- 6 Architecture Decision Records in `docs/adr/`
- CI pipeline — ruff lint → mypy type-check → pytest (≥70% coverage gate) → Codecov
