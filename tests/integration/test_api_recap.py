"""Integration tests for POST /api/v1/recap/generate endpoint."""

from unittest.mock import AsyncMock, MagicMock, patch

from tests.conftest import SYNTHETIC_CSV


class TestRecapEndpoint:
    def test_health_check(self, api_client):
        response = api_client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_root_returns_name(self, api_client):
        response = api_client.get("/")
        assert response.status_code == 200
        assert "Banker" in response.json()["name"]

    def test_generate_rejects_non_csv(self, api_client):
        response = api_client.post(
            "/api/v1/recap/generate",
            files={"file": ("statement.pdf", b"%PDF-1.4", "application/pdf")},
        )
        assert response.status_code == 422

    def test_generate_rejects_empty_file(self, api_client):
        response = api_client.post(
            "/api/v1/recap/generate",
            files={"file": ("empty.csv", b"", "text/csv")},
        )
        assert response.status_code == 422

    def test_generate_returns_session_id(self, api_client):
        with (
            patch("backend.api.v1.recap.NarrativeAgent") as MockNarrative,
            patch("backend.api.v1.recap.MediaAgent") as MockMedia,
        ):
            _setup_narrative_mock(MockNarrative)
            _setup_media_mock(MockMedia)

            response = api_client.post(
                "/api/v1/recap/generate",
                files={"file": ("jan.csv", SYNTHETIC_CSV, "text/csv")},
            )

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert len(data["session_id"]) == 36  # UUID format

    def test_generate_returns_video_url(self, api_client):
        with (
            patch("backend.api.v1.recap.NarrativeAgent") as MockNarrative,
            patch("backend.api.v1.recap.MediaAgent") as MockMedia,
        ):
            _setup_narrative_mock(MockNarrative)
            _setup_media_mock(MockMedia)

            response = api_client.post(
                "/api/v1/recap/generate",
                files={"file": ("jan.csv", SYNTHETIC_CSV, "text/csv")},
            )

        assert response.status_code == 200
        assert response.json()["video_url"].startswith("https://")

    def test_generate_returns_insights(self, api_client):
        with (
            patch("backend.api.v1.recap.NarrativeAgent") as MockNarrative,
            patch("backend.api.v1.recap.MediaAgent") as MockMedia,
        ):
            _setup_narrative_mock(MockNarrative)
            _setup_media_mock(MockMedia)

            response = api_client.post(
                "/api/v1/recap/generate",
                files={"file": ("jan.csv", SYNTHETIC_CSV, "text/csv")},
            )

        insights = response.json()["insights"]
        assert "period_label" in insights
        assert "personality" in insights
        assert insights["personality"] in [
            "Financial Builder",
            "Financial Optimizer",
            "Financial Explorer",
            "Financial Achiever",
        ]

    def test_generate_returns_b2_keys(self, api_client):
        with (
            patch("backend.api.v1.recap.NarrativeAgent") as MockNarrative,
            patch("backend.api.v1.recap.MediaAgent") as MockMedia,
        ):
            _setup_narrative_mock(MockNarrative)
            _setup_media_mock(MockMedia)

            response = api_client.post(
                "/api/v1/recap/generate",
                files={"file": ("jan.csv", SYNTHETIC_CSV, "text/csv")},
            )

        b2_keys = response.json()["b2_keys"]
        assert isinstance(b2_keys, dict)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _setup_narrative_mock(MockNarrative):
    from backend.models.narrative import NarrativeScript, Scene

    MockNarrative.return_value = AsyncMock(return_value=MagicMock(
        script=NarrativeScript(
            title="Your January Journey",
            personality="Financial Builder",
            scenes=[
                Scene(id=i, narration=f"Scene {i} narration.", visual_prompt=f"Scene {i} visual")
                for i in range(1, 5)
            ],
        )
    ))


def _setup_media_mock(MockMedia):
    from datetime import UTC, datetime

    from backend.models.session import PipelineMetadata

    MockMedia.return_value = AsyncMock(return_value=MagicMock(
        video_url="https://f000.backblazeb2.com/recap.mp4?token=test",
        b2_keys={"video": "user/sess/output/recap.mp4"},
        metadata=PipelineMetadata(
            session_id="test-session",
            user_id="test-user",
            created_at=datetime.now(UTC),
            pipeline_version="1.0.0",
            models_used={
                "llm": "nvidia-nim/meta/llama-3.1-70b-instruct",
                "image": "gmi-cloud/seedream-4-0-250828",
                "compositor": "ffmpeg",
            },
            input_filename="jan.csv",
            input_hash="abc123",
            output_url="https://f000.backblazeb2.com/recap.mp4?token=test",
            processing_time_ms=12345,
        ),
    ))
