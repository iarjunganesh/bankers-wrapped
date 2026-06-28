"""
FFmpeg Compositor.

Combines:
  - Scene images (one per scene, displayed for N seconds each)
  - Narration audio (optional MP3 spanning all scenes)

Visual effects applied:
  - Scale + letterbox to 1792×1024 (16:9)
  - xfade crossfade (0.5 s fade) between every scene pair
  - Global 0.5 s fade-in from black at the start
  - Global 0.5 s fade-out to black at the end

Output: recap.mp4 (H.264, 1792×1024, 25 fps; AAC audio when provided)
"""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path

import structlog

log = structlog.get_logger()

import shutil

# Resolved once at startup; override via FFMPEG_BIN env var / settings if not on PATH
FFMPEG_BIN = shutil.which("ffmpeg") or "ffmpeg"
_FADE_DUR = 0.5   # seconds for crossfade between scenes and global fade in/out
_FPS = 25
_SCALE = "scale=1792:1024:force_original_aspect_ratio=decrease,pad=1792:1024:(ow-iw)/2:(oh-ih)/2"
_ENDING_DUR = 3   # seconds for branded ending card


class FFmpegComposer:
    """Composes scene images + audio track into a final MP4 with visual transitions."""

    def __init__(self, scene_duration_seconds: int = 8, ffmpeg_bin: str = FFMPEG_BIN) -> None:
        self.scene_duration = scene_duration_seconds
        self.ffmpeg_bin = ffmpeg_bin

    async def compose(
        self,
        scene_image_paths: list[Path],
        output_path: Path,
        audio_path: Path | None = None,
        title: str = "Your Financial Recap",
        personality: str = "Financial Builder",
    ) -> Path:
        """
        Compose a final recap.mp4 with xfade crossfade transitions.

        Each scene image is displayed for `scene_duration` seconds, with
        0.5 s xfade transitions between consecutive scenes and a global
        fade-in/fade-out applied to the full video.

        Args:
            scene_image_paths: List of PNG/JPG image files, one per scene.
            output_path: Destination for the output MP4.
            audio_path: Optional MP3 narration audio.
            title: Video title (reserved for future overlay).
            personality: Financial Personality label (reserved for future overlay).

        Returns:
            Path to the composed MP4 file.
        """
        n = len(scene_image_paths)
        dur = self.scene_duration
        fade = _FADE_DUR
        n_total = n + 1  # scenes + ending card

        # Build FFmpeg inputs: loop each image for scene_duration seconds
        inputs: list[str] = []
        for img in scene_image_paths:
            inputs += ["-loop", "1", "-t", str(dur), "-i", str(img)]

        # Ending card: dark background generated via lavfi (input index n)
        inputs += [
            "-f", "lavfi",
            "-i", f"color=c=0x0a0a0f:s=1792x1024:d={_ENDING_DUR}",
        ]

        if audio_path is not None:
            inputs += ["-i", str(audio_path)]

        audio_idx = n_total  # audio stream index (if present)

        # ── filter_complex ────────────────────────────────────────────────────
        filter_parts: list[str] = []

        # Step 1: scale + letterbox each scene image into a labelled stream
        for i in range(n):
            filter_parts.append(f"[{i}:v]{_SCALE},format=yuv420p[v{i}]")

        # Step 2: ending card — scale + drawtext branding (input index n)
        ending_line1 = title.replace("'", "\\'")
        ending_line2 = "Generated with AI  ·  Stored in Backblaze B2"
        filter_parts.append(
            f"[{n}:v]{_SCALE},format=yuv420p,"
            f"drawtext=text='{ending_line1}':fontsize=64:fontcolor=white"
            f":x=(w-text_w)/2:y=h*0.38,"
            f"drawtext=text='{ending_line2}':fontsize=28:fontcolor=0xaaaaaa"
            f":x=(w-text_w)/2:y=h*0.55[v{n}]"
        )

        # Step 3: chain xfade between all streams (scenes + ending card)
        prev = "[v0]"
        for i in range(1, n_total):
            # offset = cumulative time at which this transition starts
            offset = sum(
                (dur if j < n else _ENDING_DUR) - fade
                for j in range(i)
            )
            out_label = f"[xf{i}]" if i < n_total - 1 else "[xout]"
            filter_parts.append(
                f"{prev}[v{i}]xfade=transition=fade:duration={fade}:offset={offset:.3f}{out_label}"
            )
            prev = f"[xf{i}]"

        # Step 4: global fade-in (first 0.5 s) and fade-out (last 0.5 s)
        total_video_dur = n * dur + _ENDING_DUR - n_total * fade + fade
        fade_out_start = total_video_dur - fade
        filter_parts.append(
            f"[xout]fade=t=in:st=0:d={fade},fade=t=out:st={fade_out_start:.3f}:d={fade}[vfinal]"
        )

        filter_complex = ";".join(filter_parts)

        # ── Assemble command ──────────────────────────────────────────────────
        cmd = [
            self.ffmpeg_bin,
            "-y",
        ] + inputs + [
            "-filter_complex", filter_complex,
            "-map", "[vfinal]",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-r", str(_FPS),
        ]

        if audio_path is not None:
            cmd += [
                "-map", f"{audio_idx}:a",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
            ]

        cmd.append(str(output_path))

        log.info(
            "ffmpeg.compose.start",
            scenes=n,
            audio=audio_path is not None,
            total_dur_s=f"{total_video_dur:.1f}",
        )

        result = await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            log.error("ffmpeg.compose.failed", stderr=result.stderr[-500:])
            raise RuntimeError(f"FFmpeg failed: {result.stderr[-300:]}")

        log.info("ffmpeg.compose.complete", output=str(output_path))
        return output_path
