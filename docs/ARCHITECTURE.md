# Architecture — Deep Dive

Reference detail for the Banker's Wrapped pipeline: per-step timing, the full Backblaze B2 storage layout, retention & integrity, and the machine-readable provenance manifests. For the high-level pipeline diagram and overview, see the [README](../README.md#architecture).

---

## Pipeline Timing

Measured on a live run against `transactions_jan_2026.csv` (22 transactions, 5 scenes):

| Step | Agent / Service | Time |
| --- | --- | --- |
| CSV parse + normalise | DocumentAgent | < 1 s |
| Spending analytics + personality | AnalyticsAgent | < 1 s |
| Narrative script (5 scenes) | NarrativeAgent · Genblaze chat → GMI `openai/gpt-5.4-mini` (NIM fallback) | ~6 s |
| Scene images × 5 | MediaAgent · Genblaze → GMI Cloud Seedream (parallel, retry ×3) | ~45–180 s |
| Voice narration | GenblazeClient → OpenAI TTS (tts-1, alloy, retry ×3) | ~17 s |
| MP4 composition | FFmpeg (H.264/AAC, segment + concat, dip-to-black) | ~6 s |
| B2 uploads (14 files) | Backblaze B2 | ~3 s |
| **Total wall-clock** | | **~2–4 min** |

Image generation dominates. Since v1.6.0 the blocking image-gen call is offloaded to a worker thread, so `asyncio.gather` truly dispatches all 5 scenes concurrently (previously the event loop serialized them). Wall time now depends on GMI Cloud's server-side concurrency per API key. Per-step latency and retry counts are recorded in `generation.json`.

---

## B2 Storage Layout

Every recap produces **14 files** (10 artifact types) — B2 is the complete source of truth for the entire media pipeline:

```text
bankers-wrapped-assets/
├── index/{session_id}.json           ← flat session→user index (ADR-008: B2 is the source of truth)
└── {user_id}/{session_id}/
    ├── input/
    │   └── transactions.csv
    ├── pipeline/
    │   ├── script.json           ← narrative script (5 scenes)
    │   ├── analytics.json        ← financial insights snapshot
    │   ├── prompts.json          ← image prompts + SHA-256 hashes per scene
    │   ├── generation.json       ← model, provider, latency, retry count per step
    │   ├── thumbnail.jpg         ← scene 0 (a JPEG) reused as recap preview image
    │   ├── narration.mp3         ← OpenAI TTS (alloy voice)
    │   └── scenes/
    │       ├── scene_00.jpg … scene_04.jpg   ← GMI Cloud Seedream
    ├── output/
    │   └── recap_{session_id}.mp4   ← H.264 yuv420p + faststart / AAC, dip-to-black transitions
    └── metadata/
        └── session_metadata.json    ← top-level provenance record
```

---

## B2 Data Lifecycle & Integrity

- **Retention (ADR-009):** a bucket lifecycle rule (committed as [`infra/b2-lifecycle.json`](../infra/b2-lifecycle.json), applied idempotently via `uv run python scripts/apply_b2_lifecycle.py`) expires session artifacts **45 days after upload** — long enough that every hackathon-period session outlives the judging window, short enough that storage stays near zero afterwards.
- **Integrity:** `generation.json` records a **SHA-256 per stored artifact** (key, size, hash — 12 content artifacts per session). To verify any download: `sha256sum scene_00.jpg` and compare against the `artifacts` entry for that key. The two manifests themselves (`generation.json`, `session_metadata.json`) are the verification root and are not self-listed.

---

## Provenance Metadata

Every run produces **four machine-readable provenance files** in B2:

**`session_metadata.json`** — top-level record:

```json
{
  "session_id": "uuid",
  "user_id":    "uuid",
  "created_at": "2026-01-15T14:22:08Z",
  "pipeline_version": "1.0.0",
  "models_used": {
    "llm":        "gmi-cloud/openai/gpt-5.4-mini",
    "image":      "gmi-cloud/seedream-4-0-250828",
    "audio":      "openai/tts-1",
    "compositor": "ffmpeg"
  },
  "input_hash":         "sha256:a3f…",
  "output_url":         "https://f000.backblazeb2.com/…",
  "processing_time_ms": 47230,
  "synthetic_data":     false
}
```

**`generation.json`** — per-step model telemetry (latency, retries, manifest hashes):

```json
{
  "images": [
    { "scene_idx": 0, "model": "seedream-4-0-250828", "provider": "gmi-cloud",
      "latency_ms": 32400, "retry_count": 0, "manifest_hash": "sha256:…", "success": true }
  ],
  "audio":      { "model": "tts-1", "provider": "openai", "latency_ms": 6900, "retry_count": 0 },
  "compositor": { "tool": "ffmpeg", "scenes": 5, "latency_ms": 2100, "success": true }
}
```

**`prompts.json`** — all image prompts with SHA-256 hashes for full reproducibility.

**`analytics.json`** — financial insights snapshot (income, expenses, savings rate, personality).
