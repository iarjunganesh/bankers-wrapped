"""
FFmpeg Compositor — memory-bounded segment + concat strategy.

Why not a single xfade filter_complex?
  A monolithic xfade graph with N looped image inputs buffers every input's
  frames until its (staggered) transition offset — several GB at 1792×1024.
  On a memory-limited container (e.g. Railway) the OOM-killer sends SIGKILL
  (returncode -9) and zero frames are written. See ADR / CHANGELOG.

This compositor instead:
  1. Renders each scene to its OWN short MP4 segment — one image in RAM at a
     time, so peak memory is a single small encode (a few hundred MB), not GBs.
  2. Concatenates the segments with the concat demuxer using `-c:v copy`
     (stream copy — no decode, near-zero memory) and muxes the narration.

Transitions are dip-to-black: each segment fades in from / out to black, so
consecutive scenes are separated by a short black dip (memory-free, cinematic).
True crossfades require overlapping two scenes' frames — exactly the buffering
this design avoids — so they are intentionally not used.

Per-scene duration = narration_length / N, so the video covers the full
narration exactly. Output: H.264 libx264, yuv420p, +faststart, AAC 192 kbps.
"""

from __future__ import annotations

import asyncio
import shutil
import subprocess
import tempfile
from pathlib import Path

import structlog

log = structlog.get_logger()

FFMPEG_BIN = shutil.which("ffmpeg") or "ffmpeg"
_SEG_FADE = 0.3   # dip-to-black fade in / out per scene segment (seconds)
_SCALE = (
    "scale=1792:1024:force_original_aspect_ratio=decrease,"
    "pad=1792:1024:(ow-iw)/2:(oh-ih)/2"
)


class FFmpegComposer:
    """Composes scene images + narration into an MP4 via per-scene segments."""

    def __init__(self, scene_duration_seconds: int = 8, ffmpeg_bin: str = FFMPEG_BIN) -> None:
        self.scene_duration = scene_duration_seconds
        self.ffmpeg_bin     = ffmpeg_bin
        # Replace only the filename, not directory segments that may also contain "ffmpeg"
        _p = Path(ffmpeg_bin)
        self._ffprobe_bin   = str(_p.parent / _p.name.replace("ffmpeg", "ffprobe"))

    def _probe_audio_duration(self, audio_path: Path) -> float:
        """Return audio duration in seconds via ffprobe. Returns 0.0 on failure."""
        try:
            result = subprocess.run(
                [
                    self._ffprobe_bin, "-v", "quiet",
                    "-show_entries", "format=duration",
                    "-of", "csv=p=0",
                    str(audio_path),
                ],
                capture_output=True,
                text=True,
            )
            return float(result.stdout.strip())
        except (OSError, ValueError):
            log.warning("ffprobe.unavailable", ffprobe=self._ffprobe_bin)
            return 0.0

    async def _run(self, cmd: list[str], label: str) -> None:
        """Run an ffmpeg command in a thread; raise with returncode on failure."""
        result = await asyncio.to_thread(
            subprocess.run, cmd, capture_output=True, text=True, timeout=300,
        )
        if result.returncode != 0:
            # returncode -9 = SIGKILL (usually OOM); -11 = SIGSEGV (crash).
            log.error(
                f"ffmpeg.{label}.failed",
                returncode=result.returncode,
                stderr=result.stderr[-2000:],
            )
            raise RuntimeError(
                f"FFmpeg {label} failed (rc={result.returncode}): {result.stderr[-500:]}"
            )

    async def compose(
        self,
        scene_image_paths: list[Path],
        output_path: Path,
        audio_path: Path | None = None,
        title: str = "Your Financial Recap",
        personality: str = "Financial Builder",
    ) -> Path:
        """
        Render each scene to a segment, then concat-copy them into the final MP4.

        Peak memory ≈ one segment encode (sequential, never parallel), so this
        runs even on tight containers where a monolithic xfade graph OOM-kills.
        """
        n = len(scene_image_paths)

        # Per-scene duration: split the narration evenly so total == audio length.
        audio_dur = self._probe_audio_duration(audio_path) if audio_path is not None else 0.0
        dur = (audio_dur / n) if audio_dur > 0 else float(self.scene_duration)
        fade = min(_SEG_FADE, dur / 3)  # guard against fades overlapping on short scenes

        log.info(
            "ffmpeg.compose.start",
            scenes=n,
            audio=audio_path is not None,
            per_scene_s=f"{dur:.2f}",
            total_s=f"{dur * n:.1f}",
        )

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)

            # ── 1. Render each scene to its own segment (one image in RAM) ──────
            segments: list[Path] = []
            for i, img in enumerate(scene_image_paths):
                seg = tmp / f"seg_{i:02d}.mp4"
                vf = (
                    f"{_SCALE},format=yuv420p,fps=25,"
                    f"fade=t=in:st=0:d={fade:.3f},"
                    f"fade=t=out:st={dur - fade:.3f}:d={fade:.3f}"
                )
                cmd = [
                    self.ffmpeg_bin, "-hide_banner", "-y",
                    "-loop", "1", "-framerate", "25", "-t", f"{dur:.3f}",
                    "-i", str(img),
                    "-vf", vf,
                    # -pix_fmt yuv420p is REQUIRED for browser playback (seedream
                    # JPEGs are full-range 4:4:4 → libx264 would emit yuvj444p,
                    # which plays in VLC but is "corrupt" in browsers).
                    # -threads 2 caps libx264 (ffmpeg sees the HOST core count, not
                    # the container's, and would otherwise spawn memory-heavy threads).
                    "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-threads", "2", "-preset", "fast", "-crf", "23",
                    "-an", str(seg),
                ]
                log.info(
                    "ffmpeg.segment.render",
                    idx=i,
                    exists=img.exists(),
                    size=img.stat().st_size if img.exists() else None,
                )
                await self._run(cmd, "segment")
                segments.append(seg)

            # ── 2. Concat (stream-copy) + mux narration — near-zero memory ──────
            list_file = tmp / "segments.txt"
            list_file.write_text(
                "".join(f"file '{seg.as_posix()}'\n" for seg in segments),
                encoding="utf-8",
            )
            cmd = [
                self.ffmpeg_bin, "-hide_banner", "-y",
                "-f", "concat", "-safe", "0", "-i", str(list_file),
            ]
            if audio_path is not None:
                cmd += ["-i", str(audio_path)]
            cmd += ["-c:v", "copy"]
            if audio_path is not None:
                cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
            cmd += ["-movflags", "+faststart", str(output_path)]

            await self._run(cmd, "concat")

        log.info("ffmpeg.compose.complete", output=str(output_path))
        return output_path
