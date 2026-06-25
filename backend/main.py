"""
Banker's Wrapped — FastAPI backend entrypoint.

Registers:
  - Structlog JSON logging
  - CORS middleware (allow all origins for hackathon MVP)
  - Request logging middleware
  - API routers: /api/v1/health, /api/v1/recap
"""

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.middleware.logging import RequestLoggingMiddleware
from backend.api.v1 import health, recap
from backend.config import get_settings

# ── Logging configuration ─────────────────────────────────────────────────────
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


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }
