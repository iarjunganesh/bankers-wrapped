"""Integration tests for the recap API endpoints."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from backend.api.v1.recap import get_b2, get_session_store
from tests.conftest import SYNTHETIC_CSV

INSIGHTS_DICT = {
    "period_label": "January 2026",
    "total_income": 5000.0,
    "total_expenses": 3000.0,
    "savings_amount": 2000.0,
    "savings_rate": 40.0,
    "top_categories": [{"category": "Food", "amount": 800.0, "percentage": 26.7}],
    "achievements": ["Saved 40% of income"],
    "personality": "Financial Builder",
    "personality_reason": "Strong saver.",
    "currency": "USD",
}


def _override_b2(api_client) -> MagicMock:
    """Stub the B2 dependency so pipeline tests never touch the network."""
    from backend.main import app

    fake_b2 = MagicMock()
    fake_b2.upload_json.return_value = "b2://bucket/index"
    fake_b2.presigned_url.return_value = "https://f000.backblazeb2.com/artifact?token=fresh"
    app.dependency_overrides[get_b2] = lambda: fake_b2
    return fake_b2


def _fake_b2_with_manifest(session_id: str, user_id: str = "user-b2") -> MagicMock:
    """A B2Client double serving the flat index + a complete session manifest."""
    manifest = {
        "session_id": session_id,
        "user_id": user_id,
        "status": "complete",
        "insights": INSIGHTS_DICT,
        "b2_keys": {
            "video": f"{user_id}/{session_id}/output/recap_{session_id}.mp4",
            "thumbnail": f"{user_id}/{session_id}/pipeline/thumbnail.jpg",
            "metadata": f"{user_id}/{session_id}/metadata/session_metadata.json",
        },
        "processing_time_ms": 4242,
        "models_used": {"llm": "nvidia-nim/meta/llama-3.1-70b-instruct"},
        "output_url": "https://stale.presigned.url/recap.mp4",
    }
    fake_b2 = MagicMock()
    fake_b2.download_json.side_effect = lambda key: (
        {"session_id": session_id, "user_id": user_id}
        if key.startswith("index/")
        else manifest
    )
    fake_b2.presigned_url.return_value = "https://fresh.presigned.url/artifact"
    fake_b2.download_bytes.return_value = b"fake artifact bytes"
    return fake_b2


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

    def test_generate_rejects_binary_disguised_as_csv(self, api_client):
        png_magic = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
        response = api_client.post(
            "/api/v1/recap/generate",
            files={"file": ("transactions.csv", png_magic, "text/csv")},
        )
        assert response.status_code == 422
        assert "CSV" in response.json()["detail"]

    def test_generate_rejects_empty_file(self, api_client):
        response = api_client.post(
            "/api/v1/recap/generate",
            files={"file": ("empty.csv", b"", "text/csv")},
        )
        assert response.status_code == 422

    def test_generate_returns_202_with_session_id(self, api_client):
        _override_b2(api_client)
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

        assert response.status_code == 202
        data = response.json()
        assert "session_id" in data
        assert len(data["session_id"]) == 36  # UUID format

    def test_generate_result_available_via_get(self, api_client):
        """After 202, the GET endpoint returns the completed recap."""
        _override_b2(api_client)
        with (
            patch("backend.api.v1.recap.NarrativeAgent") as MockNarrative,
            patch("backend.api.v1.recap.MediaAgent") as MockMedia,
        ):
            _setup_narrative_mock(MockNarrative)
            _setup_media_mock(MockMedia)

            post_resp = api_client.post(
                "/api/v1/recap/generate",
                files={"file": ("jan.csv", SYNTHETIC_CSV, "text/csv")},
            )

        assert post_resp.status_code == 202
        session_id = post_resp.json()["session_id"]

        get_resp = api_client.get(f"/api/v1/recap/{session_id}")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["video_url"].startswith("https://")
        assert data["thumbnail_url"].startswith("https://")
        assert isinstance(data["b2_keys"], dict)

    def test_generate_result_has_insights(self, api_client):
        _override_b2(api_client)
        with (
            patch("backend.api.v1.recap.NarrativeAgent") as MockNarrative,
            patch("backend.api.v1.recap.MediaAgent") as MockMedia,
        ):
            _setup_narrative_mock(MockNarrative)
            _setup_media_mock(MockMedia)

            post_resp = api_client.post(
                "/api/v1/recap/generate",
                files={"file": ("jan.csv", SYNTHETIC_CSV, "text/csv")},
            )

        session_id = post_resp.json()["session_id"]
        get_resp = api_client.get(f"/api/v1/recap/{session_id}")
        insights = get_resp.json()["insights"]
        assert "period_label" in insights
        assert "personality" in insights
        assert insights["personality"] in [
            "Financial Builder",
            "Financial Optimizer",
            "Financial Explorer",
            "Financial Achiever",
        ]

    def test_download_zip_returns_404_for_unknown_session(self, api_client):
        response = api_client.get("/api/v1/recap/no-such-session/download")
        assert response.status_code == 404

    def test_download_zip_returns_zip_for_complete_session(self, api_client):
        store = get_session_store()
        sid = str(uuid.uuid4())
        store.create(sid, "test-user")
        store.set_complete(
            sid,
            output_url="https://presigned.url/recap.mp4",
            metadata={
                "b2_keys": {"video": "u/s/output/recap.mp4"},
                "insights": {
                    "period_label": "Jan 2026",
                    "total_income": 5000.0,
                    "total_expenses": 3000.0,
                    "savings_amount": 2000.0,
                    "savings_rate": 40.0,
                    "top_categories": [],
                    "achievements": [],
                    "personality": "Financial Builder",
                    "personality_reason": "Strong saver.",
                    "currency": "USD",
                },
                "processing_time_ms": 12345,
                "thumbnail_url": "https://presigned.url/thumbnail.png",
            },
        )

        fake_b2 = MagicMock()
        fake_b2.download_bytes.return_value = b"fake video bytes"

        with patch("backend.api.v1.recap.get_b2", return_value=fake_b2):
            response = api_client.get(f"/api/v1/recap/{sid}/download")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"


class TestB2SourceOfTruth:
    """ADR-008: sessions survive a redeploy — B2 manifest serves cache misses."""

    def test_get_recap_falls_back_to_b2_when_sqlite_missing(self, api_client):
        from backend.main import app

        sid = str(uuid.uuid4())  # never written to the SQLite store
        app.dependency_overrides[get_b2] = lambda: _fake_b2_with_manifest(sid)

        response = api_client.get(f"/api/v1/recap/{sid}")

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == sid
        assert data["insights"]["personality"] == "Financial Builder"
        assert data["processing_time_ms"] == 4242
        # Presigned URLs are re-minted from the manifest's b2_keys, not reused
        assert data["video_url"] == "https://fresh.presigned.url/artifact"
        assert data["thumbnail_url"] == "https://fresh.presigned.url/artifact"

    def test_get_recap_404_when_b2_has_no_manifest(self, api_client):
        from backend.main import app

        fake_b2 = MagicMock()
        fake_b2.download_json.side_effect = Exception("NoSuchKey")
        app.dependency_overrides[get_b2] = lambda: fake_b2

        response = api_client.get(f"/api/v1/recap/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_download_zip_falls_back_to_b2_when_sqlite_missing(self, api_client):
        from backend.main import app

        sid = str(uuid.uuid4())
        app.dependency_overrides[get_b2] = lambda: _fake_b2_with_manifest(sid)

        response = api_client.get(f"/api/v1/recap/{sid}/download")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"

    def test_index_write_failure_is_nonfatal(self, api_client):
        """A failed session-index write must not abort the generation."""
        from backend.main import app

        fake_b2 = MagicMock()
        fake_b2.upload_json.side_effect = Exception("B2 hiccup")
        fake_b2.presigned_url.return_value = "https://f000.backblazeb2.com/a?t=1"
        app.dependency_overrides[get_b2] = lambda: fake_b2

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

        assert response.status_code == 202
        sid = response.json()["session_id"]
        # Pipeline completed despite the index failure
        assert api_client.get(f"/api/v1/recap/{sid}").status_code == 200

    def test_get_recap_404_when_manifest_not_complete(self, api_client):
        from backend.main import app

        sid = str(uuid.uuid4())
        fake_b2 = MagicMock()
        fake_b2.download_json.side_effect = lambda key: (
            {"session_id": sid, "user_id": "u"}
            if key.startswith("index/")
            else {"status": "processing"}
        )
        app.dependency_overrides[get_b2] = lambda: fake_b2

        assert api_client.get(f"/api/v1/recap/{sid}").status_code == 404

    def test_session_index_written_at_pipeline_start(self, api_client):
        from backend.main import app

        fake_b2 = MagicMock()
        fake_b2.upload_json.return_value = "b2://bucket/index"
        app.dependency_overrides[get_b2] = lambda: fake_b2

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

        assert response.status_code == 202
        sid = response.json()["session_id"]
        index_calls = [
            c for c in fake_b2.upload_json.call_args_list
            if c.args[0] == f"index/{sid}.json"
        ]
        assert len(index_calls) == 1
        assert index_calls[0].args[1]["user_id"]  # index maps session -> user


# ── Helpers ───────────────────────────────────────────────────────────────────

def _setup_narrative_mock(MockNarrative):
    from backend.models.narrative import NarrativeScript, Scene

    MockNarrative.return_value = AsyncMock(return_value=MagicMock(
        script=NarrativeScript(
            title="Your January Journey",
            personality="Financial Builder",
            scenes=[
                Scene(id=i, narration=f"Scene {i} narration.", visual_prompt=f"Scene {i} visual")
                for i in range(1, 6)
            ],
        )
    ))


def _setup_media_mock(MockMedia):
    from datetime import UTC, datetime

    from backend.models.session import PipelineMetadata

    MockMedia.return_value = AsyncMock(return_value=MagicMock(
        video_url="https://f000.backblazeb2.com/recap.mp4?token=test",
        thumbnail_url="https://f000.backblazeb2.com/thumbnail.png?token=test",
        b2_keys={
            "video": "user/sess/output/recap.mp4",
            "thumbnail": "user/sess/pipeline/thumbnail.png",
            "analytics": "user/sess/pipeline/analytics.json",
            "prompts": "user/sess/pipeline/prompts.json",
            "generation": "user/sess/pipeline/generation.json",
        },
        metadata=PipelineMetadata(
            session_id="test-session",
            user_id="test-user",
            created_at=datetime.now(UTC),
            pipeline_version="1.0.0",
            models_used={
                "llm": "nvidia-nim/meta/llama-3.1-70b-instruct",
                "image": "gmi-cloud/seedream-4-0-250828",
                "audio": "openai/tts-1",
                "compositor": "ffmpeg",
            },
            input_filename="jan.csv",
            input_hash="abc123",
            output_url="https://f000.backblazeb2.com/recap.mp4?token=test",
            processing_time_ms=12345,
        ),
    ))
