# ADR-011: Memory-Bounded Segment+Concat Compositor and a Non-Blocking Event Loop
**Status:** Accepted (shipped in v1.6.0; recorded retroactively per WS-5) | **Date:** 2026-06-29

## Context
Two production failures surfaced when the pipeline moved from a laptop to a
memory-limited Railway container:

1. **The video compositor was OOM-killed.** The original design was a single
   FFmpeg `xfade` `filter_complex` over N looped image inputs. Each input's
   frames are buffered until its staggered transition offset — several GB at
   1792×1024 — so the kernel OOM-killer SIGKILL'd FFmpeg (`returncode -9`,
   zero frames written). Capping `-threads` did not help: the buffering is
   inherent to the graph shape, not the parallelism.
2. **The SSE progress stream froze while the backend kept working.** Image
   generation and B2 uploads were synchronous calls inside `async` functions,
   blocking the event loop for minutes, starving the progress stream until the
   connection dropped — and silently serialising the "parallel" image jobs.

## Decision
1. **Compose per-scene segments, then concat with stream copy.** Each scene is
   rendered to its own short MP4 (one image in RAM at a time, sequential;
   `fade` in/out to black), then joined with the concat demuxer using
   `-c:v copy` (no re-decode) while muxing narration. Crossfades were dropped
   deliberately: blending two scenes requires holding both in memory — the
   exact buffering that OOM'd. Dip-to-black is the memory-free cinematic
   equivalent.
2. **Offload every blocking call with `asyncio.to_thread`.** Genblaze image
   generation, all boto3/B2 calls, FFmpeg/ffprobe subprocesses, and ZIP
   assembly run in worker threads. `asyncio.gather` then dispatches the 5
   image generations truly in parallel.

## Consequences
- Peak compositor memory: several GB → **~300 MB**; runs in a 0.5 GB container.
- Full-run wall time: ~5 min → **~2–3 min** (images actually parallel).
- Browser compatibility is enforced per segment (`-pix_fmt yuv420p`, CFR 25
  fps, `+faststart`) because seedream emits full-range 4:4:4 JPEGs that
  otherwise produce a High 4:4:4 stream browsers reject.
- Transitions are dip-to-black, not crossfade — an accepted aesthetic trade
  for unbounded-input safety.

## Alternatives considered
- Larger container (more RAM) — masks the design flaw, costs money, still
  fails at higher scene counts or resolutions.
- Two-pass tree of pairwise xfades — halves peak memory but keeps decode
  passes and complexity; dip-to-black made the whole class of problem moot.
- Keeping blocking calls and widening SSE timeouts — treats the symptom;
  the loop must never be blocked in an async service.
