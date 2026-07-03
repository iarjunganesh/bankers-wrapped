"""
Plaid Sandbox connector (ADR-010) — optional "connect a bank" ingestion path.

Talks to the Plaid REST API directly via httpx (async, no event-loop blocking;
avoids the plaid-python dependency). Normalizes Plaid transactions into the
same `Transaction` model the CSV path produces, then serialises them back to
CSV bytes so the existing 4-agent pipeline runs completely unchanged — the
B2 artifact trail (input/transactions.csv included) stays identical.

Sign convention: Plaid reports outflows as POSITIVE amounts; ours is
income positive / expense negative, so amounts are negated on ingest.
"""

from __future__ import annotations

from datetime import date

import httpx
import structlog

from backend.config import Settings
from backend.models.transaction import Transaction, TransactionCategory

log = structlog.get_logger()

PLAID_HOSTS = {
    "sandbox": "https://sandbox.plaid.com",
    "production": "https://production.plaid.com",
}

# Plaid personal_finance_category.primary → our TransactionCategory.
# Anything unmapped falls back to OTHER.
CATEGORY_MAP: dict[str, TransactionCategory] = {
    "INCOME": TransactionCategory.INCOME,
    "TRANSFER_IN": TransactionCategory.INCOME,
    "TRANSFER_OUT": TransactionCategory.SAVINGS,
    "LOAN_PAYMENTS": TransactionCategory.DEBT,
    "RENT_AND_UTILITIES": TransactionCategory.HOUSING,
    "HOME_IMPROVEMENT": TransactionCategory.HOUSING,
    "FOOD_AND_DRINK": TransactionCategory.FOOD,
    "TRANSPORTATION": TransactionCategory.TRAVEL,
    "TRAVEL": TransactionCategory.TRAVEL,
    "ENTERTAINMENT": TransactionCategory.ENTERTAINMENT,
}

_PAGE_SIZE = 500


def map_plaid_category(primary: str | None) -> TransactionCategory:
    """Map a Plaid personal-finance primary category to our taxonomy."""
    if not primary:
        return TransactionCategory.OTHER
    return CATEGORY_MAP.get(primary.upper(), TransactionCategory.OTHER)


def normalize_plaid_transaction(txn: dict) -> Transaction:  # type: ignore[type-arg]
    """Convert one Plaid transaction dict into our Transaction model."""
    pfc = txn.get("personal_finance_category") or {}
    return Transaction(
        date=txn["date"],
        description=txn.get("merchant_name") or txn.get("name") or "Unknown",
        # Plaid: positive = money OUT; ours: positive = money IN.
        amount=-float(txn["amount"]),
        currency=txn.get("iso_currency_code") or "USD",
        category=map_plaid_category(pfc.get("primary")),
    )


def transactions_to_csv(transactions: list[Transaction]) -> bytes:
    """Serialise transactions to the exact CSV schema the upload path accepts."""
    lines = ["date,description,amount,currency,category"]
    for t in transactions:
        desc = t.description.replace('"', "'")
        if "," in desc:
            desc = f'"{desc}"'
        lines.append(
            f"{t.date.isoformat()},{desc},{t.amount:.2f},{t.currency},{t.category.value}"
        )
    return ("\n".join(lines) + "\n").encode("utf-8")


class PlaidConnector:
    """Thin async client for the three Plaid endpoints the sandbox flow needs."""

    def __init__(self, settings: Settings) -> None:
        self.base_url = PLAID_HOSTS.get(settings.plaid_env, PLAID_HOSTS["sandbox"])
        self.client_id = settings.plaid_client_id
        self.secret = settings.plaid_secret

    async def _post(self, path: str, payload: dict) -> dict:  # type: ignore[type-arg]
        body = {"client_id": self.client_id, "secret": self.secret, **payload}
        async with httpx.AsyncClient(timeout=30) as http:
            resp = await http.post(f"{self.base_url}{path}", json=body)
            resp.raise_for_status()
            data: dict = resp.json()  # type: ignore[type-arg]
            return data

    async def create_link_token(self, user_id: str) -> str:
        data = await self._post(
            "/link/token/create",
            {
                "client_name": "Banker's Wrapped",
                "user": {"client_user_id": user_id},
                "products": ["transactions"],
                "country_codes": ["US"],
                "language": "en",
            },
        )
        return str(data["link_token"])

    async def exchange_public_token(self, public_token: str) -> str:
        data = await self._post(
            "/item/public_token/exchange", {"public_token": public_token}
        )
        return str(data["access_token"])

    async def fetch_transactions(
        self, access_token: str, start_date: date, end_date: date
    ) -> list[Transaction]:
        """Fetch all transactions in the window (paginated), normalized."""
        raw: list[dict] = []  # type: ignore[type-arg]
        total = 1
        while len(raw) < total:
            data = await self._post(
                "/transactions/get",
                {
                    "access_token": access_token,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "options": {"count": _PAGE_SIZE, "offset": len(raw)},
                },
            )
            total = int(data.get("total_transactions", 0))
            page = data.get("transactions", [])
            if not page:
                break
            raw.extend(page)

        transactions = [normalize_plaid_transaction(t) for t in raw]
        log.info(
            "plaid.fetch_transactions",
            count=len(transactions),
            start=start_date.isoformat(),
            end=end_date.isoformat(),
        )
        return transactions
