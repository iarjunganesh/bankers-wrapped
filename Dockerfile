FROM python:3.14-slim

# FFmpeg required for video composition
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg fonts-liberation && rm -rf /var/lib/apt/lists/*

# uv for fast, reproducible installs
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Dependencies first — cached unless pyproject.toml changes
# --no-install-project: install deps only, skip building the local package
# (PYTHONPATH=/app makes backend/ importable without hatchling needing README.md)
COPY pyproject.toml uv.lock* README.md ./
RUN uv sync --no-dev --frozen --no-install-project

# Application code
COPY backend/ ./backend/
# Swagger UI banner (served by backend/main.py:brand_asset) — only the two SVGs it needs
COPY assets/demo-cards/banner-light.svg assets/demo-cards/banner-dark.svg ./assets/demo-cards/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

CMD ["sh", "-c", "/app/.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
