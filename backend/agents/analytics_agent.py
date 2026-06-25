"""
Financial Analytics Agent + Financial Personality Generator.

Derives insights from normalised transactions and assigns one of four
Financial Personality labels: Builder, Optimizer, Explorer, Achiever.
The personality is the emotional centrepiece of the recap video.
"""

from collections import defaultdict
from dataclasses import dataclass

from backend.agents.base import BaseAgent
from backend.agents.document_agent import DocumentAgentOutput
from backend.models.insights import CategorySpend, FinancialInsights, FinancialPersonality
from backend.models.transaction import Transaction, TransactionCategory


@dataclass
class AnalyticsAgentOutput:
    insights: FinancialInsights


class AnalyticsAgent(BaseAgent):
    """Analyses transactions and classifies the user's Financial Personality."""

    def __init__(self) -> None:
        super().__init__("AnalyticsAgent")

    async def run(self, input_data: DocumentAgentOutput) -> AnalyticsAgentOutput:
        transactions = input_data.transactions
        period_label = input_data.period_label

        income = self._sum_by_filter(transactions, lambda t: t.is_income)
        expenses = self._sum_by_filter(transactions, lambda t: t.is_expense)
        savings = self._savings_amount(transactions)
        savings_rate = (savings / income * 100) if income > 0 else 0.0

        category_totals = self._category_totals(transactions)
        top_categories = self._top_categories(category_totals, expenses)
        achievements = self._detect_achievements(savings_rate, transactions)
        personality, reason = self._classify_personality(
            savings_rate, top_categories, achievements
        )
        currency = self._dominant_currency(transactions)

        insights = FinancialInsights(
            period_label=period_label,
            total_income=round(income, 2),
            total_expenses=round(abs(expenses), 2),
            savings_amount=round(savings, 2),
            savings_rate=round(savings_rate, 1),
            top_categories=top_categories,
            achievements=achievements,
            personality=personality,
            personality_reason=reason,
            currency=currency,
        )

        self.log.info(
            "analytics_agent.complete",
            income=income,
            savings_rate=savings_rate,
            personality=personality.value,
        )

        return AnalyticsAgentOutput(insights=insights)

    def _sum_by_filter(
        self, transactions: list[Transaction], fn: object
    ) -> float:
        return sum(t.amount for t in transactions if fn(t))  # type: ignore[operator]

    def _savings_amount(self, transactions: list[Transaction]) -> float:
        return sum(
            t.abs_amount
            for t in transactions
            if t.category == TransactionCategory.SAVINGS and t.amount < 0
        )

    def _category_totals(
        self, transactions: list[Transaction]
    ) -> dict[str, float]:
        totals: dict[str, float] = defaultdict(float)
        for t in transactions:
            if t.is_expense:
                totals[t.category.value] += t.abs_amount
        return totals

    def _top_categories(
        self, totals: dict[str, float], total_expenses: float
    ) -> list[CategorySpend]:
        total_abs = abs(total_expenses) or 1.0
        sorted_cats = sorted(totals.items(), key=lambda x: x[1], reverse=True)[:3]
        return [
            CategorySpend(
                category=cat,
                amount=round(amount, 2),
                percentage=round(amount / total_abs * 100, 1),
            )
            for cat, amount in sorted_cats
        ]

    def _detect_achievements(
        self, savings_rate: float, transactions: list[Transaction]
    ) -> list[str]:
        achievements = []
        if savings_rate >= 20:
            achievements.append(f"Saved {savings_rate:.0f}% of income — well above average")
        elif savings_rate >= 10:
            achievements.append(f"Maintained a healthy {savings_rate:.0f}% savings rate")

        debt_payments = sum(
            t.abs_amount
            for t in transactions
            if t.category == TransactionCategory.DEBT
        )
        if debt_payments > 0:
            achievements.append(f"Reduced debt by {debt_payments:,.0f}")

        investment = sum(
            t.abs_amount
            for t in transactions
            if t.category == TransactionCategory.INVESTMENT
        )
        if investment > 0:
            achievements.append(f"Invested {investment:,.0f} toward your future")

        if not achievements:
            achievements.append("Tracked your spending consistently this period")

        return achievements

    def _classify_personality(
        self,
        savings_rate: float,
        top_categories: list[CategorySpend],
        achievements: list[str],
    ) -> tuple[FinancialPersonality, str]:
        top_cat_names = [c.category for c in top_categories]
        has_debt_achievement = any("debt" in a.lower() for a in achievements)
        has_investment = any("invest" in a.lower() for a in achievements)

        if savings_rate >= 15 or has_debt_achievement:
            return (
                FinancialPersonality.BUILDER,
                "You consistently prioritise savings and debt reduction — building a strong financial foundation.",
            )

        if "travel" in top_cat_names or "entertainment" in top_cat_names:
            return (
                FinancialPersonality.EXPLORER,
                "You invest in experiences and adventures — living richly while keeping finances in check.",
            )

        if has_investment or savings_rate >= 8:
            return (
                FinancialPersonality.ACHIEVER,
                "You hit meaningful financial milestones this period — your discipline is paying off.",
            )

        return (
            FinancialPersonality.OPTIMIZER,
            "You keep discretionary spend lean and your budget efficient — every transaction has a purpose.",
        )

    def _dominant_currency(self, transactions: list[Transaction]) -> str:
        if not transactions:
            return "USD"
        from collections import Counter
        counts = Counter(t.currency for t in transactions)
        return counts.most_common(1)[0][0]
