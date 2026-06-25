"""
Document Intelligence Agent.

Parses and normalises uploaded CSV transaction data into structured
Transaction records. MVP: CSV only. PDF is a future roadmap item.
"""

from dataclasses import dataclass
import hashlib
import io

import pandas as pd

from backend.agents.base import BaseAgent
from backend.models.transaction import Transaction, TransactionCategory


CATEGORY_KEYWORDS: dict[str, list[str]] = {
    TransactionCategory.INCOME: ["salary", "payroll", "wage", "deposit", "refund", "bonus"],
    TransactionCategory.SAVINGS: ["savings", "save", "transfer to savings", "isk"],
    TransactionCategory.HOUSING: ["rent", "mortgage", "bolån", "hyra", "insurance home"],
    TransactionCategory.FOOD: ["grocery", "supermarket", "ica", "coop", "lidl", "restaurant",
                                "cafe", "coffee", "food", "pizza", "sushi", "lunch"],
    TransactionCategory.TRAVEL: ["airline", "lufthansa", "sas", "ryanair", "hotel",
                                  "airbnb", "uber", "taxi", "train", "tåg", "flight"],
    TransactionCategory.ENTERTAINMENT: ["spotify", "netflix", "hbo", "cinema", "concert",
                                         "steam", "playstation", "game", "streaming"],
    TransactionCategory.UTILITIES: ["electric", "electricity", "water", "internet",
                                     "phone", "mobile", "broadband", "vattenfall", "telia"],
    TransactionCategory.INVESTMENT: ["investment", "stock", "fund", "avanza", "nordnet",
                                      "etf", "crypto", "dividend"],
    TransactionCategory.DEBT: ["loan repayment", "credit card", "installment", "amortering"],
}


def _infer_category(description: str) -> TransactionCategory:
    desc_lower = description.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in desc_lower for kw in keywords):
            return TransactionCategory(category)
    return TransactionCategory.OTHER


@dataclass
class DocumentAgentInput:
    csv_bytes: bytes
    filename: str


@dataclass
class DocumentAgentOutput:
    transactions: list[Transaction]
    input_hash: str
    period_label: str


class DocumentAgent(BaseAgent):
    """Parses CSV transaction data and returns normalised Transaction records."""

    def __init__(self) -> None:
        super().__init__("DocumentAgent")

    async def run(self, input_data: DocumentAgentInput) -> DocumentAgentOutput:
        csv_text = input_data.csv_bytes.decode("utf-8", errors="replace")
        input_hash = hashlib.sha256(input_data.csv_bytes).hexdigest()

        df = self._parse_csv(csv_text)
        transactions = self._to_transactions(df)
        period_label = self._infer_period(transactions)

        self.log.info("document_agent.parsed", count=len(transactions), period=period_label)

        return DocumentAgentOutput(
            transactions=transactions,
            input_hash=input_hash,
            period_label=period_label,
        )

    def _parse_csv(self, csv_text: str) -> pd.DataFrame:
        df = pd.read_csv(io.StringIO(csv_text))

        # Normalise column names: lowercase + strip spaces
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        required = {"date", "description", "amount"}
        if not required.issubset(set(df.columns)):
            raise ValueError(
                f"CSV must contain columns: {required}. Got: {set(df.columns)}"
            )

        df["date"] = pd.to_datetime(df["date"]).dt.date
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
        df["description"] = df["description"].fillna("").astype(str).str.strip()
        df["currency"] = df.get("currency", pd.Series(["USD"] * len(df))).fillna("USD").str.upper()

        return df

    def _to_transactions(self, df: pd.DataFrame) -> list[Transaction]:
        transactions = []
        for _, row in df.iterrows():
            # Use provided category if valid, otherwise infer
            if "category" in df.columns and pd.notna(row.get("category")):
                try:
                    category = TransactionCategory(str(row["category"]).lower())
                except ValueError:
                    category = _infer_category(row["description"])
            else:
                category = _infer_category(row["description"])

            transactions.append(
                Transaction(
                    date=row["date"],
                    description=row["description"],
                    amount=float(row["amount"]),
                    currency=str(row["currency"]),
                    category=category,
                )
            )
        return transactions

    def _infer_period(self, transactions: list[Transaction]) -> str:
        if not transactions:
            return "Unknown Period"
        dates = [t.date for t in transactions]
        earliest = min(dates)
        return earliest.strftime("%B %Y")
