from datetime import date
from enum import StrEnum

from pydantic import BaseModel, field_validator


class TransactionCategory(StrEnum):
    INCOME = "income"
    SAVINGS = "savings"
    HOUSING = "housing"
    FOOD = "food"
    TRAVEL = "travel"
    ENTERTAINMENT = "entertainment"
    UTILITIES = "utilities"
    INVESTMENT = "investment"
    DEBT = "debt"
    OTHER = "other"


class Transaction(BaseModel):
    date: date
    description: str
    amount: float  # positive = income/credit, negative = expense/debit
    currency: str = "USD"
    category: TransactionCategory = TransactionCategory.OTHER

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, v: str) -> str:
        return v.upper()

    @property
    def is_expense(self) -> bool:
        return self.amount < 0

    @property
    def is_income(self) -> bool:
        return self.amount > 0

    @property
    def abs_amount(self) -> float:
        return abs(self.amount)
