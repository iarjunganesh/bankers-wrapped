# ADR-003: FFmpeg for Composition; Runway ML Excluded
**Status:** Accepted (implementation revised in v1.6.0) | **Date:** 2026-06-25

## Decision
FFmpeg for video composition. Runway ML and Luma AI excluded from hackathon scope.

> **Update (v1.6.0):** the core decision (FFmpeg over hosted video models) stands, but the
> *implementation* below changed. The monolithic `xfade filter_complex` OOM-killed on
> memory-limited containers (it buffers every looped input's frames). It was replaced by a
> **memory-bounded segment + concat** compositor with **dip-to-black** transitions (no
> crossfade, no `drawtext` ending card). See CHANGELOG 1.6.0 and [ADR-011](011-compositor-redesign.md)
> for the redesign. The rationale below is retained as the original decision record.

## Rationale
- Runway/Luma add latency, quota risk, cost with no judging advantage
- Static images + narration = complete, compelling demo
- FFmpeg is industry standard: reliable, fast, no API dependency
- `filter_complex` with chained `xfade=transition=fade:duration=0.5` between all 6 inputs (5 scenes + branded ending card) + global `fade=t=in` / `fade=t=out` produces cinema-quality transitions in a single command invocation
- Ending card: 3-second dark overlay with `drawtext` title and B2 attribution (requires `fonts-liberation` on host)
