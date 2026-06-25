"""
Structlog request logging middleware.

Logs every request with: method, path, status, duration_ms, request_id.
"""

import time
import uuid

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

log = structlog.get_logger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: object) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start = time.time()

        structlog.contextvars.bind_contextvars(request_id=request_id)

        log.info(
            "request.start",
            method=request.method,
            path=request.url.path,
        )

        response: Response = await call_next(request)  # type: ignore[operator]

        duration_ms = int((time.time() - start) * 1000)
        log.info(
            "request.complete",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=duration_ms,
        )

        structlog.contextvars.unbind_contextvars("request_id")
        response.headers["X-Request-ID"] = request_id
        return response
