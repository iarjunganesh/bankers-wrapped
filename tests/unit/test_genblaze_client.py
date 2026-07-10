"""Unit tests for GenblazeClient — mocks Genblaze SDK and OpenAI."""

from unittest.mock import MagicMock, patch

import pytest

from backend.media.genblaze_client import AudioResult, GenblazeClient, ImageResult


@pytest.fixture
def client() -> GenblazeClient:
    return GenblazeClient(
        gmi_api_key="mock-gmi-key",
        b2_bucket="test-bucket",
        b2_endpoint="https://s3.eu-central-003.backblazeb2.com",
        b2_key_id="test-key-id",
        b2_app_key="test-app-key",
        openai_api_key="sk-test-openai-key",
        nvidia_nim_api_key="nvapi-test-key",
        nvidia_nim_base_url="https://integrate.api.nvidia.com/v1",
    )


class TestGenblazeClientInit:
    def test_stores_openai_api_key(self, client):
        assert client.openai_api_key == "sk-test-openai-key"

    def test_stores_gmi_api_key(self, client):
        assert client.gmi_api_key == "mock-gmi-key"


class TestGenerateNarrationAudio:
    async def test_returns_audio_result(self, client):
        fake_mp3 = b"\xff\xe3" + b"\x00" * 256

        mock_response = MagicMock()
        mock_response.read.return_value = fake_mp3
        mock_openai_instance = MagicMock()
        mock_openai_instance.audio.speech.create.return_value = mock_response

        with patch("backend.media.genblaze_client.openai") as mock_openai_module:
            mock_openai_module.OpenAI.return_value = mock_openai_instance
            result = await client.generate_narration_audio("Hello world narration.")

        assert isinstance(result, AudioResult)
        assert result.audio_bytes == fake_mp3
        assert result.model == "tts-1"
        assert result.voice == "alloy"

    async def test_calls_openai_tts_with_correct_params(self, client):
        mock_response = MagicMock()
        mock_response.read.return_value = b"\xff\xe3\x00"
        mock_openai_instance = MagicMock()
        mock_openai_instance.audio.speech.create.return_value = mock_response

        with patch("backend.media.genblaze_client.openai") as mock_openai_module:
            mock_openai_module.OpenAI.return_value = mock_openai_instance
            await client.generate_narration_audio(
                narration_text="Test narration.",
                model="tts-1-hd",
                voice="nova",
            )

        mock_openai_instance.audio.speech.create.assert_called_once_with(
            model="tts-1-hd",
            voice="nova",
            input="Test narration.",
            response_format="mp3",
        )

    async def test_custom_model_and_voice_reflected_in_result(self, client):
        mock_response = MagicMock()
        mock_response.read.return_value = b"\xff\xe3\x00"
        mock_openai_instance = MagicMock()
        mock_openai_instance.audio.speech.create.return_value = mock_response

        with patch("backend.media.genblaze_client.openai") as mock_openai_module:
            mock_openai_module.OpenAI.return_value = mock_openai_instance
            result = await client.generate_narration_audio(
                "Text", model="tts-1-hd", voice="nova"
            )

        assert result.model == "tts-1-hd"
        assert result.voice == "nova"


class TestGenerateSceneImage:
    async def test_returns_image_result(self, client):
        fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64

        mock_asset = MagicMock()
        mock_asset.url = "https://cdn.gmi.ai/scene_00.png"

        mock_run_obj = MagicMock()
        mock_run_obj.steps = [MagicMock(assets=[mock_asset])]
        mock_manifest = MagicMock()
        mock_manifest.canonical_hash = "sha256:abc123"

        mock_pipeline_result = MagicMock()
        mock_pipeline_result.run = mock_run_obj
        mock_pipeline_result.manifest = mock_manifest

        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.step.return_value = mock_pipeline_instance
        mock_pipeline_instance.run.return_value = mock_pipeline_result

        # Patch at source modules — these are lazily imported inside the method
        with (
            patch("backend.media.genblaze_client.httpx") as mock_httpx,
            patch("genblaze_core.Pipeline", return_value=mock_pipeline_instance),
            patch("genblaze_gmicloud.GMICloudImageProvider"),
            patch("genblaze_core.Modality"),
        ):
            mock_httpx.Client.return_value.__enter__.return_value.get.return_value.content = fake_png
            result = await client.generate_scene_image("A financial scene")

        assert isinstance(result, ImageResult)
        assert result.image_bytes == fake_png
        assert result.manifest_hash == "sha256:abc123"


# ── WS-1: Genblaze chat routing (ADR-007) ────────────────────────────────────

from unittest.mock import AsyncMock  # noqa: E402

from backend.media.genblaze_client import ScriptResult  # noqa: E402


class TestGenerateScriptText:
    async def test_generate_script_text_offloads_to_thread(self, client):
        """The blocking genblaze chat call must run via asyncio.to_thread."""
        fake_resp = MagicMock(
            text='{"title": "T", "scenes": []}',
            model="openai/gpt-5.4-mini",
            tokens_in=900,
            tokens_out=450,
            cost_usd=0.0012,
        )
        with patch(
            "backend.media.genblaze_client.asyncio.to_thread",
            new=AsyncMock(return_value=fake_resp),
        ) as to_thread:
            result = await client.generate_script_text(
                system="system prompt",
                user="user message",
                model="openai/gpt-5.4-mini",
            )

        to_thread.assert_called_once()
        assert isinstance(result, ScriptResult)
        assert result.text == '{"title": "T", "scenes": []}'
        assert result.model == "openai/gpt-5.4-mini"
        assert result.tokens_out == 450
        assert result.cost_usd == 0.0012
        assert result.latency_ms >= 0
        assert result.retry_count == 0

    async def test_gmi_model_uses_default_endpoint_and_computed_cost(self, client):
        """Un-prefixed model ids go to GMI's default endpoint with the GMI key;
        cost is computed from the price table when the SDK reports None."""
        fake_resp = MagicMock(
            text='{"title": "T", "scenes": []}',
            model="openai/gpt-5.4-mini",
            tokens_in=1000,
            tokens_out=1000,
            cost_usd=None,
        )
        with patch("genblaze_gmicloud.chat", return_value=fake_resp) as chat_mock:
            result = await client.generate_script_text(
                system="s", user="u", model="openai/gpt-5.4-mini"
            )

        args, kwargs = chat_mock.call_args
        assert args[0] == "openai/gpt-5.4-mini"
        assert kwargs["base_url"] is None
        assert kwargs["api_key"] == "mock-gmi-key"
        assert result.provider == "gmi-cloud"
        assert result.cost_usd == pytest.approx(0.00525)

    async def test_nim_prefixed_model_routes_to_nim_endpoint(self, client):
        """`nvidia-nim/` ids are stripped and redirected to NIM's endpoint via
        base_url — GMI's catalog knows nothing about our prefix convention."""
        fake_resp = MagicMock(
            text='{"title": "T", "scenes": []}',
            model="meta/llama-3.1-70b-instruct",
            tokens_in=900,
            tokens_out=450,
            cost_usd=None,
        )
        with patch("genblaze_gmicloud.chat", return_value=fake_resp) as chat_mock:
            result = await client.generate_script_text(
                system="s", user="u", model="nvidia-nim/meta/llama-3.1-70b-instruct"
            )

        args, kwargs = chat_mock.call_args
        assert args[0] == "meta/llama-3.1-70b-instruct"  # prefix stripped
        assert kwargs["base_url"] == "https://integrate.api.nvidia.com/v1"
        assert kwargs["api_key"] == "nvapi-test-key"
        assert result.provider == "nvidia-nim"
        assert result.cost_usd == 0.0  # NIM dev tier is free
