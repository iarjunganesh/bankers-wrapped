"""
Generate the demo-video voiceover clips via the project's own OpenAI TTS path
(GenblazeClient.generate_narration_audio — no direct openai.audio calls, same
rule as the production pipeline).

Narration text below is the source of truth; keep it in sync with the
"Narration Script" table in submission/DEMO_SCRIPT.md — whichever one you
edit, update the other and re-run this script so the committed MP3s, their
measured durations, and the documented beat timeline never drift apart.

Usage:
    python scripts/generate_demo_voiceover.py
    python scripts/generate_demo_voiceover.py --voice nova --model tts-1
    python scripts/generate_demo_voiceover.py --beat hook   # regenerate one clip

Cost: ~$0.05-0.10 total on OpenAI TTS (tts-1, ~$15/1M chars) — does not touch
the GMI Cloud reserve used for live pipeline runs.
"""

from __future__ import annotations

import argparse
import asyncio
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from backend.config import get_settings  # noqa: E402
from backend.media.genblaze_client import GenblazeClient  # noqa: E402

OUTPUT_DIR = ROOT / "assets" / "demo-voiceover"

# (beat slug, filename stem, narration text) — order matches the "Final beat
# timeline" table in submission/DEMO_SCRIPT.md.
BEATS: list[tuple[str, str, str]] = [
    (
        "intro",
        "vo_00-intro",
        "Banks generate mountains of transaction data but deliver it as an "
        "unreadable table. Customers disengage. Banker's Wrapped turns that "
        "data into a personalized, narrated recap video — Genblaze is the "
        "sole AI layer, Backblaze B2 the source of truth for every session.",
    ),
    (
        "hook",
        "vo_01-hook",
        "Here's the raw material — just rows, dates, and numbers.",
    ),
    (
        "reveal",
        "vo_02-reveal",
        "See it live, right now — no mockup, no slides.",
    ),
    (
        "ingestion",
        "vo_03-ingestion",
        "Connect a bank in one click through Plaid, or just upload a CSV. "
        "Same pipeline either way — zero friction, zero forking.",
    ),
    (
        "pipeline",
        "vo_04-pipeline",
        "Four typed agents take it from there — parsing, analytics, a "
        "narrative script, and scene generation — all routed through the "
        "Genblaze SDK. GMI Cloud Seedream paints five scenes in parallel, "
        "OpenAI TTS narrates them, and FFmpeg composes the final video, "
        "live, in under two minutes.",
    ),
    (
        "payoff",
        "vo_05-payoff",
        "Meet the Financial Builder — your personality, your story, "
        "playing right now.",
    ),
    (
        "b2",
        "vo_06-b2",
        "Every artifact lands on Backblaze B2 — fourteen files, ten types, "
        "from the input CSV to the final video — each one hashed and "
        "verifiable, with full generation provenance you can inspect "
        "yourself.",
    ),
    (
        "durability",
        "vo_07-durability",
        "Refresh the page after a full backend redeploy — the recap still "
        "plays. B2 is the source of truth.",
    ),
    (
        "production",
        "vo_08-production",
        "Ninety-nine percent test coverage, a hard CI gate, structured "
        "logging, and eleven architecture decision records — this isn't a "
        "prototype.",
    ),
    (
        "close",
        "vo_09-close",
        "One connection. Five scenes. Your financial story — Banker's "
        "Wrapped, built on Genblaze and Backblaze B2.",
    ),
]


def probe_duration(path: Path, ffmpeg_bin: str) -> float:
    """Measured (not estimated) clip length via ffprobe. Returns 0.0 on failure."""
    ffprobe_bin = str(Path(ffmpeg_bin).parent / Path(ffmpeg_bin).name.replace("ffmpeg", "ffprobe"))
    try:
        result = subprocess.run(
            [
                ffprobe_bin, "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                str(path),
            ],
            capture_output=True,
            text=True,
        )
        return float(result.stdout.strip())
    except (OSError, ValueError):
        return 0.0


async def main() -> None:
    parser = argparse.ArgumentParser(description="Generate demo-video VO clips")
    parser.add_argument("--voice", default="nova", help="OpenAI TTS voice (default: nova — distinct from the recap's own alloy)")
    parser.add_argument("--model", default="tts-1")
    parser.add_argument("--beat", default=None, help="Regenerate a single beat slug only, e.g. 'hook'")
    args = parser.parse_args()

    settings = get_settings()
    if not settings.openai_api_key:
        print("ERROR: OPENAI_API_KEY not set (check .env).")
        sys.exit(1)

    client = GenblazeClient(
        gmi_api_key=settings.gmi_api_key,
        b2_bucket=settings.b2_bucket_name,
        b2_endpoint=settings.b2_endpoint_url,
        b2_key_id=settings.b2_key_id,
        b2_app_key=settings.b2_application_key,
        openai_api_key=settings.openai_api_key,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    beats = [b for b in BEATS if args.beat is None or b[0] == args.beat]
    if not beats:
        print(f"ERROR: no beat matches --beat {args.beat!r}")
        sys.exit(1)

    print(f"{'Beat':<12} {'File':<20} {'Words':>6} {'Measured':>10}")
    total_seconds = 0.0
    full_text_parts: list[str] = []
    for slug, stem, text in beats:
        result = await client.generate_narration_audio(
            narration_text=text, model=args.model, voice=args.voice,
        )
        out_path = OUTPUT_DIR / f"{stem}.mp3"
        out_path.write_bytes(result.audio_bytes)
        duration = probe_duration(out_path, settings.ffmpeg_bin)
        total_seconds += duration
        full_text_parts.append(text)
        print(f"{slug:<12} {stem + '.mp3':<20} {len(text.split()):>6} {duration:>9.1f}s")

    if args.beat is None:
        full = await client.generate_narration_audio(
            narration_text=" ".join(full_text_parts), model=args.model, voice=args.voice,
        )
        (OUTPUT_DIR / "vo_full-reference.mp3").write_bytes(full.audio_bytes)

    print(f"\nNarration spine: {total_seconds:.1f}s across {len(beats)} clip(s).")
    print("Update the 'Final beat timeline' + 'Narration Script' tables in "
          "submission/DEMO_SCRIPT.md with these measured durations.")


if __name__ == "__main__":
    asyncio.run(main())
