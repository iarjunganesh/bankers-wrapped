"""
Banker's Wrapped — FastAPI backend entrypoint.

Registers:
  - Structlog JSON logging
  - CORS middleware (allow all origins for hackathon MVP)
  - Request logging middleware
  - API routers: /api/v1/health, /api/v1/recap
"""

import logging
import sys

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.api.limiter import limiter
from backend.api.middleware.logging import RequestLoggingMiddleware
from backend.api.v1 import health, progress, recap
from backend.config import get_settings

# ── Logging configuration ─────────────────────────────────────────────────────
# Route stdlib logging (uvicorn, genblaze SDK, etc.) to stdout.
# force=True removes any handlers uvicorn may have installed before app import.
# start_demo.ps1 merges stderr→stdout at the process level (2>&1) so all logs
# land in a single backend.log regardless of which stream they originate from.
logging.basicConfig(stream=sys.stdout, level=logging.INFO, force=True)

# Uvicorn installs its own handlers on these loggers that write to STDERR, which
# makes Railway tag normal startup/access lines (e.g. "Started server process",
# "Application startup complete") as severity=error. Clear those handlers and let
# the records propagate to the root logger (stdout) so all logs are uniformly info.
for _uvicorn_logger in ("uvicorn", "uvicorn.error", "uvicorn.access"):
    _lg = logging.getLogger(_uvicorn_logger)
    _lg.handlers.clear()
    _lg.propagate = True

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

# ── App ───────────────────────────────────────────────────────────────────────
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "AI-powered financial storytelling platform. "
        "Upload a CSV. Get your personalized financial recap video."
    ),
)

# ── Rate limiting ─────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(recap.router, prefix="/api/v1/recap", tags=["recap"])
app.include_router(progress.router, prefix="/api/v1/recap", tags=["progress"])


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }
