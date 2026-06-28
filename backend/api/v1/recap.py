"""
POST /api/v1/recap/generate  — accepts upload, starts pipeline as background task, returns 202
GET  /api/v1/recap/{session_id}  — fetch completed recap (used by share page + frontend after SSE complete)
GET  /api/v1/recap/{session_id}/download  — stream ZIP of all B2 artifacts
"""

from __future__ import annotations

import io
import os
import uuid
import zipfile
from pathlib import Path
from typing import Annotated

import structlog
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Header,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.agents.analytics_agent import AnalyticsAgent
from backend.agents.document_agent import DocumentAgent, DocumentAgentInput
from backend.agents.media_agent import MediaAgent, MediaAgentInput
from backend.agents.narrative_agent import NarrativeAgent
from backend.api.limiter import limiter
from backend.config import Settings, get_settings
from backend.media.genblaze_client import GenblazeClient
from backend.storage.b2_client import B2Client
from backend.storage.session_store import SessionStore

_BINARY_MAGIC = [
    b"\x89PNG",
    b"\xff\xd8\xff",
    b"GIF8",
    b"PK\x03\x04",
    b"%PDF",
]

log = structlog.get_logger()
router = APIRouter()

MAX_CSV_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

_session_store = SessionStore()


def get_session_store() -> SessionStore:
    return _session_store


# ── Response schemas ──────────────────────────────────────────────────────────


class AcceptedResponse(BaseModel):
    session_id: str


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
    thumbnail_url: str = ""
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
        b2_bucket=settings.b2_bucket_name,
        b2_endpoint=settings.b2_endpoint_url,
        b2_key_id=settings.b2_key_id,
        b2_app_key=settings.b2_application_key,
        openai_api_key=settings.openai_api_key,
    )


# ── Background pipeline ───────────────────────────────────────────────────────


async def _run_pipeline(
    session_id: str,
    user_id: str,
    csv_bytes: bytes,
    safe_filename: str,
    settings: Settings,
    b2: B2Client,
    genblaze: GenblazeClient,
    store: SessionStore,
) -> None:
    """Full 4-agent pipeline — runs as a background task after 202 is returned."""
    try:
        store.append_event(session_id, "parsing", f"Parsing {safe_filename}")
        doc_agent = DocumentAgent()
        doc_output = await doc_agent(
            DocumentAgentInput(
                csv_bytes=csv_bytes,
                filename=safe_filename,
            )
        )

        store.append_event(session_id, "analyzing", "Calculating insights")
        analytics_agent = AnalyticsAgent()
        analytics_output = await analytics_agent(doc_output)

        store.append_event(session_id, "scripting", "Writing narrative script")
        narrative_agent = NarrativeAgent(settings)
        narrative_output = await narrative_agent(analytics_output)

        store.append_event(session_id, "generating_images", "Generating scene images + narration")

        def _on_media_progress(event: str, detail: str) -> None:
            store.append_event(session_id, event, detail)

        media_agent = MediaAgent(settings, genblaze, b2, progress_callback=_on_media_progress)
        media_output = await media_agent(
            MediaAgentInput(
                script_output=narrative_output,
                analytics_output=analytics_output,
                session_id=session_id,
                user_id=user_id,
                csv_bytes=csv_bytes,
                input_hash=doc_output.input_hash,
                input_filename=safe_filename,
            )
        )

        store.append_event(session_id, "uploading", "Uploading to Backblaze B2")
        insights = analytics_output.insights
        insights_summary = InsightsSummary(
            period_label=insights.period_label,
            total_income=insights.total_income,
            total_expenses=insights.total_expenses,
            savings_amount=insights.savings_amount,
            savings_rate=insights.savings_rate,
            top_categories=[
                CategorySpendResponse(**c.model_dump()) for c in insights.top_categories
            ],
            achievements=insights.achievements,
            personality=insights.personality.value,
            personality_reason=insights.personality_reason,
            currency=insights.currency,
        )
        store.set_complete(
            session_id,
            output_url=media_output.video_url,
            metadata={
                "b2_keys": media_output.b2_keys,
                "insights": insights_summary.model_dump(),
                "processing_time_ms": media_output.metadata.processing_time_ms,
                "thumbnail_url": media_output.thumbnail_url,
            },
        )

        log.info(
            "recap.generate.complete",
            session_id=session_id,
            personality=insights.personality.value,
            ms=media_output.metadata.processing_time_ms,
            artifacts=len(media_output.b2_keys),
        )

    except Exception as exc:
        store.set_failed(session_id, str(exc))
        log.error("recap.generate.failed", session_id=session_id, error=str(exc), exc_info=True)


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/generate", response_model=AcceptedResponse, status_code=202)
@limiter.limit("5/hour")
async def generate_recap(
    request: Request,
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File(description="CSV transaction export")],
    settings: Settings = Depends(get_settings),
    b2: B2Client = Depends(get_b2),
    genblaze: GenblazeClient = Depends(get_genblaze),
    store: SessionStore = Depends(get_session_store),
    x_session_id: str | None = Header(None),
) -> AcceptedResponse:
    """
    Validate the CSV and start the 4-agent pipeline as a background task.
    Returns 202 Accepted immediately with the session_id.
    Progress is streamed via GET /api/v1/recap/{session_id}/progress (SSE).
    The completed recap is available at GET /api/v1/recap/{session_id}.
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=422, detail="File must be a .csv")
    safe_filename = os.path.basename(file.filename)

    csv_bytes = await file.read()
    if len(csv_bytes) == 0:
        raise HTTPException(status_code=422, detail="Uploaded file is empty")
    if len(csv_bytes) > MAX_CSV_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 5 MB limit")
    if any(csv_bytes.startswith(magic) for magic in _BINARY_MAGIC):
        raise HTTPException(status_code=422, detail="File does not appear to be a CSV")

    session_id = x_session_id or str(uuid.uuid4())
    user_id = str(uuid.uuid4())

    store.create(session_id, user_id)
    store.set_processing(session_id)

    log.info("recap.generate.start", session_id=session_id, filename=safe_filename)

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


@router.get("/{session_id}", response_model=RecapResponse)
async def get_recap(
    session_id: str,
    store: SessionStore = Depends(get_session_store),
) -> RecapResponse:
    """Fetch a completed recap by session ID — used by the share page and frontend."""
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Recap not found")
    if session["status"] != "complete":
        raise HTTPException(status_code=404, detail="Recap not ready")
    meta = session["metadata"]
    try:
        insights = InsightsSummary(**meta["insights"])
    except (KeyError, TypeError):
        raise HTTPException(status_code=404, detail="Recap data unavailable") from None
    return RecapResponse(
        session_id=session_id,
        video_url=session["output_url"],
        thumbnail_url=meta.get("thumbnail_url", ""),
        b2_keys=meta.get("b2_keys", {}),
        insights=insights,
        processing_time_ms=meta.get("processing_time_ms", 0),
    )


@router.get("/{session_id}/download")
async def download_recap_zip(
    session_id: str,
    store: SessionStore = Depends(get_session_store),
    b2: B2Client = Depends(get_b2),
) -> StreamingResponse:
    """Download all recap artifacts as a ZIP package."""
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Recap not found")
    if session["status"] != "complete":
        raise HTTPException(status_code=404, detail="Recap not ready yet")

    b2_keys: dict[str, str] = session["metadata"].get("b2_keys", {})
    if not b2_keys:
        raise HTTPException(status_code=404, detail="No artifacts found")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for artifact_name, b2_key in b2_keys.items():
            try:
                data = b2.download_bytes(b2_key)
                ext = Path(b2_key).suffix or ".bin"
                zf.writestr(f"{artifact_name}{ext}", data)
            except Exception:
                log.warning("download_zip.skip", artifact=artifact_name, key=b2_key)

    zip_buffer.seek(0)
    short_id = session_id[:8]

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="recap-{short_id}.zip"',
        },
    )
