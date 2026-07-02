"""Unit tests for MediaAgent — mocks Genblaze, B2, and FFmpeg."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from backend.agents.analytics_agent import AnalyticsAgentOutput
from backend.agents.media_agent import MediaAgent, MediaAgentInput
from backend.agents.narrative_agent import NarrativeAgentOutput
from backend.config import Settings
from backend.media.genblaze_client import AudioResult, ImageResult
from backend.models.insights import CategorySpend, FinancialInsights, FinancialPersonality
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
        "Scene 5 narration.",
    ]
    return NarrativeScript(
        title="Your Financial Year",
        personality="Financial Builder",
        scenes=[
            Scene(id=i + 1, narration=text, visual_prompt=f"Visual prompt {i + 1}")
            for i, text in enumerate(narrations)
        ],
    )


def _make_analytics() -> AnalyticsAgentOutput:
    return AnalyticsAgentOutput(
        insights=FinancialInsights(
            period_label="January 2026",
            total_income=5000.0,
            total_expenses=3000.0,
            savings_amount=2000.0,
            savings_rate=40.0,
            top_categories=[CategorySpend(category="Food", amount=800.0, percentage=26.7)],
            achievements=["Saved 40% of income"],
            personality=FinancialPersonality.BUILDER,
            personality_reason="Strong saver.",
        )
    )


def _make_input(script: NarrativeScript | None = None) -> MediaAgentInput:
    return MediaAgentInput(
        script_output=NarrativeAgentOutput(script=script or _make_script()),
        analytics_output=_make_analytics(),
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


def _make_agent_and_write(tmp_path: Path):
    """
    Build a MediaAgent with all deps mocked.
    FFmpegComposer.compose writes FAKE_VIDEO to output_path so upload_bytes finds a real file.
    Returns (agent, mock_genblaze, mock_b2).
    """
    settings = _make_settings()

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

    with (
        patch("backend.agents.media_agent.B2Client.input_key", return_value="u/s/input/f.csv"),
        patch("backend.agents.media_agent.B2Client.pipeline_key", return_value="u/s/pipeline/script.json"),
        patch("backend.agents.media_agent.B2Client.scene_key", return_value="u/s/scene.png"),
        patch("backend.agents.media_agent.B2Client.narration_key", return_value="u/s/pipeline/narration.mp3"),
        patch("backend.agents.media_agent.B2Client.output_key", return_value="u/s/output/recap.mp4"),
        patch("backend.agents.media_agent.B2Client.metadata_key", return_value="u/s/metadata/meta.json"),
        patch("backend.agents.media_agent.B2Client.analytics_key", return_value="u/s/pipeline/analytics.json"),
        patch("backend.agents.media_agent.B2Client.prompts_key", return_value="u/s/pipeline/prompts.json"),
        patch("backend.agents.media_agent.B2Client.generation_key", return_value="u/s/pipeline/generation.json"),
        patch("backend.agents.media_agent.B2Client.thumbnail_key", return_value="u/s/pipeline/thumbnail.png"),
        patch("backend.agents.media_agent.FFmpegComposer") as MockComposer,
    ):
        async def _compose_and_write(**kwargs: object) -> Path:
            p = kwargs["output_path"]
            assert isinstance(p, Path)
            p.write_bytes(FAKE_VIDEO)
            return p

        MockComposer.return_value.compose = AsyncMock(side_effect=_compose_and_write)
        agent = MediaAgent(settings=settings, genblaze=mock_genblaze, b2=mock_b2)
        agent._composer = MockComposer.return_value
        return agent, mock_genblaze, mock_b2


class TestMediaAgentNarration:
    async def test_generates_narration_from_joined_scene_text(self):
        settings = _make_settings()
        narrations = ["First scene.", "Second scene.", "Third scene.", "Fourth scene.", "Fifth."]
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

        with patch("backend.agents.media_agent.FFmpegComposer") as MockComposer, \
             patch("backend.agents.media_agent.B2Client.input_key", return_value="u/s/input/f.csv"), \
             patch("backend.agents.media_agent.B2Client.pipeline_key", return_value="u/s/pipeline/script.json"), \
             patch("backend.agents.media_agent.B2Client.scene_key", return_value="u/s/scene.png"), \
             patch("backend.agents.media_agent.B2Client.narration_key", return_value="u/s/pipeline/narration.mp3"), \
             patch("backend.agents.media_agent.B2Client.output_key", return_value="u/s/output/recap.mp4"), \
             patch("backend.agents.media_agent.B2Client.metadata_key", return_value="u/s/metadata/meta.json"), \
             patch("backend.agents.media_agent.B2Client.analytics_key", return_value="u/s/pipeline/analytics.json"), \
             patch("backend.agents.media_agent.B2Client.prompts_key", return_value="u/s/pipeline/prompts.json"), \
             patch("backend.agents.media_agent.B2Client.generation_key", return_value="u/s/pipeline/generation.json"), \
             patch("backend.agents.media_agent.B2Client.thumbnail_key", return_value="u/s/pipeline/thumbnail.png"):
            async def _compose_and_write(**kwargs: object) -> Path:
                p = kwargs["output_path"]
                assert isinstance(p, Path)
                p.write_bytes(FAKE_VIDEO)
                return p

            MockComposer.return_value.compose = AsyncMock(side_effect=_compose_and_write)
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

        with patch("backend.agents.media_agent.FFmpegComposer") as MockComposer, \
             patch("backend.agents.media_agent.B2Client.input_key", return_value="u/s/input/f.csv"), \
             patch("backend.agents.media_agent.B2Client.pipeline_key", return_value="u/s/pipeline/script.json"), \
             patch("backend.agents.media_agent.B2Client.scene_key", return_value="u/s/scene.png"), \
             patch("backend.agents.media_agent.B2Client.narration_key", return_value="u/s/pipeline/narration.mp3"), \
             patch("backend.agents.media_agent.B2Client.output_key", return_value="u/s/output/recap.mp4"), \
             patch("backend.agents.media_agent.B2Client.metadata_key", return_value="u/s/metadata/meta.json"), \
             patch("backend.agents.media_agent.B2Client.analytics_key", return_value="u/s/pipeline/analytics.json"), \
             patch("backend.agents.media_agent.B2Client.prompts_key", return_value="u/s/pipeline/prompts.json"), \
             patch("backend.agents.media_agent.B2Client.generation_key", return_value="u/s/pipeline/generation.json"), \
             patch("backend.agents.media_agent.B2Client.thumbnail_key", return_value="u/s/pipeline/thumbnail.png"):
            async def _compose_and_write(**kwargs: object) -> Path:
                p = kwargs["output_path"]
                assert isinstance(p, Path)
                p.write_bytes(FAKE_VIDEO)
                return p

            MockComposer.return_value.compose = AsyncMock(side_effect=_compose_and_write)
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

        with patch("backend.agents.media_agent.FFmpegComposer") as MockComposer, \
             patch("backend.agents.media_agent.B2Client.input_key", return_value="u/s/input/f.csv"), \
             patch("backend.agents.media_agent.B2Client.pipeline_key", return_value="u/s/pipeline/script.json"), \
             patch("backend.agents.media_agent.B2Client.scene_key", return_value="u/s/scene.png"), \
             patch("backend.agents.media_agent.B2Client.narration_key", return_value="u/s/pipeline/narration.mp3"), \
             patch("backend.agents.media_agent.B2Client.output_key", return_value="u/s/output/recap.mp4"), \
             patch("backend.agents.media_agent.B2Client.metadata_key", return_value="u/s/metadata/meta.json"), \
             patch("backend.agents.media_agent.B2Client.analytics_key", return_value="u/s/pipeline/analytics.json"), \
             patch("backend.agents.media_agent.B2Client.prompts_key", return_value="u/s/pipeline/prompts.json"), \
             patch("backend.agents.media_agent.B2Client.generation_key", return_value="u/s/pipeline/generation.json"), \
             patch("backend.agents.media_agent.B2Client.thumbnail_key", return_value="u/s/pipeline/thumbnail.png"):
            async def _compose_and_write(**kwargs: object) -> Path:
                p = kwargs["output_path"]
                assert isinstance(p, Path)
                p.write_bytes(FAKE_VIDEO)
                return p

            MockComposer.return_value.compose = AsyncMock(side_effect=_compose_and_write)
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

        with patch("backend.agents.media_agent.FFmpegComposer") as MockComposer, \
             patch("backend.agents.media_agent.B2Client.input_key", return_value="u/s/input/f.csv"), \
             patch("backend.agents.media_agent.B2Client.pipeline_key", return_value="u/s/pipeline/script.json"), \
             patch("backend.agents.media_agent.B2Client.scene_key", return_value="u/s/scene.png"), \
             patch("backend.agents.media_agent.B2Client.narration_key", return_value="u/s/pipeline/narration.mp3"), \
             patch("backend.agents.media_agent.B2Client.output_key", return_value="u/s/output/recap.mp4"), \
             patch("backend.agents.media_agent.B2Client.metadata_key", return_value="u/s/metadata/meta.json"), \
             patch("backend.agents.media_agent.B2Client.analytics_key", return_value="u/s/pipeline/analytics.json"), \
             patch("backend.agents.media_agent.B2Client.prompts_key", return_value="u/s/pipeline/prompts.json"), \
             patch("backend.agents.media_agent.B2Client.generation_key", return_value="u/s/pipeline/generation.json"), \
             patch("backend.agents.media_agent.B2Client.thumbnail_key", return_value="u/s/pipeline/thumbnail.png"):
            async def _compose_and_write(**kwargs: object) -> Path:
                p = kwargs["output_path"]
                assert isinstance(p, Path)
                p.write_bytes(FAKE_VIDEO)
                return p

            MockComposer.return_value.compose = AsyncMock(side_effect=_compose_and_write)
            agent = MediaAgent(settings=settings, genblaze=mock_genblaze, b2=mock_b2)
            output = await agent(agent_input)

        assert output.metadata.models_used.get("audio") == "openai/tts-1"


class TestMediaAgentAssetManifest:
    """Verify the full B2 asset manifest is uploaded."""

    async def _run(self) -> tuple:
        settings = _make_settings()
        agent_input = _make_input()
        uploaded_json_keys: list[str] = []
        uploaded_bytes_types: list[str] = []

        mock_genblaze = MagicMock()
        mock_genblaze.generate_scene_image = AsyncMock(
            return_value=ImageResult(image_bytes=FAKE_PNG, manifest_hash="sha256:img")
        )
        mock_genblaze.generate_narration_audio = AsyncMock(
            return_value=AudioResult(audio_bytes=FAKE_MP3, model="tts-1", voice="alloy")
        )

        mock_b2 = MagicMock()
        mock_b2.upload_bytes.side_effect = (
            lambda k, d, ct: uploaded_bytes_types.append(ct) or "b2://bucket/k"
        )
        mock_b2.upload_json.side_effect = (
            lambda k, d: uploaded_json_keys.append(k) or "b2://bucket/meta"
        )
        mock_b2.presigned_url.return_value = "https://presigned.url/recap.mp4"

        with patch("backend.agents.media_agent.FFmpegComposer") as MockComposer, \
             patch("backend.agents.media_agent.B2Client.input_key", return_value="u/s/input/f.csv"), \
             patch("backend.agents.media_agent.B2Client.pipeline_key", return_value="u/s/pipeline/script.json"), \
             patch("backend.agents.media_agent.B2Client.scene_key", return_value="u/s/scene.png"), \
             patch("backend.agents.media_agent.B2Client.narration_key", return_value="u/s/pipeline/narration.mp3"), \
             patch("backend.agents.media_agent.B2Client.output_key", return_value="u/s/output/recap.mp4"), \
             patch("backend.agents.media_agent.B2Client.metadata_key", return_value="u/s/metadata/meta.json"), \
             patch("backend.agents.media_agent.B2Client.analytics_key", return_value="u/s/pipeline/analytics.json"), \
             patch("backend.agents.media_agent.B2Client.prompts_key", return_value="u/s/pipeline/prompts.json"), \
             patch("backend.agents.media_agent.B2Client.generation_key", return_value="u/s/pipeline/generation.json"), \
             patch("backend.agents.media_agent.B2Client.thumbnail_key", return_value="u/s/pipeline/thumbnail.png"):
            async def _compose_and_write(**kwargs: object) -> Path:
                p = kwargs["output_path"]
                assert isinstance(p, Path)
                p.write_bytes(FAKE_VIDEO)
                return p

            MockComposer.return_value.compose = AsyncMock(side_effect=_compose_and_write)
            agent = MediaAgent(settings=settings, genblaze=mock_genblaze, b2=mock_b2)
            output = await agent(agent_input)

        return output, uploaded_json_keys, uploaded_bytes_types

    async def test_all_artifact_keys_present(self):
        output, _, _ = await self._run()
        assert "analytics" in output.b2_keys
        assert "prompts" in output.b2_keys
        assert "generation" in output.b2_keys
        assert "thumbnail" in output.b2_keys
        assert "metadata" in output.b2_keys
        assert "script" in output.b2_keys

    async def test_analytics_json_uploaded(self):
        _, json_keys, _ = await self._run()
        assert "u/s/pipeline/analytics.json" in json_keys

    async def test_prompts_json_uploaded(self):
        _, json_keys, _ = await self._run()
        assert "u/s/pipeline/prompts.json" in json_keys

    async def test_generation_json_uploaded(self):
        _, json_keys, _ = await self._run()
        assert "u/s/pipeline/generation.json" in json_keys

    async def test_thumbnail_jpeg_uploaded(self):
        _, _, byte_types = await self._run()
        assert "image/jpeg" in byte_types

    async def test_thumbnail_url_returned(self):
        output, _, _ = await self._run()
        assert output.thumbnail_url.startswith("https://")

    async def test_session_manifest_is_self_contained(self):
        """ADR-008: the B2 manifest alone must be able to serve GET /recap/{id}."""
        settings = _make_settings()
        agent_input = _make_input()
        uploaded_json: dict[str, dict] = {}

        mock_genblaze = MagicMock()
        mock_genblaze.generate_scene_image = AsyncMock(
            return_value=ImageResult(image_bytes=FAKE_PNG, manifest_hash="sha256:img")
        )
        mock_genblaze.generate_narration_audio = AsyncMock(
            return_value=AudioResult(audio_bytes=FAKE_MP3, model="tts-1", voice="alloy")
        )
        mock_b2 = MagicMock()
        mock_b2.upload_bytes.return_value = "b2://bucket/key"
        mock_b2.upload_json.side_effect = (
            lambda k, d: uploaded_json.__setitem__(k, d) or "b2://bucket/meta"
        )
        mock_b2.presigned_url.return_value = "https://presigned.url/recap.mp4"

        with patch("backend.agents.media_agent.FFmpegComposer") as MockComposer, \
             patch("backend.agents.media_agent.B2Client.input_key", return_value="u/s/input/f.csv"), \
             patch("backend.agents.media_agent.B2Client.pipeline_key", return_value="u/s/pipeline/script.json"), \
             patch("backend.agents.media_agent.B2Client.scene_key", return_value="u/s/scene.png"), \
             patch("backend.agents.media_agent.B2Client.narration_key", return_value="u/s/pipeline/narration.mp3"), \
             patch("backend.agents.media_agent.B2Client.output_key", return_value="u/s/output/recap.mp4"), \
             patch("backend.agents.media_agent.B2Client.metadata_key", return_value="u/s/metadata/meta.json"), \
             patch("backend.agents.media_agent.B2Client.analytics_key", return_value="u/s/pipeline/analytics.json"), \
             patch("backend.agents.media_agent.B2Client.prompts_key", return_value="u/s/pipeline/prompts.json"), \
             patch("backend.agents.media_agent.B2Client.generation_key", return_value="u/s/pipeline/generation.json"), \
             patch("backend.agents.media_agent.B2Client.thumbnail_key", return_value="u/s/pipeline/thumbnail.png"):
            async def _compose_and_write(**kwargs: object) -> Path:
                p = kwargs["output_path"]
                assert isinstance(p, Path)
                p.write_bytes(FAKE_VIDEO)
                return p

            MockComposer.return_value.compose = AsyncMock(side_effect=_compose_and_write)
            agent = MediaAgent(settings=settings, genblaze=mock_genblaze, b2=mock_b2)
            output = await agent(agent_input)

        manifest = uploaded_json["u/s/metadata/meta.json"]
        assert manifest["status"] == "complete"
        # Full insights snapshot — enough to hydrate InsightsSummary
        assert manifest["insights"]["personality"] == "Financial Builder"
        assert manifest["insights"]["savings_rate"] == 40.0
        assert manifest["insights"]["top_categories"][0]["category"] == "Food"
        # Every artifact key, including the manifest's own key and generation.json
        for name in ("csv", "script", "analytics", "prompts", "narration",
                     "thumbnail", "video", "metadata", "generation",
                     "scene_0", "scene_4"):
            assert name in manifest["b2_keys"], f"manifest missing b2 key: {name}"
        assert manifest["b2_keys"] == output.b2_keys
        assert manifest["processing_time_ms"] >= 0
        assert "llm" in manifest["models_used"]

    async def test_progress_callback_called(self):
        settings = _make_settings()
        agent_input = _make_input()
        received_events: list[str] = []

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

        def _cb(event: str, _detail: str) -> None:
            received_events.append(event)

        with patch("backend.agents.media_agent.FFmpegComposer") as MockComposer, \
             patch("backend.agents.media_agent.B2Client.input_key", return_value="u/s/input/f.csv"), \
             patch("backend.agents.media_agent.B2Client.pipeline_key", return_value="u/s/pipeline/script.json"), \
             patch("backend.agents.media_agent.B2Client.scene_key", return_value="u/s/scene.png"), \
             patch("backend.agents.media_agent.B2Client.narration_key", return_value="u/s/pipeline/narration.mp3"), \
             patch("backend.agents.media_agent.B2Client.output_key", return_value="u/s/output/recap.mp4"), \
             patch("backend.agents.media_agent.B2Client.metadata_key", return_value="u/s/metadata/meta.json"), \
             patch("backend.agents.media_agent.B2Client.analytics_key", return_value="u/s/pipeline/analytics.json"), \
             patch("backend.agents.media_agent.B2Client.prompts_key", return_value="u/s/pipeline/prompts.json"), \
             patch("backend.agents.media_agent.B2Client.generation_key", return_value="u/s/pipeline/generation.json"), \
             patch("backend.agents.media_agent.B2Client.thumbnail_key", return_value="u/s/pipeline/thumbnail.png"):
            async def _compose_and_write(**kwargs: object) -> Path:
                p = kwargs["output_path"]
                assert isinstance(p, Path)
                p.write_bytes(FAKE_VIDEO)
                return p

            MockComposer.return_value.compose = AsyncMock(side_effect=_compose_and_write)
            agent = MediaAgent(
                settings=settings, genblaze=mock_genblaze, b2=mock_b2, progress_callback=_cb
            )
            await agent(agent_input)

        assert "composing_video" in received_events
        assert "uploading_to_b2" in received_events
