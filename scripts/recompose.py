"""
Recompose: download existing B2 assets → render two local MP4s for comparison.

  concat_<id8>.mp4  — current approach: concat demuxer + global fade-in/out
  xfade_<id8>.mp4   — experimental:     per-scene xfade crossfades

Both use the same dynamic scene-duration logic (probes audio with ffprobe,
stretches scenes to cover the full narration). No API calls; no re-uploads.

Usage:
    uv run python scripts/recompose.py <session_id> <user_id> [--ffmpeg PATH]

session_id and user_id are visible in any B2 key path, e.g.:
    2124435c-.../b9b6704e-.../pipeline/narration.mp3
    └─ user_id ┘  └─ session_id ┘

Env vars: B2_KEY_ID  B2_APPLICATION_KEY  B2_ENDPOINT_URL  B2_BUCKET_NAME
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Force UTF-8 console output so arrows / box-drawing chars don't crash on Windows cp1252
with contextlib.suppress(Exception):
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

from backend.config import get_settings
from backend.media.ffmpeg_composer import FFmpegComposer
from backend.storage.b2_client import B2Client

# ── constants ─────────────────────────────────────────────────────────────────

_SCALE   = "scale=1792:1024:force_original_aspect_ratio=decrease,pad=1792:1024:(ow-iw)/2:(oh-ih)/2"
_XDUR    = 0.5   # xfade crossfade duration (seconds)
_FADE    = 0.5   # global fade-in / fade-out duration (seconds)
_DEFAULT_SCENE_DUR = 8   # fallback if ffprobe fails


# ── helpers ───────────────────────────────────────────────────────────────────

def run(cmd: list[str], label: str) -> None:
    """Run an ffmpeg command; print stderr and exit on failure."""
    print(f"  $ {' '.join(cmd[:6])} …")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"\n[{label}] FFmpeg stderr:\n{result.stderr[-3000:]}")
        sys.exit(f"\n✗  {label} failed (exit {result.returncode})")


def probe_duration(ffprobe: str, path: Path) -> float:
    r = subprocess.run(
        [ffprobe, "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    )
    try:
        return float(r.stdout.strip())
    except ValueError:
        return -1.0


def scene_dur_for(audio_dur: float, n: int, default: int) -> int:
    """Minimum per-scene seconds so video >= audio. Falls back to default."""
    if audio_dur <= 0:
        return default
    needed = audio_dur / n
    return int(math.ceil(needed)) if needed > default else default


# ── approach 1: concat demuxer ────────────────────────────────────────────────

async def render_concat(
    composer: FFmpegComposer,
    scene_paths: list[Path],
    audio_path: Path,
    output_path: Path,
) -> None:
    """Use the existing FFmpegComposer (concat demuxer + global fades)."""
    await composer.compose(
        scene_image_paths=scene_paths,
        output_path=output_path,
        audio_path=audio_path,
    )


# ── approach 2: xfade crossfades ─────────────────────────────────────────────

def build_xfade_cmd(
    ffmpeg: str,
    scene_paths: list[Path],
    audio_path: Path,
    output_path: Path,
    scene_dur: int,
) -> list[str]:
    """
    Filter-complex that xfades every consecutive scene pair, then wraps the
    whole video in a global fade-in and fade-out.

    Each image input is looped for (scene_dur + XDUR) seconds — just enough
    headroom for FFmpeg to consume frames during the overlapping transition.

    xfade offset for transition k (0-indexed):  (k+1) * (scene_dur - XDUR)
    Total video duration (before -shortest):    n*scene_dur - (n-1)*XDUR
    """
    n          = len(scene_paths)
    total_dur  = n * scene_dur - (n - 1) * _XDUR
    fade_out_t = total_dur - _FADE

    cmd = [ffmpeg, "-hide_banner", "-y", "-filter_complex_threads", "2"]

    # One looped image input per scene (-framerate 25 → defined input rate for xfade)
    for p in scene_paths:
        cmd += ["-loop", "1", "-framerate", "25", "-t", str(scene_dur + _XDUR), "-i", str(p)]
    cmd += ["-i", str(audio_path)]

    audio_idx = n
    parts: list[str] = []

    # Scale + format every scene stream (fps=25 → CFR, required by xfade)
    for i in range(n):
        parts.append(f"[{i}:v]{_SCALE},format=yuv420p,setpts=PTS-STARTPTS,fps=25[v{i}]")

    if n == 1:
        parts.append(
            f"[v0]fade=t=in:st=0:d={_FADE},"
            f"fade=t=out:st={fade_out_t:.3f}:d={_FADE}[out]"
        )
    else:
        prev = "v0"
        for k in range(n - 1):
            offset   = (k + 1) * (scene_dur - _XDUR)
            out_lbl  = f"xf{k}" if k < n - 2 else "xfall"
            parts.append(
                f"[{prev}][v{k+1}]"
                f"xfade=transition=fade:duration={_XDUR}:offset={offset:.3f}"
                f"[{out_lbl}]"
            )
            prev = out_lbl

        parts.append(
            f"[{prev}]fade=t=in:st=0:d={_FADE},"
            f"fade=t=out:st={fade_out_t:.3f}:d={_FADE}[out]"
        )

    cmd += [
        "-filter_complex", "; ".join(parts),
        "-map", "[out]",
        "-map", f"{audio_idx}:a",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-threads", "4",
        "-preset", "fast", "-crf", "23", "-movflags", "+faststart",
        "-c:a", "aac", "-b:a", "192k", "-shortest",
        str(output_path),
    ]
    return cmd


# ── main ──────────────────────────────────────────────────────────────────────

async def main(session_id: str, user_id: str, ffmpeg_override: str | None) -> None:
    settings = get_settings()

    ffmpeg  = ffmpeg_override or settings.ffmpeg_bin
    # Replace only the filename, not directory segments (e.g. "ffmpeg-8.1.1-full_build")
    _fp = Path(ffmpeg)
    ffprobe = str(_fp.parent / _fp.name.replace("ffmpeg", "ffprobe"))

    if not shutil.which(ffmpeg):
        sys.exit(f"ffmpeg not found: '{ffmpeg}'. Use --ffmpeg <path>.")
    if not shutil.which(ffprobe):
        sys.exit(f"ffprobe not found: '{ffprobe}'. It must live alongside ffmpeg.")

    b2 = B2Client(
        endpoint_url=settings.b2_endpoint_url,
        key_id=settings.b2_key_id,
        application_key=settings.b2_application_key,
        bucket_name=settings.b2_bucket_name,
    )

    id8 = session_id[:8]

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        # ── download assets ───────────────────────────────────────────────────
        print(f"\nDownloading B2 assets for session {id8}…")

        def download(key: str, dest: Path) -> None:
            try:
                dest.write_bytes(b2.download_bytes(key))
            except Exception as exc:
                sys.exit(
                    f"\n✗  Key not found in B2: {key}\n"
                    f"   Check that the session completed successfully and the "
                    f"user_id/session_id are correct.\n"
                    f"   ({exc})"
                )

        narration_key  = B2Client.narration_key(user_id, session_id)
        narration_path = tmp / "narration.mp3"
        download(narration_key, narration_path)
        audio_dur = probe_duration(ffprobe, narration_path)
        print(f"  narration.mp3  {narration_path.stat().st_size:>10,} B   {audio_dur:.2f}s")

        scene_paths: list[Path] = []
        for i in range(5):
            key  = B2Client.scene_key(user_id, session_id, i)
            path = tmp / f"scene_{i:02d}.jpg"
            download(key, path)
            print(f"  scene_{i:02d}.jpg  {path.stat().st_size:>10,} B")
            scene_paths.append(path)

        # ── compute scene duration ────────────────────────────────────────────
        n         = len(scene_paths)
        scene_dur = scene_dur_for(audio_dur, n, _DEFAULT_SCENE_DUR)
        print(f"\nAudio: {audio_dur:.2f}s  →  scene_dur: {scene_dur}s/scene  "
              f"(video before -shortest: {n * scene_dur}s)")

        # ── approach 1: concat ────────────────────────────────────────────────
        concat_out = tmp / f"concat_{id8}.mp4"
        print("\n── CONCAT (concat demuxer + global fades) ──────────────────")
        composer = FFmpegComposer(
            scene_duration_seconds=_DEFAULT_SCENE_DUR,
            ffmpeg_bin=ffmpeg,
        )
        await render_concat(composer, scene_paths, narration_path, concat_out)
        concat_dur  = probe_duration(ffprobe, concat_out)
        concat_size = concat_out.stat().st_size

        # ── approach 2: xfade ─────────────────────────────────────────────────
        xfade_out = tmp / f"xfade_{id8}.mp4"
        print("\n── XFADE (per-scene crossfade transitions) ─────────────────")
        cmd = build_xfade_cmd(ffmpeg, scene_paths, narration_path, xfade_out, scene_dur)
        run(cmd, "xfade")
        xfade_dur  = probe_duration(ffprobe, xfade_out)
        xfade_size = xfade_out.stat().st_size

        # ── copy to cwd ───────────────────────────────────────────────────────
        cwd = Path.cwd()
        for src, dst_name in [(concat_out, f"concat_{id8}.mp4"),
                               (xfade_out,  f"xfade_{id8}.mp4")]:
            dst = cwd / dst_name
            shutil.copy2(src, dst)

    # ── summary ───────────────────────────────────────────────────────────────
    print(f"""
┌─────────────────────────────────────────────────────────────┐
│  Results for session {id8}
├──────────────┬──────────────┬───────────────────────────────┤
│  approach    │  duration    │  size                         │
├──────────────┼──────────────┼───────────────────────────────┤
│  concat      │  {concat_dur:>7.2f}s    │  {concat_size/1e6:>6.2f} MB                      │
│  xfade       │  {xfade_dur:>7.2f}s    │  {xfade_size/1e6:>6.2f} MB                      │
│  audio ref   │  {audio_dur:>7.2f}s    │  (narration.mp3)              │
└──────────────┴──────────────┴───────────────────────────────┘
  concat_{id8}.mp4
  xfade_{id8}.mp4
""")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Recompose recap from B2 assets — no API calls",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Identify the IDs from the B2 console path, which is always user_id/session_id:

  e.g.  20e39daf-…/48a7e535-…/pipeline/narration.mp3
              └─ user_id ─┘  └─ session_id ─┘

Pass as:  --prefix 20e39daf-…/48a7e535-…
  or as:  <session_id> <user_id>   (positional, note the reversed order)
""",
    )
    parser.add_argument("session_id", nargs="?", help="Session UUID (second segment of B2 path)")
    parser.add_argument("user_id",    nargs="?", help="User UUID (first segment of B2 path)")
    parser.add_argument("--prefix", metavar="USER_ID/SESSION_ID",
                        help="Paste the B2 path prefix directly, e.g. 20e39daf-…/48a7e535-…")
    parser.add_argument("--ffmpeg", metavar="PATH", help="Path to ffmpeg binary")
    args = parser.parse_args()

    if args.prefix:
        parts = args.prefix.strip("/").split("/")
        if len(parts) != 2:
            parser.error("--prefix must be exactly USER_ID/SESSION_ID")
        user_id, session_id = parts[0], parts[1]
    elif args.session_id and args.user_id:
        session_id, user_id = args.session_id, args.user_id
    else:
        parser.error("Provide either --prefix USER_ID/SESSION_ID or both positional args")

    asyncio.run(main(session_id, user_id, args.ffmpeg))
