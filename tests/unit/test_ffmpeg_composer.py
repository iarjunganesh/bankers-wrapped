"""Unit tests for FFmpegComposer — segment + concat strategy, mocks subprocess."""

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
    """Prevent real ffprobe calls in every test; default to 0.0 (no audio length)."""
    with patch.object(FFmpegComposer, "_probe_audio_duration", return_value=0.0):
        yield


def _capture():
    """Return (captured_cmds, patched_to_thread) where each call appends its cmd."""
    captured: list[list[str]] = []

    async def capture_thread(fn, cmd, **kwargs):  # type: ignore[no-untyped-def]
        captured.append(cmd)
        return MagicMock(returncode=0, stderr="")

    return captured, capture_thread


def _is_segment(cmd: list[str]) -> bool:
    return "-loop" in cmd


def _is_concat(cmd: list[str]) -> bool:
    return "concat" in cmd


class TestFFmpegComposer:
    async def test_compose_returns_output_path(self, composer, fake_scene_images, fake_audio, tmp_path):
        output = tmp_path / "recap.mp4"
        _, capture_thread = _capture()
        with patch("backend.media.ffmpeg_composer.asyncio.to_thread", capture_thread):
            result = await composer.compose(
                scene_image_paths=fake_scene_images,
                audio_path=fake_audio,
                output_path=output,
            )
        assert result == output

    async def test_one_segment_render_per_scene_plus_concat(self, composer, fake_scene_images, fake_audio, tmp_path):
        """N scenes → N segment renders + exactly one concat pass."""
        output = tmp_path / "recap.mp4"
        captured, capture_thread = _capture()
        with patch("backend.media.ffmpeg_composer.asyncio.to_thread", capture_thread):
            await composer.compose(
                scene_image_paths=fake_scene_images,
                audio_path=fake_audio,
                output_path=output,
            )
        segs = [c for c in captured if _is_segment(c)]
        concats = [c for c in captured if _is_concat(c)]
        assert len(segs) == len(fake_scene_images)
        assert len(concats) == 1

    async def test_segments_are_browser_safe_yuv420p(self, composer, fake_scene_images, fake_audio, tmp_path):
        """Every segment must encode yuv420p, else browsers report 'file is corrupt'."""
        output = tmp_path / "recap.mp4"
        captured, capture_thread = _capture()
        with patch("backend.media.ffmpeg_composer.asyncio.to_thread", capture_thread):
            await composer.compose(
                scene_image_paths=fake_scene_images,
                audio_path=fake_audio,
                output_path=output,
            )
        for seg in [c for c in captured if _is_segment(c)]:
            assert "-pix_fmt" in seg
            assert seg[seg.index("-pix_fmt") + 1] == "yuv420p"
            assert "-threads" in seg  # libx264 thread cap (container OOM guard)

    async def test_dip_to_black_fades_on_segments(self, composer, fake_scene_images, fake_audio, tmp_path):
        output = tmp_path / "recap.mp4"
        captured, capture_thread = _capture()
        with patch("backend.media.ffmpeg_composer.asyncio.to_thread", capture_thread):
            await composer.compose(
                scene_image_paths=fake_scene_images,
                audio_path=fake_audio,
                output_path=output,
            )
        seg = next(c for c in captured if _is_segment(c))
        vf = seg[seg.index("-vf") + 1]
        assert "fade=t=in" in vf
        assert "fade=t=out" in vf

    async def test_concat_stream_copies_and_faststarts(self, composer, fake_scene_images, fake_audio, tmp_path):
        """Final pass concat-copies video (no re-encode) and writes faststart MP4."""
        output = tmp_path / "recap.mp4"
        captured, capture_thread = _capture()
        with patch("backend.media.ffmpeg_composer.asyncio.to_thread", capture_thread):
            await composer.compose(
                scene_image_paths=fake_scene_images,
                audio_path=fake_audio,
                output_path=output,
            )
        concat = next(c for c in captured if _is_concat(c))
        assert concat[concat.index("-c:v") + 1] == "copy"
        assert "+faststart" in concat
        # narration muxed as AAC
        assert "-c:a" in concat
        assert concat[concat.index("-c:a") + 1] == "aac"
        assert str(fake_audio) in concat

    async def test_no_audio_skips_audio_mux(self, composer, fake_scene_images, tmp_path):
        output = tmp_path / "recap.mp4"
        captured, capture_thread = _capture()
        with patch("backend.media.ffmpeg_composer.asyncio.to_thread", capture_thread):
            await composer.compose(
                scene_image_paths=fake_scene_images,
                output_path=output,
            )
        concat = next(c for c in captured if _is_concat(c))
        assert "-c:a" not in concat
        assert "-shortest" not in concat

    async def test_per_scene_duration_from_audio(self, fake_scene_images, fake_audio, tmp_path):
        """dur = audio_dur / n so the slideshow exactly covers the narration.

        n=4, audio=60s → 15.000s per segment.
        """
        composer = FFmpegComposer(scene_duration_seconds=5)
        output = tmp_path / "recap.mp4"
        captured, capture_thread = _capture()
        with patch.object(FFmpegComposer, "_probe_audio_duration", return_value=60.0), \
             patch("backend.media.ffmpeg_composer.asyncio.to_thread", capture_thread):
            await composer.compose(
                scene_image_paths=fake_scene_images,
                audio_path=fake_audio,
                output_path=output,
            )
        seg = next(c for c in captured if _is_segment(c))
        assert seg[seg.index("-t") + 1] == "15.000"

    async def test_single_scene(self, composer, tmp_path):
        single_img = tmp_path / "scene_00.jpg"
        single_img.write_bytes(b"\xff\xd8\xff" + b"\x00" * 64)
        output = tmp_path / "recap.mp4"
        captured, capture_thread = _capture()
        with patch("backend.media.ffmpeg_composer.asyncio.to_thread", capture_thread):
            await composer.compose(
                scene_image_paths=[single_img],
                output_path=output,
            )
        assert len([c for c in captured if _is_segment(c)]) == 1
        assert len([c for c in captured if _is_concat(c)]) == 1

    async def test_raises_on_segment_failure(self, composer, fake_scene_images, fake_audio, tmp_path):
        output = tmp_path / "recap.mp4"

        def _fail(returncode: int = 1, stderr: str = "boom") -> AsyncMock:
            proc = MagicMock(returncode=returncode, stderr=stderr)
            return AsyncMock(return_value=proc)

        with patch("backend.media.ffmpeg_composer.asyncio.to_thread", _fail()), \
             pytest.raises(RuntimeError, match="FFmpeg segment failed"):
            await composer.compose(
                scene_image_paths=fake_scene_images,
                audio_path=fake_audio,
                output_path=output,
            )
