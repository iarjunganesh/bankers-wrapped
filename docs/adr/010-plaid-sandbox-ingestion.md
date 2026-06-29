# ADR-010: Plaid Sandbox Connector as an Optional Ingestion Path
**Status:** Proposed (v1.7.0) | **Date:** 2026-06-30

## Decision
Add an **optional** "Connect a bank (sandbox)" ingestion path using **Plaid Sandbox**, alongside
the existing CSV upload. Plaid transactions are normalized into the same `List[Transaction]` the
`DocumentAgent` produces, so the rest of the pipeline is unchanged. CSV upload stays the default
and the offline/zero-dependency path for the demo.

## Rationale
- The strongest weakness on Real-World Utility is CSV friction — real users don't export CSVs.
  A "connect your bank" path reframes the product as "any bank, zero setup."
- Plaid **Sandbox** is free, requires no real bank, and returns realistic transaction data —
  perfect for a demo without cost or PII risk.
- Keeps the CSV path intact: judges can still run the offline synthetic datasets with no keys.

## Consequences / risks
- Adds `plaid-python` + 3 env vars (`PLAID_CLIENT_ID`, `PLAID_SECRET`, `PLAID_ENV=sandbox`);
  must be **feature-flagged off** when unset so the app still runs with only the CSV path.
- Plaid Link is a frontend flow (token exchange) — a small `/api/v1/plaid/*` surface is needed.
- Category taxonomy differs from our CSV schema — a mapping layer is required in the connector.

## Alternatives considered
- Mocked "connect bank" button (no real Plaid) — cheaper, but a real sandbox link is far more
  convincing in the demo for marginal extra effort.
- Full production Plaid (Development/Production tier) — out of scope; sandbox is sufficient.
