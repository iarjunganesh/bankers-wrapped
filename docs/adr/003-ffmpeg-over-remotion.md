# ADR-003: FFmpeg for Composition; Runway ML Excluded
**Status:** Accepted | **Date:** 2026-06-25

## Decision
FFmpeg for video composition. Runway ML and Luma AI excluded from hackathon scope.

## Rationale
- Runway/Luma add latency, quota risk, cost with no judging advantage
- Static images + narration = complete, compelling demo
- FFmpeg is industry standard: reliable, fast, no API dependency
- `filter_complex` with chained `xfade=transition=fade:duration=0.5` between scenes + global `fade=t=in` / `fade=t=out` produces cinema-quality transitions in a single command invocation
