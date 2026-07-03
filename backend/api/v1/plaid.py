"""
Plaid sandbox ingestion endpoints (ADR-010) — mounted always, active only
when PLAID_CLIENT_ID + PLAID_SECRET are configured (404 otherwise, so the
app runs identically with no keys).

POST /api/v1/plaid/link-token — mint a Plaid Link token for the frontend
POST /api/v1/plaid/exchange   — public_token → transactions → same pipeline
                                 as the CSV upload (reuses _run_pipeline)
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from pydantic import BaseModel

from backend.api.limiter import limiter
from backend.api.v1.recap import (
    AcceptedResponse,
    _run_pipeline,
    get_b2,
    get_genblaze,
    get_session_store,
)
from backend.config import Settings, get_settings
from backend.ingest.plaid_connector import PlaidConnector, transactions_to_csv
from backend.media.genblaze_client import GenblazeClient
from backend.storage.b2_client import B2Client
from backend.storage.session_store import SessionStore

log = structlog.get_logger()
router = APIRouter()

# How far back to pull sandbox transactions for the recap window.
TRANSACTION_WINDOW_DAYS = 30


class LinkTokenResponse(BaseModel):
    link_token: str


class ExchangeRequest(BaseModel):
    public_token: str


def _require_plaid(settings: Settings) -> None:
    if not settings.plaid_enabled:
        raise HTTPException(status_code=404, detail="Plaid ingestion is not enabled")


@router.post("/link-token", response_model=LinkTokenResponse)
async def create_link_token(
    settings: Settings = Depends(get_settings),
) -> LinkTokenResponse:
    """Mint a Plaid Link token the frontend uses to open the Link dialog."""
    _require_plaid(settings)
    connector = PlaidConnector(settings)
    token = await connector.create_link_token(user_id=str(uuid.uuid4()))
    return LinkTokenResponse(link_token=token)


@router.post("/exchange", response_model=AcceptedResponse, status_code=202)
@limiter.limit("5/hour")
async def exchange_and_generate(
    request: Request,
    body: ExchangeRequest,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings),
    b2: B2Client = Depends(get_b2),
    genblaze: GenblazeClient = Depends(get_genblaze),
    store: SessionStore = Depends(get_session_store),
    x_session_id: str | None = Header(None),
) -> AcceptedResponse:
    """
    Exchange the Link public_token, pull sandbox transactions, and start the
    exact same 4-agent pipeline as the CSV path (202 + SSE progress).
    """
    _require_plaid(settings)
    connector = PlaidConnector(settings)

    access_token = await connector.exchange_public_token(body.public_token)
    end = date.today()
    start = end - timedelta(days=TRANSACTION_WINDOW_DAYS)
    transactions = await connector.fetch_transactions(access_token, start, end)
    if not transactions:
        raise HTTPException(
            status_code=422, detail="No transactions found in the linked account"
        )

    # Serialise to our CSV schema and reuse the pipeline unchanged — the full
    # B2 artifact trail (input/transactions.csv included) stays identical.
    csv_bytes = transactions_to_csv(transactions)
    safe_filename = "plaid_sandbox.csv"

    session_id = x_session_id or str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    store.create(session_id, user_id)
    store.set_processing(session_id)

    log.info(
        "plaid.exchange.start", session_id=session_id, transactions=len(transactions)
    )

    background_tasks.add_task(
        _run_pipeline,
        session_id=session_id,
        user_id=user_id,
        csv_bytes=csv_bytes,
        safe_filename=safe_filename,
        settings=settings,
        b2=b2,
        genblaze=genblaze,
        store=store,
    )
    return AcceptedResponse(session_id=session_id)
