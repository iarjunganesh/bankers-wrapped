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
from pathlib import Path

import structlog
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import FileResponse, HTMLResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.api.limiter import limiter
from backend.api.middleware.logging import RequestLoggingMiddleware
from backend.api.v1 import health, plaid, progress, recap
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
    docs_url=None,
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

# ── Theme-aware Swagger UI ────────────────────────────────────────────────────
# Swagger UI ships light-only. `docs_url=None` above disables the default route so
# this one can inject a real banner header, self-served from this container (not an
# external CDN — a proxy fetching arbitrary GitHub content is exactly the kind of
# third-party asset ad blockers/corporate proxies block, which is silent and
# undebuggable from the server side) via /brand/{filename}.svg below.
# The banner is spliced into the page shell — NOT the OpenAPI `description` field —
# because Swagger UI renders `description` through its own markdown sanitizer, which
# strips <picture>/<source> and leaves only a static <img src>. Sitting outside
# `#swagger-ui` (the div SwaggerUIBundle mounts into) it also survives client-side render.
# Only the header toggles with prefers-color-scheme — NOT the Swagger UI chrome itself
# (no CSS filter-invert on `.swagger-ui`): that trick also inverts hue-coded schema/type
# badges into visually "highlighted"-looking noise, trading one cosmetic problem for
# another. Swagger UI has no first-party dark theme, so its panel stays light always.
_brand_directory = Path(__file__).parent.parent / "assets" / "demo-cards"
_brand_files = {"light": "banner-light.svg", "dark": "banner-dark.svg"}
_SWAGGER_HEAD_CSS = """
<style>
  :root { color-scheme: light dark; }
  /* Full-bleed background strip (edge to edge); the image itself is capped and
     centered via the horizontal padding, same technique as a marketing hero. */
  #docs-banner {
    display: flex;
    justify-content: center;
    padding: 32px max(16px, calc((100vw - 900px) / 2));
    background: #fafafa;
    border-bottom: 1px solid #e5e5e5;
  }
  /* <picture> is inline by default — giving it (not just the <img> inside it)
     an explicit block width is what makes the img's percentage width resolve
     consistently across browsers, especially Firefox. Capped at 900px — the
     source SVG is natively 1000x410, so this stays under 1:1 with no upscale blur. */
  #docs-banner picture { display: block; width: 100%; max-width: 900px; }
  #docs-banner img { display: block; width: 100%; height: auto; }
  @media (prefers-color-scheme: dark) {
    #docs-banner { background: #14141f; border-bottom-color: #2a2a3d; }
  }
</style>
"""
_DOCS_BANNER_HTML = """
<div id="docs-banner">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="/brand/dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="/brand/light.svg">
    <img src="/brand/light.svg" alt="Banker's Wrapped">
  </picture>
</div>
"""


@app.get("/brand/{theme}.svg", include_in_schema=False)
async def brand_asset(theme: str) -> FileResponse:
    """Serve the theme-aware banner used by the Swagger UI docs page."""
    filename = _brand_files.get(theme)
    if filename is None:
        raise HTTPException(status_code=404, detail="Unknown brand theme.")
    return FileResponse(_brand_directory / filename, media_type="image/svg+xml")


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html() -> HTMLResponse:
    response = get_swagger_ui_html(
        openapi_url=app.openapi_url or "/openapi.json",
        title=f"{app.title} — Swagger UI",
    )
    html = bytes(response.body).decode("utf-8")
    html = html.replace("</head>", f"{_SWAGGER_HEAD_CSS}</head>")
    html = html.replace('<div id="swagger-ui">', f'{_DOCS_BANNER_HTML}<div id="swagger-ui">')
    return HTMLResponse(html)


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(recap.router, prefix="/api/v1/recap", tags=["recap"])
app.include_router(progress.router, prefix="/api/v1/recap", tags=["progress"])
# Plaid routes are always mounted but answer 404 unless PLAID_* keys are set
# (ADR-010) — the app boots and behaves identically without Plaid credentials.
app.include_router(plaid.router, prefix="/api/v1/plaid", tags=["plaid"])


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }
