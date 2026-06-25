from enum import StrEnum

from pydantic import BaseModel


class FinancialPersonality(StrEnum):
    BUILDER = "Financial Builder"
    OPTIMIZER = "Financial Optimizer"
    EXPLORER = "Financial Explorer"
    ACHIEVER = "Financial Achiever"


class CategorySpend(BaseModel):
    category: str
    amount: float
    percentage: float


class FinancialInsights(BaseModel):
    period_label: str  # e.g. "January 2026"

    # Core metrics
    total_income: float
    total_expenses: float
    savings_amount: float
    savings_rate: float  # percentage 0-100

    # Spending breakdown
    top_categories: list[CategorySpend]

    # Achievements
    achievements: list[str]

    # Personality
    personality: FinancialPersonality
    personality_reason: str

    # Currency (dominant)
    currency: str = "USD"
