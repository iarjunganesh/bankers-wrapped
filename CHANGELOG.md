# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to Banker's Wrapped are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [Unreleased]

_Targeting **2.0.0** (submission):_

- Demo video (≤ 3 min) recorded and uploaded public to YouTube; wire the URL into the
  "▶ Watch" badge and the Submission Links table (README, `submission/SUBMISSION.md`).
- Devpost submission form completed; add the Devpost project URL alongside the video link.

---

## [1.9.1] — 2026-07-14

Frontend typography + branding fixes so the deployed app matches the brand cards.
No backend behavior change.

### Added

- **Font-independent wordmark** — `frontend/public/wordmark.svg`, the gradient "Wrapped"
  wordmark with its Inter ExtraBold glyphs pre-converted to vector paths. It carries no
  font dependency, so it renders pixel-identical on every browser/OS and stays crisp at any
  DPI. Used on the home header and both recap-page headers. (The banner/signoff cards can't
  be reused directly in the app: `<img>`-referenced SVGs can't load webfonts, and the PNGs
  are fixed 16:9 video cards.)
- **Idle-screen tagline** echoing the signoff card — "One connection. Five scenes. Your
  financial story." + "Powered by Genblaze on Backblaze B2.", with the same bold emphasis.

### Fixed

- **Inter never actually loaded** — `globals.css` referenced `'Inter'` but no `@font-face`,
  `next/font`, or Google Fonts link existed, so every weight silently fell back to
  `system-ui`. Now loaded via `next/font/google` (400/600/700/800) and wired through the
  `--font-inter` variable.
- **"Wrapped" gradient was clipped** — as a full-width block the 5-stop `background-clip:text`
  gradient painted across the whole card while the centered glyphs only covered its middle,
  hiding the amber/teal ends. Resolved by the outlined-SVG wordmark above.
- **Subtitle emphasis** — "Your financial year," is now bold, matching the brand cards.

### Docs

- `assets/demo-cards/README.md`: corrected the stale "Inter/Segoe typography" claim
  (`banner.html`/`signoff.html` now load real Inter via Google Fonts) and fixed the
  PNG re-export command (`--virtual-time-budget` + Windows `file://` path).

---

## [1.9.0] — 2026-07-12

Maintenance + release-hardening pass ahead of submission. No runtime behavior change.

### Changed

- **Dependencies refreshed** (`uv lock --upgrade`): uvicorn 0.51, fastapi 0.139, openai 2.45,
  boto3 1.43.46, mypy 2.2, plus patch-level transitives. No major bumps; the Genblaze
  subpackages (`genblaze-core` 0.3.4, `genblaze-s3` 0.3.4, `genblaze-gmicloud` 0.3.2) were
  already the newest published — the v0.4.0 release wave.
- **Coverage 97.8% → 99.6%** (134 → 148 tests): analytics achievements + ACHIEVER path,
  invalid-category fallback, narrative prompt/NIM/0-scene branches, and recap
  413 / pipeline-failure / malformed-insights / empty-artifacts / progress-callback paths.
- Coverage claim synced 98% → 99% across README, CLAUDE.md, and submission docs;
  regenerated `vo_08-production` + `vo_full-reference` demo voiceover clips to match.

### Fixed

- `config.openai_model` default was a stale `gpt-4o` — it is a fallback `models_used.llm`
  label only, now set to the real chat model and documented as such.
- Clarified that `config.gmi_chat_model` defaults to NIM's free dev tier on purpose
  (prod overrides via `GMI_CHAT_MODEL`); added an ADR-011 cross-reference in ADR-003.
- **Accuracy:** corrected Semantic Kernel references (README badge/diagram/tech-stack,
  ADR-002, `base.py` docstring, scaffold changelog line) — it was never a dependency or
  used; agents are a hand-rolled typed async `BaseAgent` pipeline, now documented as such.

### Docs & assets

- **README restructured** for judges — reordered (What Is This? → Problem → How It Works →
  Architecture → Genblaze → Personality → Tech Stack → Live & Interactive Demo → Screenshots →
  Quick Start → Synthetic Data → Project Structure → Production & Quality); merged Live Demo +
  notebook, and consolidated CI/CD + load testing + the 11-ADR table into one "Production & Quality".
- **Architecture depth extracted** to [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) (pipeline timing,
  B2 storage layout, lifecycle & integrity, provenance manifests); the README keeps the diagram + a
  summary + a link.
- **Theme-aware SVG README banners** — the opening hero and closing sign-off reproduced as vector
  `<picture>` banners (`assets/demo-cards/banner-{light,dark}.svg`, `assets/demo-cards/signoff-{light,dark}.svg`), ~3 KB each,
  replacing ~380 KB PNGs in the README and following GitHub's light/dark toggle. Bold-weight
  emphasis on the tagline (`banner`) now matches the sign-off's existing partial-bold treatment.
- **Demo video title/closing cards** — `assets/demo-cards/banner-{dark,light}.png` and
  `signoff-{dark,light}.png` (1920×1080, sharing base names with their SVG counterparts — same
  brand content, rendered to a video-editor-friendly format from theme-aware HTML sources) for the
  ≤3-min video bookends; `submission/DEMO_SCRIPT.md` given a real-duration, 10-beat cut sheet and a
  two-OBS-recording runbook (a one-time live-pipeline capture jump-cut into the main take) targeting
  2:50–2:55.
- **Brand-themed architecture diagram** — `assets/architecture/architecture-diagram-{dark,light}.svg/.png`,
  rendered from `architecture-diagram.mmd` via `mermaid-cli` with the app's own fonts/background
  tokens (replacing GitHub's generic mermaid theme in the README embed); forces a horizontal
  drill-down layout (top summary row above, dotted expansion below) instead of mermaid-cli's default
  vertical subgraph stacking. Doubles as the demo video's Step 0 asset (no manual screenshot needed).
- **Assets folder reorganized** — `assets/banner-*.svg`/`signoff-*.svg` moved into `assets/demo-cards/`
  (co-located with the video cards they share brand content with); the architecture diagram lives in
  its own `assets/architecture/`. Every reference across README, CHANGELOG, and the submission docs
  updated to match.

---

## [1.8.1] — 2026-07-11

The first live post-flip run exposed that WS-1's chat path could never reach NVIDIA NIM: the
Genblaze chat wrapper always posts to GMI's endpoint, so `nvidia-nim/...`-prefixed ids (and the
documented "NIM fallback") 404'd — only mocked tests exercised the route. Found before any
credits were burned (the 404 bills nothing).

### Fixed

- **Real NVIDIA NIM routing** (`GenblazeClient.generate_script_text`): `nvidia-nim/`-prefixed
  model ids are stripped and redirected to NIM's OpenAI-compatible endpoint via the SDK chat
  wrapper's `base_url` override (new `nvidia_nim_api_key` / `nvidia_nim_base_url` client params).
  Provider provenance is derived from the route actually taken, not the model-id prefix.
- **Automatic NIM fallback now exists** (`NarrativeAgent._try_genblaze`): after the primary
  model exhausts its attempts (provider failure or invalid JSON), one final SDK-routed attempt
  runs against NVIDIA NIM — previously claimed in docs but not implemented.
- **`GMI_CHAT_MODEL` default was invalid**: GMI's catalog serves no `meta-llama/*` models
  (verified via `GET /v1/models`). Production model is now `openai/gpt-5.4-mini`
  ($0.75/$4.50 per M tokens ≈ $0.005/run); both routes live-validated with 1-token probes.
- `llm.cost_usd` in `generation.json` is now computed from GMI's published per-token pricing
  when the SDK reports none (the SDK intentionally returns `cost_usd=None`); NIM runs record $0.

### Changed

- 5 new tests (NIM-fallback success/exhaustion in NarrativeAgent; chat routing +
  cost computation in GenblazeClient); coverage 97.8%.
- Docs sweep: README (pipeline diagram, timing table, tech stack, `models_used` example,
  release badge → `releases/latest`), DEVPOST providers table, COSTS per-run table,
  CLAUDE.md, `.env.example` — all reflect GMI `openai/gpt-5.4-mini` primary + NIM fallback.

---

## [1.8.0] — 2026-07-03

All five v1.7.0-roadmap workstreams shipped (the `v1.7.0` tag marks the roadmap itself; this release is the implementation). Coverage 98% (gate 80%), 135 tests.

### Added

- **WS-2 — B2 as source of truth** ([ADR-008](docs/adr/008-b2-source-of-truth.md)): sessions now survive Railway redeploys.
  - `session_metadata.json` is a **self-contained manifest** — full `InsightsSummary` snapshot, `status`, `processing_time_ms`, `models_used`, and every B2 key (including its own); uploaded **last** so its `b2_keys` map is complete.
  - Flat `index/{session_id}.json` object written to B2 at pipeline start maps `session_id → user_id` (share URLs stay clean).
  - `GET /recap/{id}` and `GET /recap/{id}/download` fall back to the B2 manifest when the SQLite row is missing; presigned URLs are re-minted per request. SQLite is now a cache (ADR-004 amended).
  - `B2Client`: new `download_json`, `exists`, `session_index_key` helpers.
- **WS-3 — B2 lifecycle + artifact integrity** ([ADR-009](docs/adr/009-b2-lifecycle-integrity.md)):
  - `generation.json` now carries an `artifacts` list — **SHA-256 + size for each of the 12 content artifacts** uploaded per session, computed from the exact bytes stored.
  - Bucket retention rule committed as `infra/b2-lifecycle.json` (45-day expiry — outlives the Aug 5–11 judging window for all hackathon sessions) and applied idempotently by `scripts/apply_b2_lifecycle.py`.
- **WS-1 — Genblaze LLM routing** ([ADR-007](docs/adr/007-genblaze-sole-ai-layer.md)): narrative script generation now runs through **Genblaze SDK chat** with provider-prefixed backend models, making 3 of 4 AI steps Genblaze-orchestrated.
  - `GenblazeClient.generate_script_text()` — same non-blocking (`asyncio.to_thread`) + tenacity-retry pattern as image gen; returns text + provenance (provider, model, latency, retries, tokens, `cost_usd`).
  - `NarrativeAgent` is SDK-only for script generation (no direct provider path in-agent). `NARRATIVE_PROVIDER` selects backend model mode via SDK (`genblaze` model id vs `nvidia-nim/<model>`), with schema retry on invalid JSON.
  - `generation.json` carries `llm` provenance and `models_used.llm` reflects the backend model used.
  - Default narrative provider mode is now `genblaze`, with `GMI_CHAT_MODEL` defaulting to `nvidia-nim/meta/llama-3.1-70b-instruct` for NVIDIA NIM via SDK.
- **WS-4 — Plaid sandbox connector** ([ADR-010](docs/adr/010-plaid-sandbox-ingestion.md)): optional "Connect a bank (sandbox)" ingestion path.
  - `backend/ingest/plaid_connector.py`: Plaid REST via httpx (async; no `plaid-python` dep) — link token, public-token exchange, paginated `/transactions/get`, category mapping to our taxonomy, sign-convention flip (Plaid outflow-positive → ours income-positive).
  - Plaid transactions are serialised back to our CSV schema and fed to the **unchanged** pipeline — identical B2 artifact trail, `DocumentAgent` revalidates everything.
  - `POST /api/v1/plaid/link-token` + `POST /api/v1/plaid/exchange` (rate-limited 5/hr/IP, same SSE progress). Feature-flagged: without `PLAID_CLIENT_ID`/`PLAID_SECRET` the routes answer 404 and the app is unchanged; `/health` now reports `plaid_enabled`.
  - Frontend: "🏦 Connect a bank (sandbox)" button (Plaid Link via CDN, loaded on demand), shown only when the backend reports Plaid enabled.
  - Test hermeticity fix: `test_settings` now explicitly blanks Plaid keys so a developer's real `.env` can never trigger live calls in the suite.
- **WS-5 — hardening + polish**:
  - [ADR-011](docs/adr/011-compositor-redesign.md): the v1.6.0 compositor + non-blocking-loop redesign recorded as a decision record.
  - `tests/load/k6_smoke.js`: manual k6 smoke test — /health p95 < 500 ms under 20 VUs; rate limiter must 429 (never 5xx) under /generate abuse.
  - Narrative prompt: Scene 4 advice must name the actual top spending category and cite a concrete number from the data (no generic advice).

### Fixed

- Removed aspirational PostgreSQL claims (no `DATABASE_URL` code path exists): B2 is the source of truth, SQLite is a cache, Postgres stays a documented scale path only.
- B2 lifecycle rule shape: the S3-compatible API requires the `Days` rule paired with an `ExpiredObjectDeleteMarker` `_marker` rule (same prefix).
- `/health` now reports the real app version (was hardcoded `1.0.0`) and `plaid_enabled`.

### Changed

- Coverage 93% → **98%** (135 tests): SSE progress stream, B2 helper, Plaid HTTP/pagination/CSV-quoting, ffprobe, provider-init, and B2-fallback edge cases now covered.

---

## [1.7.0] — 2026-06-30 (roadmap tag — planning only)

The `v1.7.0` tag reserved the version for five planned workstreams — decision records ADR-007–011.
**All five were implemented and shipped in [1.8.0].**

### Planned

- **WS-1 — Genblaze as sole AI layer** ([ADR-007](docs/adr/007-genblaze-sole-ai-layer.md)) — route the narrative LLM through Genblaze (GMI chat/reasoning) so 3 of 4 AI steps go through it; optional Genblaze video scene. *Needs GMI credit top-up.*
- **WS-2 — B2 as source of truth** ([ADR-008](docs/adr/008-b2-source-of-truth.md)) — self-contained session manifest on B2 + `get_recap` fallback, so share links survive Railway redeploys (fixes the ephemeral-SQLite gap). *No credits.*
- **WS-3 — B2 lifecycle + integrity** ([ADR-009](docs/adr/009-b2-lifecycle-integrity.md)) — retention rule + SHA-256 per artifact in `generation.json`. *No credits.*
- **WS-4 — Plaid sandbox connector** ([ADR-010](docs/adr/010-plaid-sandbox-ingestion.md)) — optional "connect a bank" ingestion path; CSV stays default. *No credits.*
- **WS-5 — Submission polish + hardening++** — 7th ADR, k6 load test, security review, CI badge, honest Postgres claim, demo assets, utility signal.

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

- **Share links no longer expire** (`GET /recap/{id}`) — the endpoint returned the presigned video/thumbnail URLs minted at generation time, which expire after `b2_presigned_url_expiry` (1 h), so any share page or notebook Scenario C opened later showed a dead video. Now it **regenerates presigned URLs from the stored B2 keys on every request**, so links stay valid indefinitely.
- **Session DB path is configurable** (`SESSION_DB_PATH` env) so the SQLite store can live on a Railway persistent volume and survive redeploys (Railway's default filesystem is ephemeral — sessions were wiped on every deploy).
- **Demo notebook (`DEMO_RUNBOOK.ipynb`) refreshed** for v1.6.0: parallel-image timings (~2–3 min, was ~4–5), correct artifact count (14 files / 10 types), and Scenario C durability notes.
- **Demo notebook `run_pipeline` now drives the async backend correctly** — it expected a synchronous full response, but `POST /generate` returns `202 + {session_id}` and runs in the background, so `print_summary` hit `KeyError: 'insights'`. It now POSTs, then **polls `GET /recap/{id}`** until ready (with a 429 rate-limit message and a timeout). Added `matplotlib` + `ipykernel` to the dev group so the notebook's charts and kernel actually work from a clean clone.
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

- Initial project scaffold — FastAPI backend with a 4-agent typed async pipeline
- `DocumentAgent` — CSV parse + normalise → `List[Transaction]`
- `AnalyticsAgent` — financial metrics + Financial Personality classification
- `NarrativeAgent` — GPT-4o structured JSON script (4 scenes)
- `MediaAgent` — Genblaze orchestration → ElevenLabs TTS + DALL·E 3 images + FFmpeg → MP4
- Backblaze B2 storage — structured `{user_id}/{session_id}/` key layout with provenance metadata
- Financial Personality system — Builder · Optimizer · Explorer · Achiever
- Synthetic demo datasets committed to `data/synthetic/`
- 6 Architecture Decision Records in `docs/adr/`
- CI pipeline — ruff lint → mypy type-check → pytest (≥70% coverage gate) → Codecov
