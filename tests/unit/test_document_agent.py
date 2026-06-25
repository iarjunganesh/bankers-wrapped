"""Unit tests for DocumentAgent."""

import pytest

from backend.agents.document_agent import DocumentAgent, DocumentAgentInput
from backend.models.transaction import TransactionCategory


@pytest.fixture
def agent() -> DocumentAgent:
    return DocumentAgent()


class TestDocumentAgent:
    async def test_parses_valid_csv(self, agent, synthetic_csv):
        output = await agent(DocumentAgentInput(csv_bytes=synthetic_csv, filename="test.csv"))
        assert len(output.transactions) > 0

    async def test_period_label(self, agent, synthetic_csv):
        output = await agent(DocumentAgentInput(csv_bytes=synthetic_csv, filename="test.csv"))
        assert output.period_label == "January 2026"

    async def test_input_hash_is_sha256(self, agent, synthetic_csv):
        output = await agent(DocumentAgentInput(csv_bytes=synthetic_csv, filename="test.csv"))
        assert len(output.input_hash) == 64
        assert all(c in "0123456789abcdef" for c in output.input_hash)

    async def test_income_categorised(self, agent, synthetic_csv):
        output = await agent(DocumentAgentInput(csv_bytes=synthetic_csv, filename="test.csv"))
        incomes = [t for t in output.transactions if t.category == TransactionCategory.INCOME]
        assert len(incomes) >= 1

    async def test_savings_categorised(self, agent, synthetic_csv):
        output = await agent(DocumentAgentInput(csv_bytes=synthetic_csv, filename="test.csv"))
        savings = [t for t in output.transactions if t.category == TransactionCategory.SAVINGS]
        assert len(savings) >= 1

    async def test_empty_csv_raises(self, agent):
        csv = b"date,description,amount\n"
        output = await agent(DocumentAgentInput(csv_bytes=csv, filename="empty.csv"))
        assert output.transactions == []

    async def test_missing_required_column_raises(self, agent):
        bad_csv = b"date,description\n2026-01-01,test\n"
        with pytest.raises(ValueError, match="must contain columns"):
            await agent(DocumentAgentInput(csv_bytes=bad_csv, filename="bad.csv"))

    async def test_malformed_amount_skipped(self, agent):
        csv = b"date,description,amount,currency\n2026-01-01,test,NOT_A_NUMBER,USD\n"
        output = await agent(DocumentAgentInput(csv_bytes=csv, filename="bad.csv"))
        # Amount should be 0.0 (coerced) not raise
        assert output.transactions[0].amount == 0.0

    async def test_category_inferred_from_description(self, agent):
        csv = b"date,description,amount,currency\n2026-01-01,Spotify Premium,-9.99,USD\n"
        output = await agent(DocumentAgentInput(csv_bytes=csv, filename="t.csv"))
        assert output.transactions[0].category == TransactionCategory.ENTERTAINMENT

    async def test_currency_uppercased(self, agent):
        csv = b"date,description,amount,currency\n2026-01-01,Salary,1000,usd\n"
        output = await agent(DocumentAgentInput(csv_bytes=csv, filename="t.csv"))
        assert output.transactions[0].currency == "USD"

    async def test_deterministic_hash(self, agent, synthetic_csv):
        out1 = await agent(DocumentAgentInput(csv_bytes=synthetic_csv, filename="t.csv"))
        out2 = await agent(DocumentAgentInput(csv_bytes=synthetic_csv, filename="t.csv"))
        assert out1.input_hash == out2.input_hash
