# Synthetic Transaction Data

All datasets in this directory are **fully synthetic**. No real customer data,
personal financial information, or PII is included anywhere in this repository.

## CSV Schema

| Column | Type | Required | Notes |
|---|---|---|---|
| `date` | YYYY-MM-DD | ✅ | Transaction date |
| `description` | string | ✅ | Merchant or transfer description |
| `amount` | float | ✅ | Positive = income/credit, negative = expense/debit |
| `currency` | string | ❌ | ISO 4217 code (default: USD) |
| `category` | string | ❌ | Auto-inferred from description if omitted |

## Valid Categories

`income` · `savings` · `housing` · `food` · `travel` · `entertainment` ·
`utilities` · `investment` · `debt` · `other`

## Available Datasets

| File | Period | Transactions | Use case |
|---|---|---|---|
| `transactions_jan_2026.csv` | Jan 2026 | 22 | Primary demo — judges quickstart |
| `transactions_q4_2025.csv` | Oct–Dec 2025 | 39 | Larger dataset — richer analysis |

## Quickstart

```bash
# Run the pipeline with the January demo file
make demo
# or
curl -X POST http://localhost:8000/api/v1/recap/generate \
  -F "file=@data/synthetic/transactions_jan_2026.csv"
```
