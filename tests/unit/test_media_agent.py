"""Unit tests for MediaAgent — mocks Genblaze, B2, and FFmpeg."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.agents.media_agent import MediaAgent, MediaAgentInput
from backend.agents.narrative_agent import NarrativeAgentOutput
from backend.config import Settings
from backend.media.genblaze_client import AudioResult, ImageResult
from backend.models.narrative import NarrativeScript, Scene

FAKE_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
FAKE_MP3 = b"\xff\xe3" + b"\x00" * 256
FAKE_VIDEO = b"\x00\x00\x00\x18ftyp" + b"\x00" * 128


def _make_script(narrations: list[str] | None = None) -> NarrativeScript:
    narrations = narrations or [
        "Scene 1 narration.",
        "Scene 2 narration.",
        "Scene 3 narration.",
        "Scene 4 narration.",
    ]
    return NarrativeScript(
        title="Your Financial Year",
        personality="Financial Builder",
        scenes=[
            Scene(id=i + 1, narration=text, visual_prompt=f"Visual prompt {i + 1}")
            for i, text in enumerate(narrations)
        ],
    )


def _make_input(script: NarrativeScript | None = None) -> MediaAgentInput:
    return MediaAgentInput(
        script_output=NarrativeAgentOutput(script=script or _make_script()),
        session_id="test-session-id",
        user_id="test-user-id",
        csv_bytes=b"date,description,amount\n2026-01-01,Salary,1000.0\n",
        input_hash="sha256:abc123",
        input_filename="transactions.csv",
    )


def _make_settings() -> Settings:
    return Settings(
        openai_api_key="sk-test",
        openai_tts_model="tts-1",
        openai_tts_voice="alloy",
        gmi_api_key="mock-gmi",
        gmi_image_model="seedream-4-0-250828",
        b2_key_id="key",
        b2_application_key="appkey",
        b2_endpoint_url="https://s3.eu-central-003.backblazeb2.com",
        b2_bucket_name="test-bucket",
    )


@pytest.fixture
def mock_genblaze():
    client = MagicMock()
    client.generate_scene_image = AsyncMock(
        return_value=ImageResult(image_bytes=FAKE_PNG, manifest_hash="sha256:img")
    )
    client.generate_narration_audio = AsyncMock(
        return_value=AudioResult(audio_bytes=FAKE_MP3, model="tts-1", voice="alloy")
    )
    return client


@pytest.fixture
def mock_b2():
    client = MagicMock()
    client.upload_bytes = MagicMock(return_value="b2://test-bucket/key")
    client.upload_json = MagicMock(return_value="b2://test-bucket/meta.json")
    client.presigned_url = MagicMock(return_value="https://presigned.url/recap.mp4")
    # Static methods must be patched separately; set return values via side_effect on class
    client.input_key = MagicMock(return_value="user/sess/input/transactions.csv")
    client.pipeline_key = MagicMock(return_value="user/sess/pipeline/script.json")
    client.scene_key = MagicMock(side_effect=lambda u, s, i: f"user/sess/pipeline/scenes/scene_{i:02d}.png")
    client.narration_key = MagicMock(return_value="user/sess/pipeline/narration.mp3")
    client.output_key = MagicMock(return_value="user/sess/output/recap_test-session-id.mp4")
    client.metadata_key = MagicMock(return_value="user/sess/metadata/session_metadata.json")
    return client


@pytest.fixture
def media_agent(mock_genblaze, mock_b2):
    settings = _make_settings()
    with patch("backend.agents.media_agent.FFmpegComposer") as MockComposer:
        instance = MockComposer.return_value
        instance.compose = AsyncMock(side_effect=lambda **kwargs: kwargs["output_path"])
        with (
            patch.object(type(mock_b2), "input_key", staticmethod(lambda u, s, f: f"{u}/{s}/input/{f}")),
            patch.object(type(mock_b2), "pipeline_key", staticmethod(lambda u, s, f: f"{u}/{s}/pipeline/{f}")),
            patch.object(type(mock_b2), "scene_key", staticmethod(lambda u, s, i: f"{u}/{s}/pipeline/scenes/scene_{i:02d}.png")),
            patch.object(type(mock_b2), "narration_key", staticmethod(lambda u, s: f"{u}/{s}/pipeline/narration.mp3")),
            patch.object(type(mock_b2), "output_key", staticmethod(lambda u, s: f"{u}/{s}/output/recap_{s}.mp4")),
            patch.object(type(mock_b2), "metadata_key", staticmethod(lambda u, s: f"{u}/{s}/metadata/session_metadata.json")),
        ):
            agent = MediaAgent(settings=settings, genblaze=mock_genblaze, b2=mock_b2)
            agent._composer = instance
            yield agent, instance, mock_genblaze, mock_b2


class TestMediaAgentNarration:
    async def test_generates_narration_from_joined_scene_text(self):
        settings = _make_settings()
        narrations = ["First scene.", "Second scene.", "Third scene.", "Fourth scene."]
        script = _make_script(narrations)
        agent_input = _make_input(script)
        expected_text = " ".join(narrations)

        mock_genblaze = MagicMock()
        mock_genblaze.generate_scene_image = AsyncMock(
            return_value=ImageResult(image_bytes=FAKE_PNG, manifest_hash="sha256:img")
        )
        audio_mock = AsyncMock(
            return_value=AudioResult(audio_bytes=FAKE_MP3, model="tts-1", voice="alloy")
        )
        mock_genblaze.generate_narration_audio = audio_mock

        mock_b2 = MagicMock()
        mock_b2.upload_bytes.return_value = "b2://bucket/key"
        mock_b2.upload_json.return_value = "b2://bucket/meta"
        mock_b2.presigned_url.return_value = "https://presigned.url/recap.mp4"

        with patch("backend.agents.media_agent.FFmpegComposer") as MockComposer:
            async def _compose_and_write(**kwargs: object) -> Path:
                p = kwargs["output_path"]
                assert isinstance(p, Path)
                p.write_bytes(FAKE_VIDEO)
                return p

            MockComposer.return_value.compose = AsyncMock(side_effect=_compose_and_write)
            with (
                patch("backend.agents.media_agent.B2Client.input_key", return_value="u/s/input/f.csv"),
                patch("backend.agents.media_agent.B2Client.pipeline_key", return_value="u/s/pipeline/script.json"),
                patch("backend.agents.media_agent.B2Client.scene_key", return_value="u/s/scene.png"),
                patch("backend.agents.media_agent.B2Client.narration_key", return_value="u/s/pipeline/narration.mp3"),
                patch("backend.agents.media_agent.B2Client.output_key", return_value="u/s/output/recap.mp4"),
                patch("backend.agents.media_agent.B2Client.metadata_key", return_value="u/s/metadata/meta.json"),
            ):
                agent = MediaAgent(settings=settings, genblaze=mock_genblaze, b2=mock_b2)
                await agent(agent_input)

        audio_mock.assert_called_once_with(
            narration_text=expected_text,
            model="tts-1",
            voice="alloy",
        )

    async def test_uploads_narration_to_b2(self):
        settings = _make_settings()
        agent_input = _make_input()

        mock_genblaze = MagicMock()
        mock_genblaze.generate_scene_image = AsyncMock(
            return_value=ImageResult(image_bytes=FAKE_PNG, manifest_hash="sha256:img")
        )
        mock_genblaze.generate_narration_audio = AsyncMock(
            return_value=AudioResult(audio_bytes=FAKE_MP3, model="tts-1", voice="alloy")
        )

        upload_calls: list = []
        mock_b2 = MagicMock()
        mock_b2.upload_bytes.side_effect = lambda k, d, ct: upload_calls.append((k, ct)) or "b2://bucket/k"
        mock_b2.upload_json.return_value = "b2://bucket/meta"
        mock_b2.presigned_url.return_value = "https://presigned.url/recap.mp4"

        with patch("backend.agents.media_agent.FFmpegComposer") as MockComposer:
            async def _compose_and_write(**kwargs: object) -> Path:
                p = kwargs["output_path"]
                assert isinstance(p, Path)
                p.write_bytes(FAKE_VIDEO)
                return p

            MockComposer.return_value.compose = AsyncMock(side_effect=_compose_and_write)
            with (
                patch("backend.agents.media_agent.B2Client.input_key", return_value="u/s/input/f.csv"),
                patch("backend.agents.media_agent.B2Client.pipeline_key", return_value="u/s/pipeline/script.json"),
                patch("backend.agents.media_agent.B2Client.scene_key", return_value="u/s/scene.png"),
                patch("backend.agents.media_agent.B2Client.narration_key", return_value="u/s/pipeline/narration.mp3"),
                patch("backend.agents.media_agent.B2Client.output_key", return_value="u/s/output/recap.mp4"),
                patch("backend.agents.media_agent.B2Client.metadata_key", return_value="u/s/metadata/meta.json"),
            ):
                agent = MediaAgent(settings=settings, genblaze=mock_genblaze, b2=mock_b2)
                await agent(agent_input)

        content_types = [ct for _, ct in upload_calls]
        assert "audio/mpeg" in content_types

    async def test_narration_b2_key_in_output(self):
        settings = _make_settings()
        agent_input = _make_input()

        mock_genblaze = MagicMock()
        mock_genblaze.generate_scene_image = AsyncMock(
            return_value=ImageResult(image_bytes=FAKE_PNG, manifest_hash="sha256:img")
        )
        mock_genblaze.generate_narration_audio = AsyncMock(
            return_value=AudioResult(audio_bytes=FAKE_MP3, model="tts-1", voice="alloy")
        )
        mock_b2 = MagicMock()
        mock_b2.upload_bytes.return_value = "b2://bucket/key"
        mock_b2.upload_json.return_value = "b2://bucket/meta"
        mock_b2.presigned_url.return_value = "https://presigned.url/recap.mp4"

        with patch("backend.agents.media_agent.FFmpegComposer") as MockComposer:
            async def _compose_and_write(**kwargs: object) -> Path:
                p = kwargs["output_path"]
                assert isinstance(p, Path)
                p.write_bytes(FAKE_VIDEO)
                return p

            MockComposer.return_value.compose = AsyncMock(side_effect=_compose_and_write)
            with (
                patch("backend.agents.media_agent.B2Client.input_key", return_value="u/s/input/f.csv"),
                patch("backend.agents.media_agent.B2Client.pipeline_key", return_value="u/s/pipeline/script.json"),
                patch("backend.agents.media_agent.B2Client.scene_key", return_value="u/s/scene.png"),
                patch("backend.agents.media_agent.B2Client.narration_key", return_value="u/s/pipeline/narration.mp3"),
                patch("backend.agents.media_agent.B2Client.output_key", return_value="u/s/output/recap.mp4"),
                patch("backend.agents.media_agent.B2Client.metadata_key", return_value="u/s/metadata/meta.json"),
            ):
                agent = MediaAgent(settings=settings, genblaze=mock_genblaze, b2=mock_b2)
                output = await agent(agent_input)

        assert "narration" in output.b2_keys

    async def test_audio_model_in_metadata(self):
        settings = _make_settings()
        agent_input = _make_input()

        mock_genblaze = MagicMock()
        mock_genblaze.generate_scene_image = AsyncMock(
            return_value=ImageResult(image_bytes=FAKE_PNG, manifest_hash="sha256:img")
        )
        mock_genblaze.generate_narration_audio = AsyncMock(
            return_value=AudioResult(audio_bytes=FAKE_MP3, model="tts-1", voice="alloy")
        )
        mock_b2 = MagicMock()
        mock_b2.upload_bytes.return_value = "b2://bucket/key"
        mock_b2.upload_json.return_value = "b2://bucket/meta"
        mock_b2.presigned_url.return_value = "https://presigned.url/recap.mp4"

        with patch("backend.agents.media_agent.FFmpegComposer") as MockComposer:
            async def _compose_and_write(**kwargs: object) -> Path:
                p = kwargs["output_path"]
                assert isinstance(p, Path)
                p.write_bytes(FAKE_VIDEO)
                return p

            MockComposer.return_value.compose = AsyncMock(side_effect=_compose_and_write)
            with (
                patch("backend.agents.media_agent.B2Client.input_key", return_value="u/s/input/f.csv"),
                patch("backend.agents.media_agent.B2Client.pipeline_key", return_value="u/s/pipeline/script.json"),
                patch("backend.agents.media_agent.B2Client.scene_key", return_value="u/s/scene.png"),
                patch("backend.agents.media_agent.B2Client.narration_key", return_value="u/s/pipeline/narration.mp3"),
                patch("backend.agents.media_agent.B2Client.output_key", return_value="u/s/output/recap.mp4"),
                patch("backend.agents.media_agent.B2Client.metadata_key", return_value="u/s/metadata/meta.json"),
            ):
                agent = MediaAgent(settings=settings, genblaze=mock_genblaze, b2=mock_b2)
                output = await agent(agent_input)

        assert output.metadata.models_used.get("audio") == "openai/tts-1"
