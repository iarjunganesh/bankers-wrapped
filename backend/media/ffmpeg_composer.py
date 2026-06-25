"""
FFmpeg Compositor.

Combines:
  - Intro title slide (text-rendered PNG)
  - Scene images (one per scene, displayed for N seconds each)
  - Narration audio (full MP3 spanning all scenes)

Output: recap.mp4 (H.264 + AAC, 1792x1024, 25fps)
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
        audio_path: Path,
        output_path: Path,
        title: str = "Your Financial Recap",
        personality: str = "Financial Builder",
    ) -> Path:
        """
        Compose a final recap.mp4.

        Args:
            scene_image_paths: List of PNG/JPG image files, one per scene.
            audio_path: MP3 narration audio file.
            output_path: Destination for the output MP4.
            title: Video title shown on intro slide.
            personality: Financial Personality shown on intro slide.

        Returns:
            Path to the composed MP4 file.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)

            # 1. Build the image sequence for ffmpeg
            concat_file = tmp / "concat.txt"
            lines = []

            for img_path in scene_image_paths:
                lines.append(f"file '{img_path.resolve()}'")
                lines.append(f"duration {self.scene_duration}")

            # Last image needs to be repeated (ffmpeg concat demuxer quirk)
            if scene_image_paths:
                lines.append(f"file '{scene_image_paths[-1].resolve()}'")

            concat_file.write_text("\n".join(lines))

            # 2. Run ffmpeg
            cmd = [
                FFMPEG_BIN,
                "-y",
                # Input 1: image slideshow via concat demuxer
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                # Input 2: audio
                "-i", str(audio_path),
                # Video encoding
                "-vf", "scale=1792:1024:force_original_aspect_ratio=decrease,"
                       "pad=1792:1024:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                # Audio encoding
                "-c:a", "aac",
                "-b:a", "192k",
                # Sync: end when audio ends
                "-shortest",
                str(output_path),
            ]

            log.info("ffmpeg.compose.start", scenes=len(scene_image_paths))

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
