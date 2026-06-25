"""Unit tests for FFmpegComposer — mocks subprocess."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.media.ffmpeg_composer import FFmpegComposer


@pytest.fixture
def composer() -> FFmpegComposer:
    return FFmpegComposer(scene_duration_seconds=5)


@pytest.fixture
def fake_scene_images(tmp_path) -> list[Path]:
    images = []
    for i in range(4):
        img = tmp_path / f"scene_{i:02d}.png"
        img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
        images.append(img)
    return images


@pytest.fixture
def fake_audio(tmp_path) -> Path:
    audio = tmp_path / "narration.mp3"
    audio.write_bytes(b"\xff\xe0" + b"\x00" * 1024)
    return audio


def _make_thread_mock(returncode: int = 0, stderr: str = "") -> AsyncMock:
    """Return an AsyncMock for asyncio.to_thread that yields a subprocess result."""
    proc = MagicMock(returncode=returncode, stderr=stderr)
    m = AsyncMock(return_value=proc)
    return m


class TestFFmpegComposer:
    async def test_compose_calls_subprocess(self, composer, fake_scene_images, fake_audio, tmp_path):
        output = tmp_path / "recap.mp4"
        with patch("backend.media.ffmpeg_composer.asyncio.to_thread", _make_thread_mock()):
            result = await composer.compose(
                scene_image_paths=fake_scene_images,
                audio_path=fake_audio,
                output_path=output,
            )
        assert result == output

    async def test_compose_includes_ffmpeg_in_command(self, composer, fake_scene_images, fake_audio, tmp_path):
        output = tmp_path / "recap.mp4"
        captured: list = []

        async def capture_thread(fn, cmd, **kwargs):  # type: ignore[no-untyped-def]
            captured.append(cmd)
            return MagicMock(returncode=0, stderr="")

        with patch("backend.media.ffmpeg_composer.asyncio.to_thread", capture_thread):
            await composer.compose(
                scene_image_paths=fake_scene_images,
                audio_path=fake_audio,
                output_path=output,
            )
        assert captured, "asyncio.to_thread was never called"
        assert "ffmpeg" in captured[0][0]

    async def test_compose_raises_on_ffmpeg_failure(self, composer, fake_scene_images, fake_audio, tmp_path):
        output = tmp_path / "recap.mp4"
        with patch(
            "backend.media.ffmpeg_composer.asyncio.to_thread",
            _make_thread_mock(returncode=1, stderr="Error: Invalid input file"),
        ):
            with pytest.raises(RuntimeError, match="FFmpeg failed"):
                await composer.compose(
                    scene_image_paths=fake_scene_images,
                    audio_path=fake_audio,
                    output_path=output,
                )

    async def test_concat_file_written(self, composer, fake_scene_images, fake_audio, tmp_path):
        output = tmp_path / "recap.mp4"
        captured: list = []

        async def capture_thread(fn, cmd, **kwargs):  # type: ignore[no-untyped-def]
            captured.append(cmd)
            return MagicMock(returncode=0, stderr="")

        with patch("backend.media.ffmpeg_composer.asyncio.to_thread", capture_thread):
            await composer.compose(
                scene_image_paths=fake_scene_images,
                audio_path=fake_audio,
                output_path=output,
            )
        assert captured
        cmd = captured[0]
        assert "-f" in cmd
        assert "concat" in cmd

    async def test_scene_duration_applied(self, fake_scene_images, fake_audio, tmp_path):
        composer = FFmpegComposer(scene_duration_seconds=10)
        output = tmp_path / "recap.mp4"
        with patch("backend.media.ffmpeg_composer.asyncio.to_thread", _make_thread_mock()):
            await composer.compose(
                scene_image_paths=fake_scene_images,
                audio_path=fake_audio,
                output_path=output,
            )
        assert composer.scene_duration == 10
