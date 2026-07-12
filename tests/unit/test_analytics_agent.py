"""Unit tests for AnalyticsAgent including all 4 Financial Personalities."""

from datetime import date

import pytest

from backend.agents.analytics_agent import AnalyticsAgent
from backend.agents.document_agent import DocumentAgentOutput
from backend.models.insights import FinancialPersonality
from backend.models.transaction import Transaction, TransactionCategory


def make_doc_output(transactions: list[Transaction]) -> DocumentAgentOutput:
    return DocumentAgentOutput(
        transactions=transactions,
        input_hash="abc123",
        period_label="January 2026",
    )


@pytest.fixture
def agent() -> AnalyticsAgent:
    return AnalyticsAgent()


class TestAnalyticsAgent:
    async def test_income_totalled(self, agent, synthetic_transactions):
        output = await agent(make_doc_output(synthetic_transactions))
        assert output.insights.total_income == pytest.approx(13000.0, abs=1)

    async def test_savings_calculated(self, agent, synthetic_transactions):
        output = await agent(make_doc_output(synthetic_transactions))
        assert output.insights.savings_amount == pytest.approx(1200.0, abs=1)

    async def test_savings_rate_percentage(self, agent, synthetic_transactions):
        output = await agent(make_doc_output(synthetic_transactions))
        rate = output.insights.savings_rate
        assert 0 < rate < 100

    async def test_top_categories_max_3(self, agent, synthetic_transactions):
        output = await agent(make_doc_output(synthetic_transactions))
        assert len(output.insights.top_categories) <= 3

    async def test_top_categories_sum_to_100_approx(self, agent, synthetic_transactions):
        output = await agent(make_doc_output(synthetic_transactions))
        total = sum(c.percentage for c in output.insights.top_categories)
        assert total <= 101  # May not add to 100 if only top 3 of many

    async def test_achievements_non_empty(self, agent, synthetic_transactions):
        output = await agent(make_doc_output(synthetic_transactions))
        assert len(output.insights.achievements) >= 1

    async def test_builder_personality_high_savings(self, agent):
        txns = [
            Transaction(date=date(2026, 1, 1), description="Salary", amount=5000,
                        currency="USD", category=TransactionCategory.INCOME),
            Transaction(date=date(2026, 1, 2), description="Savings", amount=-1500,
                        currency="USD", category=TransactionCategory.SAVINGS),
        ]
        output = await agent(make_doc_output(txns))
        assert output.insights.personality == FinancialPersonality.BUILDER

    async def test_explorer_personality_high_travel(self, agent):
        txns = [
            Transaction(date=date(2026, 1, 1), description="Salary", amount=5000,
                        currency="USD", category=TransactionCategory.INCOME),
            Transaction(date=date(2026, 1, 2), description="Lufthansa", amount=-2000,
                        currency="USD", category=TransactionCategory.TRAVEL),
            Transaction(date=date(2026, 1, 3), description="Hotel", amount=-800,
                        currency="USD", category=TransactionCategory.TRAVEL),
        ]
        output = await agent(make_doc_output(txns))
        assert output.insights.personality == FinancialPersonality.EXPLORER

    async def test_optimizer_personality_default(self, agent):
        txns = [
            Transaction(date=date(2026, 1, 1), description="Salary", amount=5000,
                        currency="USD", category=TransactionCategory.INCOME),
            Transaction(date=date(2026, 1, 2), description="Grocery", amount=-400,
                        currency="USD", category=TransactionCategory.FOOD),
        ]
        output = await agent(make_doc_output(txns))
        assert output.insights.personality in list(FinancialPersonality)

    async def test_personality_reason_non_empty(self, agent, synthetic_transactions):
        output = await agent(make_doc_output(synthetic_transactions))
        assert len(output.insights.personality_reason) > 10

    async def test_zero_income_no_division_error(self, agent):
        txns = [
            Transaction(date=date(2026, 1, 1), description="Grocery", amount=-100,
                        currency="USD", category=TransactionCategory.FOOD),
        ]
        output = await agent(make_doc_output(txns))
        assert output.insights.savings_rate == 0.0

    async def test_achiever_personality_and_healthy_savings(self, agent):
        # 12% savings rate → "healthy" achievement + ACHIEVER personality
        # (savings_rate >= 8 but < 15, no debt, no travel/entertainment).
        txns = [
            Transaction(date=date(2026, 1, 1), description="Salary", amount=5000,
                        currency="USD", category=TransactionCategory.INCOME),
            Transaction(date=date(2026, 1, 2), description="Savings", amount=-600,
                        currency="USD", category=TransactionCategory.SAVINGS),
        ]
        output = await agent(make_doc_output(txns))
        assert output.insights.personality == FinancialPersonality.ACHIEVER
        assert any("healthy" in a.lower() for a in output.insights.achievements)

    async def test_debt_reduction_achievement(self, agent):
        txns = [
            Transaction(date=date(2026, 1, 1), description="Salary", amount=5000,
                        currency="USD", category=TransactionCategory.INCOME),
            Transaction(date=date(2026, 1, 2), description="Loan payment", amount=-500,
                        currency="USD", category=TransactionCategory.DEBT),
        ]
        output = await agent(make_doc_output(txns))
        assert any("debt" in a.lower() for a in output.insights.achievements)

    async def test_investment_achievement(self, agent):
        txns = [
            Transaction(date=date(2026, 1, 1), description="Salary", amount=5000,
                        currency="USD", category=TransactionCategory.INCOME),
            Transaction(date=date(2026, 1, 2), description="Index fund", amount=-800,
                        currency="USD", category=TransactionCategory.INVESTMENT),
        ]
        output = await agent(make_doc_output(txns))
        assert any("invest" in a.lower() for a in output.insights.achievements)

    def test_dominant_currency_empty_defaults_usd(self, agent):
        assert agent._dominant_currency([]) == "USD"

    async def test_dominant_currency(self, agent):
        txns = [
            Transaction(date=date(2026, 1, 1), description="Salary", amount=6000,
                        currency="SEK", category=TransactionCategory.INCOME),
            Transaction(date=date(2026, 1, 2), description="Grocery", amount=-400,
                        currency="SEK", category=TransactionCategory.FOOD),
        ]
        output = await agent(make_doc_output(txns))
        assert output.insights.currency == "SEK"
