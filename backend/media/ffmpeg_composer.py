"""
FFmpeg Compositor.

Combines:
  - Scene images (one per scene, displayed for N seconds each)
  - Narration audio (optional MP3 spanning all scenes)

Visual effects applied:
  - Scale + letterbox to 1792x1024 (16:9) via concat demuxer
  - Global 0.5 s fade-in from black at the start
  - Global 0.5 s fade-out to black at the end

Output: recap.mp4 (H.264, 1792x1024, 25 fps; AAC audio when provided)
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
_FADE_DUR = 0.5
_FPS = 25
_SCALE = "scale=1792:1024:force_original_aspect_ratio=decrease,pad=1792:1024:(ow-iw)/2:(oh-ih)/2"


class FFmpegComposer:
    """Composes scene images + audio track into a final MP4."""

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
        Compose a final recap.mp4 using the concat demuxer.

        Each scene image is displayed for `scene_duration` seconds with a
        global fade-in at the start and fade-out at the end.

        Args:
            scene_image_paths: List of JPEG/PNG image files, one per scene.
            output_path: Destination for the output MP4.
            audio_path: Optional MP3 narration audio.
            title: Reserved for future overlay use.
            personality: Reserved for future overlay use.

        Returns:
            Path to the composed MP4 file.
        """
        n = len(scene_image_paths)
        dur = self.scene_duration
        total_dur = n * dur
        fade_out_start = total_dur - _FADE_DUR

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)

            # Build concat.txt: each image for scene_duration seconds.
            # The concat demuxer requires the last file to be listed twice
            # (FFmpeg quirk) to ensure the final frame duration is honoured.
            lines: list[str] = []
            for img_path in scene_image_paths:
                lines.append(f"file '{img_path.resolve().as_posix()}'")
                lines.append(f"duration {dur}")
            if scene_image_paths:
                lines.append(f"file '{scene_image_paths[-1].resolve().as_posix()}'")

            concat_file = tmp / "concat.txt"
            concat_file.write_text("\n".join(lines))

            vf = (
                f"{_SCALE},"
                f"format=yuv420p,"
                f"fade=t=in:st=0:d={_FADE_DUR},"
                f"fade=t=out:st={fade_out_start}:d={_FADE_DUR}"
            )

            cmd = [
                self.ffmpeg_bin, "-hide_banner", "-y",
                "-f", "concat", "-safe", "0", "-i", str(concat_file),
            ]
            if audio_path is not None:
                cmd += ["-i", str(audio_path)]

            cmd += [
                "-vf", vf,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-r", str(_FPS),
            ]
            if audio_path is not None:
                cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]

            cmd.append(str(output_path))

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
