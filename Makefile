.PHONY: install test lint type-check ci demo demo-start demo-stop dev clean

install:
	uv sync --group dev

test:
	uv run pytest tests/ -v

lint:
	uv run ruff check .

type-check:
	uv run mypy backend/

ci: lint type-check test

# Run the demo pipeline against both synthetic CSVs (API must be running)
demo:
	uv run python scripts/demo_run.py

# Start backend + frontend demo stack
demo-start:
	bash scripts/start_demo.sh

# Stop backend + frontend demo stack
demo-stop:
	bash scripts/stop_demo.sh

dev:
	uv run uvicorn backend.main:app --reload --port 8000

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	rm -f bankers_wrapped.db
	rm -f coverage.xml .coverage
	rm -rf logs/
