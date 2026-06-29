# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to Banker's Wrapped are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [Unreleased]

---

## [1.6.0] — 2026-06-29

### Changed

- **FFmpeg compositor rewritten: monolithic xfade → memory-bounded segment + concat** (`ffmpeg_composer.py`). The single `xfade` `filter_complex` buffered every looped input's frames until its staggered transition offset — several GB at 1792×1024 — and the OOM-killer SIGKILL'd it (`returncode -9`, 0 frames) on memory-limited containers, even after capping threads. The new compositor:
  1. **renders each scene to its own short MP4 segment** — only one image is in RAM at a time, so peak memory is a single small encode (~300 MB) instead of GBs;
  2. **concatenates the segments with the concat demuxer using `-c:v copy`** (stream copy — no decode, near-zero memory) and muxes the narration.
  Peak memory dropped from several GB to ~300 MB; it now runs on any container size (validated end-to-end against real B2 assets via `scripts/recompose.py`).
- **Transitions: crossfade → dip-to-black.** True crossfades require holding two scenes' frames simultaneously — the exact buffering that OOMs — so each segment now fades in from / out to black, giving a memory-free cinematic dip between scenes. Output stays browser-safe (`yuv420p`, `+faststart`, CFR 25 fps, AAC).
- **Per-scene duration = narration_length / N** (float), so the slideshow covers the narration exactly (no `-shortest` trimming artefacts).
- `scripts/recompose.py` comparison labels clarified (`segments (new)` vs `old-xfade`) to match the new compositor.

### Fixed

- **Event loop no longer blocked by synchronous I/O during the pipeline** — `generate_scene_image` ran the genblaze pipeline `.run()` and a sync `httpx.Client` fetch directly inside an `async` function, freezing the loop for the entire ~3–4 min image phase. That starved the SSE progress stream: the connection dropped and the frontend hung on "Writing narrative script" even though the backend completed. Fixes:
  - **`genblaze_client.generate_scene_image`** — blocking genblaze run + HTTP fetch moved into `asyncio.to_thread`. Side benefit: the 5 image generations now actually run **in parallel** via the existing `asyncio.gather` (image phase ~3.3 min → ~40–50 s; total pipeline ~5.4 min → ~2.5–3 min).
  - **`MediaAgent`** — all 13 synchronous boto3 B2 calls (`upload_bytes`/`upload_json`/`presigned_url`) offloaded via small `_b2_*` `to_thread` helpers.
  - **`GET /recap/{id}/download`** — the blocking B2-download + ZIP build offloaded via `asyncio.to_thread`, so a ZIP download no longer stalls every other request.
  - Left synchronous intentionally: ffprobe (sub-ms local read), SQLite session store (sub-ms local), key-builders / pure logic / tests.

---

## [1.5.0] — 2026-06-28

### Fixed

- **FFmpeg OOM-kill on Railway (0 frames, encoder opened then died in ~1 s)** (`ffmpeg_composer.py`) — libx264 auto-detects the **host** core count (32 on Railway), not the container's allocation, and spawned 32 thread contexts whose buffers blew past the container memory limit → SIGKILL at encoder init. Capped concurrency with `-filter_complex_threads 2` and `-threads 4`; negligible speed impact on a ~75 s video. Also log the FFmpeg `returncode` on failure (137 = SIGKILL/OOM, 139 = SIGSEGV) for unambiguous diagnosis.
- **Progress timer for active step** (`page.tsx`) — each SSE event marks a step's *start*, but the UI treated arrival as *done*, so "Writing narrative script" flipped to ✅ instantly and showed no timer during the ~30 s NIM call. Now the latest-started step is **active** (live timer counting from its own start event) and a step is **done** only once a later step starts. Removed the `generating_images`/`scripting` special-casing — it falls out naturally.
- **FFmpeg xfade "constant frame rate" failure on Railway** (`ffmpeg_composer.py`) — looped image inputs (`-loop 1`) have an undefined rate (`1/0`); stricter ffmpeg builds (Railway's apt package vs. local 8.1.1) reject this with *"The inputs needs to be a constant frame rate; current rate of 1/0 is invalid"* → 0-frame output, pipeline `failed`. Fixed by setting `-framerate 25` on each input **and** `fps=25` in each scene's filter chain so xfade receives true CFR. Verified by rebuilding the failed session's B2 assets locally (`avg_frame_rate=25/1`).
- **Browser playback "file is corrupt"** (`ffmpeg_composer.py`) — output was H.264 **High 4:4:4 / `yuvj444p`** because seedream JPEGs are full-range 4:4:4 and the in-filter `format=yuv420p` did not survive xfade format negotiation. Browsers cannot decode 4:4:4 H.264 (VLC can — hence "plays locally, corrupt on web"). Forced `-pix_fmt yuv420p` as an explicit output option → `High` / 4:2:0, decodable everywhere. Added `-movflags +faststart` so the `moov` atom is at the front for progressive streaming. Regression test asserts both flags.
- **Composer migrated to xfade `filter_complex`** as the permanent path (was concat demuxer). Scene duration now auto-stretches from the probed audio length so the video always covers the full narration; `-shortest` trims to the exact audio end — fixes narration being cut off (~40 s) on longer scripts.
- **`ffprobe` path resolution** — deriving `ffprobe` from `ffmpeg` via a naive `replace("ffmpeg","ffprobe")` mangled install directories such as `ffmpeg-8.1.1-full_build`; now replaces only the filename. Same bug fixed in `scripts/recompose.py`.
- **Thumbnail key extension** `.png` → `.jpg` (`b2_client.py`) — scene 0 is a JPEG; the `.png` key produced a content-type mismatch and a broken share-page thumbnail.
- **Progress timer double-count** (`page.tsx`) — per-step duration was measured against the *previous* event, so "Generating scenes" and "Composing video" both counted the same span (the "6m30s → 5m2s" jump). Now measured forward: `(next step start) − (this step start)`. Pipeline timer also starts on the first SSE event (safe against React batched updates that skipped `length === 1`).
- **FFmpeg 0-frame bug (root cause of 500 on Railway)** — `n_total = n + 1` without a matching lavfi input caused xfade to reference non-existent `[v5]`; added branded ending card (dark overlay + `drawtext` title) as the 6th input.
- **Dockerfile** — added `fonts-liberation` so `drawtext` finds a system font on Debian slim.
- **SSE race condition** (`progress.py`) — frontend opens SSE before the POST creates the session; previously returned 404 immediately ("spinner hangs forever"). Now polls up to 10 s for session creation.
- **SSE final event `ts: 0`** — terminal event now uses `time.time()` so per-step duration is correct for the last stage.
- **Demo button** — `fetch("/data/synthetic/…")` now has `ok` check + `.catch()` to surface errors visibly instead of silently sending a garbage blob.

### Added

- **`scripts/recompose.py`** — offline tool that downloads a session's existing B2 assets and rebuilds the MP4 locally with **zero API cost** (no image/LLM/TTS calls). Used to isolate and prove the pixel-format fix. Supports `--prefix USER_ID/SESSION_ID` (paste straight from the B2 console), `--ffmpeg PATH`, graceful `NoSuchKey` messaging, and UTF-8 console output on Windows.
- **Video `poster` thumbnail** — the recap thumbnail is set as the `<video poster>` on both the main and share pages, so the preview frame shows instantly while the file buffers.
- **Per-step latency** (`page.tsx` + `globals.css`) — each completed step shows elapsed time (e.g. `44.4s`, `1m 4s`) from consecutive SSE timestamps. Steps container widened to 360 px; `.bw-step-duration` class added.
- **`FFMPEG_BIN` config** (`config.py` + `media_agent.py`) — override FFmpeg binary path via env var without rebuilding.
- **README Interactive Demo Notebook section** — scenario table + quickstart added before "What Is This?" so it's the first thing judges see.

### Changed

- **Progress UI** (`page.tsx`) — collapsed the five per-scene rows into a single "Generating scenes + narration — X/5 scenes" sub-label; that step stays active (⏳) until `composing_video` fires (the `generating_images` event marks the *start* of media work). The "Uploading all artifacts" label corrected to "Saving recap video to Backblaze B2" (all `pipeline/` assets are already uploaded during scene generation). Estimated-time weights retuned to a realistic ~5 min total (observed 4–7 min).

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
