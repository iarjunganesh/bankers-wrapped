# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to Banker's Wrapped are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [Unreleased]

---

## [1.4.0] — 2026-06-28

### Added

- **Full asset manifest** — B2 now stores 10 artifact types per session: `analytics.json` (financial insights snapshot), `prompts.json` (image prompts + SHA-256 hashes per scene), `generation.json` (model, provider, latency\_ms, retry\_count per pipeline step), `thumbnail.png` (scene 0 reused as preview image)
- **Tenacity retry** — all Genblaze media calls (`generate_scene_image`, `generate_narration_audio`) wrapped with 3-attempt exponential backoff (2–30 s). `retry_count` and `latency_ms` tracked in `ImageResult` / `AudioResult`
- **5-scene cinematic narrative** — `NarrativeAgent` now requests a 5-act script: Opening / Personality Reveal → Big Achievement → Spending Insight → Personalized Advice → Motivational Close
- **FFmpeg xfade transitions** — `FFmpegComposer` rewritten to `filter_complex` pipeline: 0.5 s crossfade between every scene pair + global 0.5 s fade-in / fade-out
- **SSE stages** `composing_video` and `uploading_to_b2` added; emitted from `MediaAgent` via `progress_callback` (7 stages total)
- **Download ZIP endpoint** — `GET /api/v1/recap/{session_id}/download` streams an in-memory ZIP containing all B2 artifacts for the session
- `thumbnail_url` field added to `RecapResponse` and stored in session metadata
- `B2Client.download_bytes()` — reads an object body from B2 (used by ZIP endpoint)
- Frontend: thumbnail image on main and share pages, "Download full package" ZIP button, full B2 key paths per artifact, 7-step SSE progress bar, scene + artifact count in footer
- 93 tests, 93% coverage (gate: 80%)

### Changed

- `NarrativeAgent` user prompt updated to request 5-scene JSON
- `MediaAgent.__init__` now accepts optional `progress_callback: Callable[[str, str], None]`
- `MediaAgentInput` gains optional `analytics_output: AnalyticsAgentOutput | None = None`
- `MediaAgentOutput` gains `thumbnail_url: str`
- `FFmpegComposer.compose()` uses single `-filter_complex` command (replaces concat demuxer)

---

## [1.3.0] — 2026-06-26

### Added

- `GET /api/v1/recap/{session_id}` — public share endpoint; returns full `RecapResponse` from session store
- Public share page at `/recap/[session_id]` — personality badge, stats, video player, B2 artifact list, copy link, CTA

### Changed

- README: project structure, pipeline timing table corrected to ~210 s from prod logs, narration row added
- SUBMISSION.md: share page step added to demo script
- CLAUDE.md: Phase 2 marked complete; all API endpoints documented

### Fixed

- ADR-001 updated to document both provider types (images + audio)

---

## [1.2.1] — 2026-06-26

### Fixed

- Dockerfile: removed `startCommand` from `railway.json`; fixed `$PORT` shell expansion in `CMD`
- Docker layer cache: `COPY README.md` moved before `uv sync` to avoid hatchling build error

---

## [1.2.0] — 2026-06-26

### Added

- **Voice narration** — `GenblazeClient.generate_narration_audio()` wraps OpenAI TTS (tts-1, alloy); MediaAgent joins all scene text, generates `narration.mp3`, uploads to B2, passes `audio_path` to FFmpeg
- **SSE pipeline progress** — `SessionStore.append_event` / `get_events` (JSON `events` column, auto-migrated); `GET /api/v1/recap/{session_id}/progress` streams `text/event-stream` at 500 ms poll; 5 stages: `parsing → analyzing → scripting → generating_images → uploading`
- `X-Session-ID` header on POST response so frontend can subscribe to SSE before pipeline returns
- Frontend: live step-by-step SSE progress list (✅ done / ⏳ active / ○ pending); personality badges with per-theme CSS variables; drag-and-drop upload, demo dataset button, video player, B2 artifact panel
- **Rate limiting** — `slowapi`: 5 uploads/hour per IP (disabled in tests via `limiter.enabled = False`)
- **Binary CSV validation** — magic-byte check rejects PNG/JPEG/GIF/ZIP/PDF even with `.csv` extension
- Coverage gate raised 70% → 80%
- Dockerfile, `railway.json`, `render.yaml`, `vercel.json` — production deployment configs
- `scripts/start_demo.sh` / `stop_demo.sh` (Bash) for Railway + Vercel local preview

### Changed

- `FFmpegComposer.compose()` signature: `audio_path` parameter now used (was ignored)
- Session metadata: `insights` + `processing_time_ms` stored on complete

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
