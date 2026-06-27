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

FFMPEG_BIN = "ffmpeg"
_FADE_DUR = 0.5   # seconds for crossfade between scenes and global fade in/out
_FPS = 25
_SCALE = "scale=1792:1024:force_original_aspect_ratio=decrease,pad=1792:1024:(ow-iw)/2:(oh-ih)/2"


class FFmpegComposer:
    """Composes scene images + audio track into a final MP4 with visual transitions."""

    def __init__(self, scene_duration_seconds: int = 8) -> None:
        self.scene_duration = scene_duration_seconds

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

        # Build FFmpeg inputs: loop each image for scene_duration seconds
        inputs: list[str] = []
        for img in scene_image_paths:
            inputs += ["-loop", "1", "-t", str(dur), "-i", str(img)]

        if audio_path is not None:
            inputs += ["-i", str(audio_path)]

        audio_idx = n  # audio stream index (if present)

        # ── filter_complex ────────────────────────────────────────────────────
        filter_parts: list[str] = []

        # Step 1: scale + letterbox each input into a labelled video stream
        for i in range(n):
            filter_parts.append(f"[{i}:v]{_SCALE},format=yuv420p[v{i}]")

        # Step 2: chain xfade between consecutive streams
        if n == 1:
            # No transitions needed — just rename
            filter_parts.append("[v0]copy[xout]")
        else:
            prev = "[v0]"
            for i in range(1, n):
                # offset = time into the output where the transition starts
                offset = i * (dur - fade)
                out_label = f"[xf{i}]" if i < n - 1 else "[xout]"
                filter_parts.append(
                    f"{prev}[v{i}]xfade=transition=fade:duration={fade}:offset={offset}{out_label}"
                )
                prev = f"[xf{i}]"

        # Step 3: global fade-in (first 0.5 s) and fade-out (last 0.5 s)
        total_video_dur = n * dur - (n - 1) * fade
        fade_out_start = total_video_dur - fade
        filter_parts.append(
            f"[xout]fade=t=in:st=0:d={fade},fade=t=out:st={fade_out_start:.3f}:d={fade}[vfinal]"
        )

        filter_complex = ";".join(filter_parts)

        # ── Assemble command ──────────────────────────────────────────────────
        cmd = [
            FFMPEG_BIN,
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
