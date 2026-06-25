"""
POST /api/v1/recap/generate

Accepts a CSV upload, runs the full 4-agent pipeline, and returns
the presigned B2 URL for the generated recap video.
"""

from __future__ import annotations

import os
import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from backend.agents.analytics_agent import AnalyticsAgent
from backend.agents.document_agent import DocumentAgent, DocumentAgentInput
from backend.agents.media_agent import MediaAgent, MediaAgentInput
from backend.agents.narrative_agent import NarrativeAgent
from backend.config import Settings, get_settings
from backend.media.genblaze_client import GenblazeClient
from backend.storage.b2_client import B2Client
from backend.storage.session_store import SessionStore

log = structlog.get_logger()
router = APIRouter()

MAX_CSV_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

_session_store = SessionStore()


def get_session_store() -> SessionStore:
    return _session_store


# ── Response schemas ──────────────────────────────────────────────────────────

class CategorySpendResponse(BaseModel):
    category: str
    amount: float
    percentage: float


class InsightsSummary(BaseModel):
    period_label: str
    total_income: float
    total_expenses: float
    savings_amount: float
    savings_rate: float
    top_categories: list[CategorySpendResponse]
    achievements: list[str]
    personality: str
    personality_reason: str
    currency: str


class RecapResponse(BaseModel):
    session_id: str
    video_url: str
    insights: InsightsSummary
    processing_time_ms: int
    b2_keys: dict[str, str]


# ── Dependencies ──────────────────────────────────────────────────────────────

def get_b2(settings: Settings = Depends(get_settings)) -> B2Client:
    return B2Client(
        endpoint_url=settings.b2_endpoint_url,
        key_id=settings.b2_key_id,
        application_key=settings.b2_application_key,
        bucket_name=settings.b2_bucket_name,
        presigned_url_expiry=settings.b2_presigned_url_expiry,
    )


def get_genblaze(settings: Settings = Depends(get_settings)) -> GenblazeClient:
    return GenblazeClient(
        gmi_api_key=settings.gmi_api_key,
        elevenlabs_api_key=settings.elevenlabs_api_key,
        b2_bucket=settings.b2_bucket_name,
        b2_endpoint=settings.b2_endpoint_url,
        b2_key_id=settings.b2_key_id,
        b2_app_key=settings.b2_application_key,
    )


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/generate", response_model=RecapResponse)
async def generate_recap(
    file: Annotated[UploadFile, File(description="CSV transaction export")],
    settings: Settings = Depends(get_settings),
    b2: B2Client = Depends(get_b2),
    genblaze: GenblazeClient = Depends(get_genblaze),
    store: SessionStore = Depends(get_session_store),
) -> RecapResponse:
    """
    Run the full Banker's Wrapped pipeline:
      Document Agent → Analytics Agent → Narrative Agent → Media Agent

    Returns the presigned Backblaze B2 URL for the generated recap.mp4.
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=422, detail="File must be a .csv")
    safe_filename = os.path.basename(file.filename)

    csv_bytes = await file.read()
    if len(csv_bytes) == 0:
        raise HTTPException(status_code=422, detail="Uploaded file is empty")
    if len(csv_bytes) > MAX_CSV_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 5 MB limit")

    session_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())  # Anonymous user — no auth required for MVP

    store.create(session_id, user_id)
    store.set_processing(session_id)

    log.info("recap.generate.start", session_id=session_id, filename=safe_filename)

    try:
        # ── Agent 1: Document Intelligence ───────────────────────────────────
        doc_agent = DocumentAgent()
        doc_output = await doc_agent(DocumentAgentInput(
            csv_bytes=csv_bytes,
            filename=safe_filename,
        ))

        # ── Agent 2: Financial Analytics + Personality ───────────────────────
        analytics_agent = AnalyticsAgent()
        analytics_output = await analytics_agent(doc_output)

        # ── Agent 3: Narrative Generation ────────────────────────────────────
        narrative_agent = NarrativeAgent(settings)
        narrative_output = await narrative_agent(analytics_output)

        # ── Agent 4: Media (Voice + Images + FFmpeg + B2) ────────────────────
        media_agent = MediaAgent(settings, genblaze, b2)
        media_output = await media_agent(MediaAgentInput(
            script_output=narrative_output,
            session_id=session_id,
            user_id=user_id,
            csv_bytes=csv_bytes,
            input_hash=doc_output.input_hash,
            input_filename=safe_filename,
        ))

        # ── Persist session ──────────────────────────────────────────────────
        store.set_complete(
            session_id,
            output_url=media_output.video_url,
            metadata={"b2_keys": media_output.b2_keys},
        )

        insights = analytics_output.insights
        response = RecapResponse(
            session_id=session_id,
            video_url=media_output.video_url,
            b2_keys=media_output.b2_keys,
            insights=InsightsSummary(
                period_label=insights.period_label,
                total_income=insights.total_income,
                total_expenses=insights.total_expenses,
                savings_amount=insights.savings_amount,
                savings_rate=insights.savings_rate,
                top_categories=[
                    CategorySpendResponse(**c.model_dump())
                    for c in insights.top_categories
                ],
                achievements=insights.achievements,
                personality=insights.personality.value,
                personality_reason=insights.personality_reason,
                currency=insights.currency,
            ),
            processing_time_ms=media_output.metadata.processing_time_ms,
        )

        log.info(
            "recap.generate.complete",
            session_id=session_id,
            personality=insights.personality.value,
            ms=media_output.metadata.processing_time_ms,
        )

        return response

    except Exception as exc:
        store.set_failed(session_id, str(exc))
        log.error("recap.generate.failed", session_id=session_id, error=str(exc), exc_info=True)
        raise HTTPException(status_code=500, detail="Pipeline processing failed. Please try again.") from exc
