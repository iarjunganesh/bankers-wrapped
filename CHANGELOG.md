# Changelog

All notable changes to Banker's Wrapped are documented here.

## [Unreleased]

### Added
- NVIDIA NIM integration — NarrativeAgent uses Llama 3.1 70B via `integrate.api.nvidia.com/v1`; falls back to OpenAI GPT-4o when key is absent
- GMI Cloud image generation via `genblaze-gmicloud` — replaced DALL·E 3 with FLUX2-Dev (1344×768)
- `gmi_api_key` and `gmi_image_model` settings in `config.py`
- NVIDIA NIM and GMI Cloud badges in README
- Mermaid architecture diagrams replacing ASCII art
- `CLAUDE.md` project context file for Claude Code
- `.claude/settings.json` pre-approved command allowlist
- `LICENSE` (MIT), `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`

### Changed
- `FFmpegComposer.compose()` made `async def` — FFmpeg subprocess wrapped with `asyncio.to_thread` to prevent event loop blocking
- `get_settings()` decorated with `@lru_cache()` — `.env` parsed once per process
- CORS: removed `allow_credentials=True`; origins now configurable via `cors_allow_origins` setting
- `SessionStore` lifted to module-level singleton in `recap.py` — `init_db()` runs once on startup
- Genblaze provider: `genblaze-openai` → `genblaze-gmicloud` for image generation
- Removed OpenAI TTS fallback path; ElevenLabs is now the sole TTS provider via Genblaze
- README rewritten to competition quality for Backblaze Generative Media Hackathon 2026

### Fixed
- SQLite connection leak — all `_conn()` calls wrapped with `contextlib.closing()`
- SAVINGS double-counting — `_savings_amount` now filters `amount < 0` to exclude income-side entries
- Empty LLM scene response — `_parse_script` raises `ValueError` immediately rather than crashing FFmpeg later
- Duplicate scene file collision — scene images keyed by `enumerate` index, not LLM-supplied `scene.id`
- Stale CI environment variables aligned with current `config.py` fields

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
