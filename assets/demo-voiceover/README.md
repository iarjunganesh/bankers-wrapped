# Demo Voiceover

AI-narrated voiceover for the ≤3-min submission video, generated with the project's
**own OpenAI `tts-1`** (voice **`nova`** — kept distinct from the recap's `alloy` so the
product's voice stands out when the recap plays). Text is verbatim from
[`submission/DEMO_SCRIPT.md`](../../submission/DEMO_SCRIPT.md).

- `vo_00-intro … vo_09-close.mp3` — one clip per beat (~1:24 total, measured via ffprobe), for
  precise placement against the screen recording. `vo_00-intro` narrates over a GitHub repo
  screenshot ("What Is This?" / "The Problem"), opening the video on real project context before
  the CSV hook.
- `vo_full-reference.mp3` — the whole narration as one continuous track (reference/fallback).

Regenerate or tweak wording via [`scripts/generate_demo_voiceover.py`](../../scripts/generate_demo_voiceover.py)
(the narration text lives there — keep it in sync with the "Narration Script" table in
[`submission/DEMO_SCRIPT.md`](../../submission/DEMO_SCRIPT.md)); cost ≈ $0.05–0.10 on OpenAI
(does not touch the GMI reserve).
