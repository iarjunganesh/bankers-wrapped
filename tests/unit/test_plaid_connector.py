"""Unit tests for the Plaid sandbox connector (ADR-010) — Plaid API mocked."""

from datetime import date
from unittest.mock import AsyncMock, patch

import pytest

from backend.config import Settings
from backend.ingest.plaid_connector import (
    PlaidConnector,
    map_plaid_category,
    normalize_plaid_transaction,
    transactions_to_csv,
)
from backend.models.transaction import Transaction, TransactionCategory


def _plaid_settings() -> Settings:
    return Settings(
        plaid_client_id="test-plaid-id",
        plaid_secret="test-plaid-secret",
        plaid_env="sandbox",
    )


class TestCategoryMapping:
    def test_plaid_category_mapping(self):
        assert map_plaid_category("FOOD_AND_DRINK") == TransactionCategory.FOOD
        assert map_plaid_category("INCOME") == TransactionCategory.INCOME
        assert map_plaid_category("LOAN_PAYMENTS") == TransactionCategory.DEBT
        assert map_plaid_category("RENT_AND_UTILITIES") == TransactionCategory.HOUSING
        assert map_plaid_category("TRAVEL") == TransactionCategory.TRAVEL
        assert map_plaid_category("TRANSFER_OUT") == TransactionCategory.SAVINGS

    def test_unknown_and_missing_categories_fall_back_to_other(self):
        assert map_plaid_category("SOMETHING_NEW") == TransactionCategory.OTHER
        assert map_plaid_category(None) == TransactionCategory.OTHER
        assert map_plaid_category("") == TransactionCategory.OTHER


class TestNormalization:
    def test_fetch_transactions_normalizes_to_transaction_model(self):
        # Plaid sign convention: positive = outflow. An expense of $12.50:
        expense = normalize_plaid_transaction({
            "date": "2026-06-15",
            "name": "Starbucks",
            "merchant_name": "Starbucks",
            "amount": 12.50,
            "iso_currency_code": "USD",
            "personal_finance_category": {"primary": "FOOD_AND_DRINK"},
        })
        assert isinstance(expense, Transaction)
        assert expense.amount == -12.50  # ours: expense negative
        assert expense.category == TransactionCategory.FOOD
        assert expense.date == date(2026, 6, 15)

        # Plaid inflow (negative) becomes our positive income
        salary = normalize_plaid_transaction({
            "date": "2026-06-01",
            "name": "ACME PAYROLL",
            "merchant_name": None,
            "amount": -6500.0,
            "iso_currency_code": "USD",
            "personal_finance_category": {"primary": "INCOME"},
        })
        assert salary.amount == 6500.0
        assert salary.category == TransactionCategory.INCOME
        assert salary.description == "ACME PAYROLL"

    def test_missing_optional_fields_get_defaults(self):
        t = normalize_plaid_transaction({
            "date": "2026-06-02",
            "name": None,
            "amount": 10.0,
            "iso_currency_code": None,
        })
        assert t.description == "Unknown"
        assert t.currency == "USD"
        assert t.category == TransactionCategory.OTHER


class TestCsvSerialization:
    async def test_transactions_to_csv_roundtrips_through_document_agent(self):
        """The serialised CSV must be accepted by the same DocumentAgent as uploads."""
        from backend.agents.document_agent import DocumentAgent, DocumentAgentInput

        original = [
            Transaction(date=date(2026, 6, 1), description="ACME PAYROLL",
                        amount=6500.0, currency="USD",
                        category=TransactionCategory.INCOME),
            Transaction(date=date(2026, 6, 15), description="Starbucks",
                        amount=-12.5, currency="USD",
                        category=TransactionCategory.FOOD),
        ]
        csv_bytes = transactions_to_csv(original)

        output = await DocumentAgent()(
            DocumentAgentInput(csv_bytes=csv_bytes, filename="plaid_sandbox.csv")
        )
        parsed = output.transactions
        assert len(parsed) == 2
        assert parsed[0].amount == 6500.0
        assert parsed[0].category == TransactionCategory.INCOME
        assert parsed[1].amount == -12.5
        assert parsed[1].category == TransactionCategory.FOOD


class TestFetchPagination:
    async def test_fetch_transactions_paginates_until_total(self):
        connector = PlaidConnector(_plaid_settings())
        page1 = {
            "total_transactions": 3,
            "transactions": [
                {"date": "2026-06-01", "name": "A", "amount": 1.0},
                {"date": "2026-06-02", "name": "B", "amount": 2.0},
            ],
        }
        page2 = {
            "total_transactions": 3,
            "transactions": [
                {"date": "2026-06-03", "name": "C", "amount": 3.0},
            ],
        }
        with patch.object(
            PlaidConnector, "_post", new=AsyncMock(side_effect=[page1, page2])
        ) as mock_post:
            result = await connector.fetch_transactions(
                "access-token", date(2026, 6, 1), date(2026, 6, 30)
            )

        assert [t.description for t in result] == ["A", "B", "C"]
        assert mock_post.call_count == 2
        second_call_payload = mock_post.call_args_list[1].args[1]
        assert second_call_payload["options"]["offset"] == 2

    async def test_sandbox_host_selected_from_env(self):
        connector = PlaidConnector(_plaid_settings())
        assert connector.base_url == "https://sandbox.plaid.com"


@pytest.fixture
def plaid_api_client():
    """TestClient with Plaid enabled in settings and rate limiting disabled."""
    from fastapi.testclient import TestClient

    from backend.api.limiter import limiter
    from backend.config import get_settings
    from backend.main import app

    settings = Settings(
        openai_api_key="sk-test-key",
        gmi_api_key="mock-gmi-key",
        b2_key_id="b2-test-key-id",
        b2_application_key="b2-test-app-key",
        b2_endpoint_url="https://s3.us-west-004.backblazeb2.com",
        b2_bucket_name="test-bucket",
        plaid_client_id="test-plaid-id",
        plaid_secret="test-plaid-secret",
    )
    app.dependency_overrides[get_settings] = lambda: settings
    limiter.enabled = False
    with TestClient(app) as client:
        yield client
    limiter.enabled = True
    app.dependency_overrides.clear()


class TestPlaidRoutes:
    def test_plaid_routes_404_when_disabled(self, api_client):
        """Without PLAID_* keys the app boots and Plaid endpoints answer 404."""
        assert api_client.post("/api/v1/plaid/link-token").status_code == 404
        resp = api_client.post(
            "/api/v1/plaid/exchange", json={"public_token": "public-sandbox-x"}
        )
        assert resp.status_code == 404

    # Note: these two must stay separate tests — both fixtures override the
    # same get_settings dependency on the shared app, so the last one wins.
    def test_health_reports_plaid_disabled(self, api_client):
        assert api_client.get("/api/v1/health").json()["plaid_enabled"] is False

    def test_health_reports_plaid_enabled(self, plaid_api_client):
        assert plaid_api_client.get("/api/v1/health").json()["plaid_enabled"] is True

    def test_link_token_returned_when_enabled(self, plaid_api_client):
        with patch("backend.api.v1.plaid.PlaidConnector") as MockConnector:
            MockConnector.return_value.create_link_token = AsyncMock(
                return_value="link-sandbox-token-123"
            )
            resp = plaid_api_client.post("/api/v1/plaid/link-token")
        assert resp.status_code == 200
        assert resp.json()["link_token"] == "link-sandbox-token-123"

    def test_exchange_kicks_same_pipeline(self, plaid_api_client):
        """public_token → sandbox transactions → the exact CSV pipeline (202)."""
        from unittest.mock import MagicMock

        from backend.api.v1.recap import get_b2
        from backend.main import app
        from tests.conftest import SYNTHETIC_TRANSACTIONS
        from tests.integration.test_api_recap import (
            _setup_media_mock,
            _setup_narrative_mock,
        )

        fake_b2 = MagicMock()
        fake_b2.upload_json.return_value = "b2://bucket/index"
        fake_b2.presigned_url.return_value = "https://f000.backblazeb2.com/a?t=1"
        app.dependency_overrides[get_b2] = lambda: fake_b2

        with (
            patch("backend.api.v1.plaid.PlaidConnector") as MockConnector,
            patch("backend.api.v1.recap.NarrativeAgent") as MockNarrative,
            patch("backend.api.v1.recap.MediaAgent") as MockMedia,
        ):
            instance = MockConnector.return_value
            instance.exchange_public_token = AsyncMock(return_value="access-token")
            instance.fetch_transactions = AsyncMock(
                return_value=SYNTHETIC_TRANSACTIONS
            )
            _setup_narrative_mock(MockNarrative)
            _setup_media_mock(MockMedia)

            resp = plaid_api_client.post(
                "/api/v1/plaid/exchange", json={"public_token": "public-sandbox-x"}
            )

        assert resp.status_code == 202
        session_id = resp.json()["session_id"]
        # The background pipeline ran to completion off the Plaid transactions
        get_resp = plaid_api_client.get(f"/api/v1/recap/{session_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["insights"]["personality"].startswith("Financial")
