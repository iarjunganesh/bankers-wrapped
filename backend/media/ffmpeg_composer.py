"""
FFmpeg Compositor.

Combines:
  - Scene images (one per scene, displayed for N seconds each)
  - Narration audio (optional MP3 spanning all scenes)

Output: recap.mp4 (H.264, 1792x1024, 25fps; AAC audio track when provided)
"""

from __future__ import annotations

import asyncio
import subprocess
import tempfile
from pathlib import Path

import structlog

log = structlog.get_logger()

FFMPEG_BIN = "ffmpeg"


class FFmpegComposer:
    """Composes scene images + audio track into a final MP4."""

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
        Compose a final recap.mp4.

        Args:
            scene_image_paths: List of PNG/JPG image files, one per scene.
            output_path: Destination for the output MP4.
            audio_path: Optional MP3 narration audio. When omitted, the video
                runs for (scenes × scene_duration) seconds with no audio track.
            title: Video title (kept for future overlay use).
            personality: Financial Personality (kept for future overlay use).

        Returns:
            Path to the composed MP4 file.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)

            # 1. Build the image sequence for ffmpeg
            concat_file = tmp / "concat.txt"
            lines = []

            for img_path in scene_image_paths:
                lines.append(f"file '{img_path.resolve().as_posix()}'")
                lines.append(f"duration {self.scene_duration}")

            # Last image needs to be repeated (ffmpeg concat demuxer quirk)
            if scene_image_paths:
                lines.append(f"file '{scene_image_paths[-1].resolve().as_posix()}'")

            concat_file.write_text("\n".join(lines))

            # 2. Build ffmpeg command
            cmd = [
                FFMPEG_BIN,
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
            ]

            if audio_path is not None:
                cmd += ["-i", str(audio_path)]

            cmd += [
                "-vf", "scale=1792:1024:force_original_aspect_ratio=decrease,"
                       "pad=1792:1024:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
            ]

            if audio_path is not None:
                cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]

            cmd.append(str(output_path))

            log.info("ffmpeg.compose.start", scenes=len(scene_image_paths), audio=audio_path is not None)

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
