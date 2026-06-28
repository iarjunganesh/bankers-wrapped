"""
GET /api/v1/recap/{session_id}/progress

Server-Sent Events stream for pipeline progress.
Emits events as each pipeline stage completes and closes when status reaches
'complete' or 'failed'.
"""

from __future__ import annotations

import asyncio
import json
import time

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from backend.api.v1.recap import get_session_store
from backend.storage.session_store import SessionStore

router = APIRouter()


@router.get("/{session_id}/progress")
async def progress_stream(
    session_id: str,
    store: SessionStore = Depends(get_session_store),
) -> StreamingResponse:
    """Stream pipeline progress events for a session via SSE."""

    async def _event_generator():  # type: ignore[return]
        # Wait up to 10 s for the POST /generate to create the session.
        # The frontend opens this SSE connection before sending the upload,
        # so the session may not exist yet when the first poll runs.
        deadline = asyncio.get_event_loop().time() + 10.0
        while True:
            if store.get(session_id):
                break
            if asyncio.get_event_loop().time() >= deadline:
                return  # session never appeared — silently close
            await asyncio.sleep(0.25)

        sent = 0
        while True:
            events = store.get_events(session_id)
            for ev in events[sent:]:
                yield f"data: {json.dumps(ev)}\n\n"
                sent += 1

            current = store.get(session_id)
            if current and current["status"] in ("complete", "failed"):
                final = {
                    "event": current["status"],
                    "detail": current.get("output_url", ""),
                    "ts": time.time(),
                }
                yield f"data: {json.dumps(final)}\n\n"
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
