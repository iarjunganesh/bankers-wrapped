# Contributing

## Setup

```bash
git clone https://github.com/iarjunganesh/bankers-wrapped
cd bankers-wrapped
cp .env.example .env   # fill in your credentials
make install           # uv sync --group dev
make dev               # uvicorn on :8000
```

## Before Submitting a PR

```bash
make lint   # ruff + mypy must pass
make test   # pytest ≥80% coverage gate must pass
```

## Key Constraints

- **Genblaze is mandatory** — all media calls must route through `GenblazeClient`, never directly to providers
- **B2 stores everything** — do not add local file storage paths
- `get_settings()` is `@lru_cache` — call `get_settings.cache_clear()` in any test that needs different env vars
- `FFmpegComposer.compose()` is `async def` — always `await` it

## Adding a New Provider

1. Add the `genblaze-<provider>` package to `pyproject.toml`
2. Add any new API key fields to `backend/config.py` and `.env.example`
3. Extend `GenblazeClient` with the new provider call
4. Update tests in `tests/unit/` to mock the new provider
5. Document the decision in `docs/adr/` if it affects the architecture

## Synthetic Data

Use `data/synthetic/transactions_jan_2026.csv` or `transactions_q4_2025.csv` for local testing.
Never commit real bank data or PII.
