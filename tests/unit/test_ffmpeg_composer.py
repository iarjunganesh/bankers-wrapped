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
        img = tmp_path / f"scene_{i:02d}.jpg"
        img.write_bytes(b"\xff\xd8\xff" + b"\x00" * 64)
        images.append(img)
    return images


@pytest.fixture
def fake_audio(tmp_path) -> Path:
    audio = tmp_path / "narration.mp3"
    audio.write_bytes(b"\xff\xe0" + b"\x00" * 1024)
    return audio


@pytest.fixture(autouse=True)
def mock_probe(composer):
    """Prevent real ffprobe calls in every test; default to 0.0 (no adjustment)."""
    with patch.object(FFmpegComposer, "_probe_audio_duration", return_value=0.0):
        yield


def _make_thread_mock(returncode: int = 0, stderr: str = "") -> AsyncMock:
    proc = MagicMock(returncode=returncode, stderr=stderr)
    return AsyncMock(return_value=proc)


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
        assert captured
        assert "ffmpeg" in captured[0][0]

    async def test_compose_raises_on_ffmpeg_failure(self, composer, fake_scene_images, fake_audio, tmp_path):
        output = tmp_path / "recap.mp4"
        with patch(
            "backend.media.ffmpeg_composer.asyncio.to_thread",
            _make_thread_mock(returncode=1, stderr="Error: bad input"),
        ), pytest.raises(RuntimeError, match="FFmpeg failed"):
            await composer.compose(
                scene_image_paths=fake_scene_images,
                audio_path=fake_audio,
                output_path=output,
            )

    async def test_uses_xfade_filter_complex(self, composer, fake_scene_images, fake_audio, tmp_path):
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
        cmd_str = " ".join(captured[0])
        assert "-filter_complex" in cmd_str
        assert "xfade" in cmd_str

    async def test_fade_in_out_applied(self, composer, fake_scene_images, fake_audio, tmp_path):
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
        cmd_str = " ".join(captured[0])
        assert "fade=t=in" in cmd_str
        assert "fade=t=out" in cmd_str

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

    async def test_scene_duration_stretched_for_long_audio(self, fake_scene_images, fake_audio, tmp_path):
        """Scene duration stretches so the video covers audio longer than default.

        n=4, default=5s, audio=61s → dur=ceil(61/4)=16s/scene
        total_dur = 4*16 - 3*0.5 = 62.5s  →  fade_out at 62.5-0.5 = 62.000
        """
        composer = FFmpegComposer(scene_duration_seconds=5)
        output   = tmp_path / "recap.mp4"
        captured: list = []

        async def capture_thread(fn, cmd, **kwargs):  # type: ignore[no-untyped-def]
            captured.append(cmd)
            return MagicMock(returncode=0, stderr="")

        with patch.object(FFmpegComposer, "_probe_audio_duration", return_value=61.0), \
             patch("backend.media.ffmpeg_composer.asyncio.to_thread", capture_thread):
            await composer.compose(
                scene_image_paths=fake_scene_images,
                audio_path=fake_audio,
                output_path=output,
            )

        cmd_str = " ".join(captured[0])
        assert "fade=t=out:st=62.000" in cmd_str

    async def test_output_is_browser_compatible(self, composer, fake_scene_images, fake_audio, tmp_path):
        """Output MUST be yuv420p + faststart, else browsers report 'file is corrupt'.

        seedream JPEGs are full-range 4:4:4; without an explicit -pix_fmt yuv420p
        libx264 emits High 4:4:4 (yuvj444p) which plays in VLC but not in browsers.
        """
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
        cmd = captured[0]
        assert "-pix_fmt" in cmd
        assert cmd[cmd.index("-pix_fmt") + 1] == "yuv420p"
        assert "+faststart" in cmd

    async def test_single_scene_no_xfade(self, composer, tmp_path):
        """A single scene skips xfade and goes straight to global fades."""
        single_img = tmp_path / "scene_00.jpg"
        single_img.write_bytes(b"\xff\xd8\xff" + b"\x00" * 64)
        output   = tmp_path / "recap.mp4"
        captured: list = []

        async def capture_thread(fn, cmd, **kwargs):  # type: ignore[no-untyped-def]
            captured.append(cmd)
            return MagicMock(returncode=0, stderr="")

        with patch("backend.media.ffmpeg_composer.asyncio.to_thread", capture_thread):
            await composer.compose(
                scene_image_paths=[single_img],
                output_path=output,
            )
        cmd = captured[0]
        assert "-filter_complex" in cmd
        # Extract the filter_complex value (the token after the flag)
        fc = cmd[cmd.index("-filter_complex") + 1]
        assert "xfade" not in fc   # no transitions with a single scene
        assert "fade=t=in" in fc
