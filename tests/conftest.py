"""Shared pytest fixtures for Banker's Wrapped test suite."""

from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.config import Settings
from backend.models.transaction import Transaction, TransactionCategory

# ── Synthetic CSV ─────────────────────────────────────────────────────────────

SYNTHETIC_CSV = b"""date,description,amount,currency,category
2026-01-03,Salary Deposit,6500.00,USD,income
2026-01-05,ICA Maxi Grocery,-128.40,USD,food
2026-01-10,Mortgage Payment,-12000.00,USD,housing
2026-01-12,Spotify Premium,-9.99,USD,entertainment
2026-01-15,Savings Transfer,-1200.00,USD,savings
2026-01-20,Lufthansa Flight,-312.00,USD,travel
2026-01-22,Salary Deposit,6500.00,USD,income
2026-01-25,ICA Maxi Grocery,-95.00,USD,food
2026-01-28,Telia Mobile,-49.00,USD,utilities
"""

SYNTHETIC_TRANSACTIONS = [
    Transaction(date=date(2026, 1, 3), description="Salary Deposit",
                amount=6500.0, currency="USD", category=TransactionCategory.INCOME),
    Transaction(date=date(2026, 1, 5), description="ICA Maxi Grocery",
                amount=-128.4, currency="USD", category=TransactionCategory.FOOD),
    Transaction(date=date(2026, 1, 15), description="Savings Transfer",
                amount=-1200.0, currency="USD", category=TransactionCategory.SAVINGS),
    Transaction(date=date(2026, 1, 20), description="Lufthansa Flight",
                amount=-312.0, currency="USD", category=TransactionCategory.TRAVEL),
    Transaction(date=date(2026, 1, 22), description="Salary Deposit",
                amount=6500.0, currency="USD", category=TransactionCategory.INCOME),
]


@pytest.fixture
def synthetic_csv() -> bytes:
    return SYNTHETIC_CSV


@pytest.fixture
def synthetic_transactions() -> list[Transaction]:
    return SYNTHETIC_TRANSACTIONS


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        openai_api_key="sk-test-key",  # fallback LLM only; mocked in tests
        gmi_api_key="mock-gmi-key",
        elevenlabs_api_key="el-test-key",
        b2_key_id="b2-test-key-id",
        b2_application_key="b2-test-app-key",
        b2_endpoint_url="https://s3.us-west-004.backblazeb2.com",
        b2_bucket_name="test-bucket",
    )


# ── Genblaze mocks ────────────────────────────────────────────────────────────

FAKE_MP3_BYTES = b"\xff\xe0" + b"\x00" * 1024  # Minimal MP3 magic bytes
FAKE_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n"  # PNG magic bytes
    + b"\x00" * 64         # Minimal PNG data
)


@pytest.fixture
def mock_genblaze_client():
    """Mock GenblazeClient — no real Genblaze/OpenAI calls made."""
    with patch("backend.agents.media_agent.GenblazeClient") as MockClass:
        instance = MockClass.return_value
        from backend.media.genblaze_client import AudioResult, ImageResult

        instance.synthesize_narration = AsyncMock(
            return_value=AudioResult(
                audio_bytes=FAKE_MP3_BYTES,
                manifest_hash="sha256:fake-audio-hash",
            )
        )
        instance.generate_scene_image = AsyncMock(
            return_value=ImageResult(
                image_bytes=FAKE_PNG_BYTES,
                manifest_hash="sha256:fake-image-hash",
            )
        )
        yield instance


@pytest.fixture
def mock_b2_client():
    """Mock B2Client — no real B2 calls made."""
    with patch("backend.agents.media_agent.B2Client") as MockClass:
        instance = MockClass.return_value
        instance.upload_bytes = MagicMock(return_value="b2://test-bucket/key")
        instance.upload_json = MagicMock(return_value="b2://test-bucket/meta.json")
        instance.presigned_url = MagicMock(
            return_value="https://f000.backblazeb2.com/test-bucket/recap.mp4?token=abc"
        )
        yield instance


@pytest.fixture
def mock_ffmpeg_composer():
    """Mock FFmpegComposer — no real ffmpeg calls made."""
    with patch("backend.agents.media_agent.FFmpegComposer") as MockClass:
        instance = MockClass.return_value
        instance.compose = MagicMock(side_effect=lambda **kwargs: kwargs["output_path"])
        yield instance


# ── FastAPI test client ───────────────────────────────────────────────────────

@pytest.fixture
def api_client(test_settings):
    """FastAPI test client with settings override."""
    from backend.main import app
    from backend.config import get_settings

    app.dependency_overrides[get_settings] = lambda: test_settings
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
