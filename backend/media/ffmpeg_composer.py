"""
FFmpeg Compositor.

Combines:
  - Scene images (one per scene)
  - Narration audio (optional MP3)

Visual effects:
  - Per-scene xfade crossfade (0.5 s) between every consecutive pair
  - Global fade-in from black (0.5 s at start)
  - Global fade-out to black  (0.5 s at end)
  - Scale + letterbox to 1792×1024 (16:9)

Scene duration is computed dynamically from the audio length so the video
always covers the full narration. -shortest then trims to the exact audio end.

Output: H.264 libx264, 1792×1024, AAC 192 kbps audio.
"""

from __future__ import annotations

import asyncio
import math
import shutil
import subprocess
from pathlib import Path

import structlog

log = structlog.get_logger()

FFMPEG_BIN  = shutil.which("ffmpeg")  or "ffmpeg"
_XFADE_DUR  = 0.5   # crossfade duration between consecutive scenes (seconds)
_FADE_DUR   = 0.5   # global fade-in / fade-out duration (seconds)
_SCALE = (
    "scale=1792:1024:force_original_aspect_ratio=decrease,"
    "pad=1792:1024:(ow-iw)/2:(oh-ih)/2"
)


class FFmpegComposer:
    """Composes scene images + audio into a final MP4 using xfade transitions."""

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

    async def compose(
        self,
        scene_image_paths: list[Path],
        output_path: Path,
        audio_path: Path | None = None,
        title: str = "Your Financial Recap",
        personality: str = "Financial Builder",
    ) -> Path:
        """
        Compose a recap MP4 using xfade crossfades between every scene pair.

        Scene duration is stretched automatically so the video length covers
        the full narration. -shortest then trims the video to the audio end.

        xfade offset for transition k (0-indexed): (k+1) * (scene_dur - XFADE_DUR)
        Total video duration before -shortest:      n*scene_dur - (n-1)*XFADE_DUR
        """
        n   = len(scene_image_paths)
        dur = self.scene_duration

        # Stretch scene duration if narration is longer than default video length
        if audio_path is not None:
            audio_dur = self._probe_audio_duration(audio_path)
            if audio_dur > 0:
                min_scene_dur = audio_dur / n
                if min_scene_dur > dur:
                    dur = math.ceil(min_scene_dur)
                    log.info(
                        "ffmpeg.scene_dur_adjusted",
                        audio_dur_s=f"{audio_dur:.1f}",
                        scene_dur_s=dur,
                    )

        total_dur      = n * dur - (n - 1) * _XFADE_DUR
        fade_out_start = total_dur - _FADE_DUR

        # ── Build FFmpeg command ───────────────────────────────────────────────
        cmd = [self.ffmpeg_bin, "-hide_banner", "-y"]

        # One looped image input per scene; extra XFADE_DUR gives the filter
        # enough headroom to consume frames during the overlapping transition.
        for img in scene_image_paths:
            cmd += ["-loop", "1", "-t", str(dur + _XFADE_DUR), "-i", str(img)]
        if audio_path is not None:
            cmd += ["-i", str(audio_path)]

        audio_idx = n  # audio is the (n+1)-th input, 0-indexed

        # ── filter_complex ────────────────────────────────────────────────────
        parts: list[str] = []

        # Scale + format every scene stream
        for i in range(n):
            parts.append(
                f"[{i}:v]{_SCALE},format=yuv420p,setpts=PTS-STARTPTS[v{i}]"
            )

        # Chain xfades then wrap in global fades
        if n == 1:
            parts.append(
                f"[v0]"
                f"fade=t=in:st=0:d={_FADE_DUR},"
                f"fade=t=out:st={fade_out_start:.3f}:d={_FADE_DUR}"
                f"[out]"
            )
        else:
            prev = "v0"
            for k in range(n - 1):
                offset  = (k + 1) * (dur - _XFADE_DUR)
                out_lbl = f"xf{k}" if k < n - 2 else "xfall"
                parts.append(
                    f"[{prev}][v{k+1}]"
                    f"xfade=transition=fade:duration={_XFADE_DUR}:offset={offset:.3f}"
                    f"[{out_lbl}]"
                )
                prev = out_lbl
            parts.append(
                f"[{prev}]"
                f"fade=t=in:st=0:d={_FADE_DUR},"
                f"fade=t=out:st={fade_out_start:.3f}:d={_FADE_DUR}"
                f"[out]"
            )

        cmd += ["-filter_complex", "; ".join(parts)]
        cmd += ["-map", "[out]"]
        if audio_path is not None:
            cmd += ["-map", f"{audio_idx}:a"]

        # -pix_fmt yuv420p is REQUIRED for browser playback. seedream JPEGs are
        # full-range 4:4:4; without this, libx264 emits High 4:4:4 (yuvj444p) which
        # plays in VLC but is undecodable in browsers ("file is corrupt"). The
        # in-filter format=yuv420p does not survive xfade negotiation, so force it here.
        cmd += [
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-preset", "fast", "-crf", "23", "-movflags", "+faststart",
        ]
        if audio_path is not None:
            cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]

        cmd.append(str(output_path))

        # ── Log inputs ────────────────────────────────────────────────────────
        for img in scene_image_paths:
            log.info(
                "ffmpeg.input.scene",
                path=str(img),
                exists=img.exists(),
                size=img.stat().st_size if img.exists() else None,
            )
        if audio_path is not None:
            log.info(
                "ffmpeg.input.audio",
                path=str(audio_path),
                exists=audio_path.exists(),
                size=audio_path.stat().st_size if audio_path.exists() else None,
            )
        log.info(
            "ffmpeg.compose.start",
            scenes=n,
            audio=audio_path is not None,
            total_dur_s=f"{total_dur:.1f}",
        )

        result = await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            log.error("ffmpeg.compose.failed", stderr=result.stderr[-2000:])
            raise RuntimeError(f"FFmpeg failed: {result.stderr[-500:]}")

        log.info("ffmpeg.compose.complete", output=str(output_path))
        return output_path
