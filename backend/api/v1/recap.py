"""
POST /api/v1/recap/generate  — accepts upload, starts pipeline as background task, returns 202
GET  /api/v1/recap/{session_id}  — fetch completed recap (used by share page + frontend after SSE complete)
GET  /api/v1/recap/{session_id}/download  — stream ZIP of all B2 artifacts
"""

from __future__ import annotations

import asyncio
import io
import os
import uuid
import zipfile
from datetime import UTC, datetime
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
        nvidia_nim_api_key=settings.nvidia_nim_api_key,
        nvidia_nim_base_url=settings.nvidia_nim_base_url,
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
    # ADR-008: write the flat {session_id -> user_id} index to B2 first so the
    # manifest can be located by session_id alone (share URLs carry no user_id),
    # even after the SQLite cache is wiped by a redeploy. Non-fatal: an index
    # write failure must not abort the generation (only redeploy durability is
    # affected; if B2 is truly down, MediaAgent's uploads will fail anyway).
    try:
        await asyncio.to_thread(
            b2.upload_json,
            B2Client.session_index_key(session_id),
            {
                "session_id": session_id,
                "user_id": user_id,
                "created_at": datetime.now(UTC).isoformat(),
            },
        )
    except Exception as exc:
        log.warning("recap.session_index.write_failed", session_id=session_id, error=str(exc))

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
        # genblaze passed for ADR-007 LLM routing (active when
        # NARRATIVE_PROVIDER=genblaze; otherwise the direct NIM path is used)
        narrative_agent = NarrativeAgent(settings, genblaze=genblaze)
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


# ── B2 fallback (ADR-008: B2 is the source of truth, SQLite is a cache) ──────


async def _manifest_from_b2(session_id: str, b2: B2Client) -> dict | None:  # type: ignore[type-arg]
    """
    Load the session manifest from B2 by session_id alone.

    Resolves user_id via the flat index object, then reads
    {user_id}/{session_id}/metadata/session_metadata.json. Returns None when
    the session is unknown to B2 (or the manifest isn't complete yet).
    """
    try:
        index = await asyncio.to_thread(
            b2.download_json, B2Client.session_index_key(session_id)
        )
        user_id = index["user_id"]
        manifest: dict = await asyncio.to_thread(  # type: ignore[type-arg]
            b2.download_json, B2Client.metadata_key(user_id, session_id)
        )
    except Exception:
        log.info("recap.b2_fallback.miss", session_id=session_id)
        return None
    if manifest.get("status") != "complete":
        return None
    log.info("recap.b2_fallback.hit", session_id=session_id)
    return manifest


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
    b2: B2Client = Depends(get_b2),
) -> RecapResponse:
    """Fetch a completed recap by session ID — used by the share page and frontend."""
    session = store.get(session_id)
    if session and session["status"] == "complete":
        meta = session["metadata"]  # fast path: SQLite cache
    else:
        # Cache miss (redeploy wiped SQLite, or row not complete) — fall back
        # to the durable B2 manifest, which is a superset of the cached metadata.
        manifest = await _manifest_from_b2(session_id, b2)
        if manifest is None:
            detail = "Recap not ready" if session else "Recap not found"
            raise HTTPException(status_code=404, detail=detail)
        meta = manifest
    try:
        insights = InsightsSummary(**meta["insights"])
    except (KeyError, TypeError):
        raise HTTPException(status_code=404, detail="Recap data unavailable") from None

    # Regenerate presigned URLs from the stored B2 keys on every request. The URLs
    # minted at generation time expire after b2_presigned_url_expiry (1h), which
    # would break the share page / notebook Scenario C for any recap opened later.
    b2_keys: dict[str, str] = meta.get("b2_keys", {})
    video_key = b2_keys.get("video")
    thumb_key = b2_keys.get("thumbnail")
    video_url = (
        await asyncio.to_thread(b2.presigned_url, video_key)
        if video_key
        else (session["output_url"] if session else meta.get("output_url", ""))
    )
    thumbnail_url = (
        await asyncio.to_thread(b2.presigned_url, thumb_key)
        if thumb_key else meta.get("thumbnail_url", "")
    )

    return RecapResponse(
        session_id=session_id,
        video_url=video_url,
        thumbnail_url=thumbnail_url,
        b2_keys=b2_keys,
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
    if session and session["status"] == "complete":
        b2_keys: dict[str, str] = session["metadata"].get("b2_keys", {})
    else:
        # Same B2 fallback as get_recap — ZIP download must survive a redeploy.
        manifest = await _manifest_from_b2(session_id, b2)
        if manifest is None:
            detail = "Recap not ready yet" if session else "Recap not found"
            raise HTTPException(status_code=404, detail=detail)
        b2_keys = manifest.get("b2_keys", {})
    if not b2_keys:
        raise HTTPException(status_code=404, detail="No artifacts found")

    def _build_zip() -> io.BytesIO:
        """Blocking: download each artifact from B2 and zip it (runs off the loop)."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for artifact_name, b2_key in b2_keys.items():
                try:
                    data = b2.download_bytes(b2_key)
                    ext = Path(b2_key).suffix or ".bin"
                    zf.writestr(f"{artifact_name}{ext}", data)
                except Exception:
                    log.warning("download_zip.skip", artifact=artifact_name, key=b2_key)
        buf.seek(0)
        return buf

    # boto3 downloads + zip compression are synchronous — offload so the ZIP build
    # doesn't block the event loop (and stall every other request) while it runs.
    zip_buffer = await asyncio.to_thread(_build_zip)
    short_id = session_id[:8]

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="recap-{short_id}.zip"',
        },
    )
