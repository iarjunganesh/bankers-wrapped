.PHONY: install test lint type-check ci demo dev clean

install:
	poetry install

test:
	poetry run pytest tests/ -v

lint:
	poetry run ruff check .

type-check:
	poetry run mypy backend/

ci: lint type-check test

demo:
	@echo "Starting Banker's Wrapped demo pipeline..."
	curl -s -X POST http://localhost:8000/api/v1/recap/generate \
	  -F "file=@data/synthetic/transactions_jan_2026.csv" | python3 -m json.tool

dev:
	poetry run uvicorn backend.main:app --reload --port 8000

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	rm -f bankers_wrapped.db
	rm -f coverage.xml .coverage
