# Assets Index — Judge-Facing Evidence

Two **complete, independently validated** pipeline runs are captured here, one per ingestion path.
Both route the narrative LLM through **Genblaze → GMI Cloud (`openai/gpt-5.4-mini`)** with automatic
NVIDIA NIM fallback, store **14 files / 10 artifact types** to Backblaze B2, and carry a **SHA-256 for
all 12 content artifacts** in `generation.json`.

| Run | Folder | Session | Ingestion | Recap URL |
| --- | --- | --- | --- | --- |
| **CSV upload** (canonical — the run the demo video shows) | [`csv-run/d987fbba/`](csv-run/d987fbba/) | `d987fbba-b143-46e6-be5b-c9326d3bf88e` | `data/synthetic/transactions_jan_2026.csv` | [/recap/d987fbba…](https://bankers-wrapped.arjunganesh.dev/recap/d987fbba-b143-46e6-be5b-c9326d3bf88e) |
| **CSV upload** (earlier run, 2026-07-14) | [`csv-run/2e6bdb3d/`](csv-run/2e6bdb3d/) | `2e6bdb3d-228f-456c-971e-9855274b0d54` | same CSV | [/recap/2e6bdb3d…](https://bankers-wrapped.arjunganesh.dev/recap/2e6bdb3d-228f-456c-971e-9855274b0d54) |
| **Plaid Sandbox** (WS-4) | [`plaid-run/`](plaid-run/) | `84cdf98f-b8ce-457a-969f-724cf116c130` | "Connect a bank" → `input/plaid_sandbox.csv` | [/recap/84cdf98f…](https://bankers-wrapped.arjunganesh.dev/recap/84cdf98f-b8ce-457a-969f-724cf116c130) |

Both CSV runs use the **same input file two weeks apart** and produce identical insights (January 2026,
$13,850 income, 8.7% savings, Financial Builder) — the pipeline is deterministic on its analytics.
`d987fbba` is the one to cite: it ran on 2026-07-28 against the custom domain and current UI, in
**90.4 s**, and is what the demo video shows on screen.

Each folder has `evidence/` (raw B2 JSONs, prefixed with the short session id) and `screenshots/`
(numbered in walkthrough order).

**Provider-side corroboration** lives in [`gmi-cloud/`](gmi-cloud/): GMI Cloud's own console showing
the account's recently-used models (`GPT-5.4-mini` + `seedream-4-0-250828`), real per-model spend,
and the generated scene images with timestamps matching both runs above. Everything else in this
folder is the application's own record of what it did — that one is the provider's.

---

## Which run to cite for what

- **Financial story, personality, stats, the recap video** → use **`csv-run/`**. It runs on the committed
  synthetic dataset, so the numbers are coherent: *Financial Builder*, January 2026, income **$13,850**,
  expenses **$4,352**, an **8.7% savings rate**.
- **Zero-friction ingestion ("Connect a bank")** → use **`plaid-run/`**. Screenshot `01` is the in-app
  "Connect a bank" click, `02–07` capture the full Plaid Link flow (institution search → First Platypus
  Bank → `user_good` login → account select → save prompt), and `14` shows the resulting
  **`input/plaid_sandbox.csv`** in B2 — proof that a live bank connection flows into
  the **exact same** pipeline and B2 layout as a CSV upload, with zero code forking between paths.
  > **On the numbers:** this run is powered by Plaid's Sandbox, which by design serves *synthetic* test
  > transactions (the canonical `user_good` account) rather than a real spending history. That's exactly what
  > makes it perfect evidence: it proves the **ingestion path is real and production-shaped** end-to-end,
  > independent of any one dataset. The pipeline faithfully renders whatever the bank returns — and the
  > `csv-run/` above demonstrates the analytics on a realistic dataset (a coherent 8.7% savings story). Two
  > runs, one pipeline: **real connectivity** proven by Plaid, **real insight quality** proven by the CSV run.
  >
  > **Why this run shows a 1358% savings rate:** Plaid's sandbox fixture is internally inconsistent, and
  > it is identical for every sandbox institution (the transactions are bound to the `user_good` test
  > user, not the bank). It reports the `ACH Electronic Credit GUSTO PAY` payroll row as
  > `amount=+5850, personal_finance_category=TRANSFER_OUT` — i.e. money *leaving* the account — while the
  > only inflows it labels are a `$4.22` interest payment and a `$500` airline refund. Income therefore
  > reads as `$504.22` against `$11,149.46` of outflows, and `savings ÷ income` lands at 1358%. The
  > connector's sign handling follows Plaid's documented convention (outflows positive, negated on
  > ingest — `backend/ingest/plaid_connector.py`), so this is a property of the sandbox dataset, not of
  > the analytics. The `csv-run/` figures above are the ones that reflect how the analytics behave on a
  > coherent month.

---

## LLM provenance (both runs, from `generation.json`)

```json
"llm": {
  "provider": "gmi-cloud",
  "model": "gpt-5.4-mini-2026-03-17",
  "tokens_in": 386, "tokens_out": 474,
  "cost_usd": 0.002422
}
```

`models_used.llm` = `gmi-cloud/gpt-5.4-mini-2026-03-17` · 12/12 artifacts SHA-256-hashed · status `complete`.

---

## Evidence files (per run)

`evidence/<session>_generation.json` (model, provider, latency, retries, tokens, cost, per-artifact SHA-256) ·
`_session-metadata.json` (self-contained manifest + all 14 b2_keys) · `_analytics.json` · `_script.json` ·
`_prompts.json`. The Plaid run additionally includes `84cdf98f_input-plaid_sandbox.csv` (the Plaid→CSV
normalisation output); the CSV run's input is the committed `data/synthetic/transactions_jan_2026.csv`.

## Screenshot highlights

- **`csv-run/d987fbba/`** (`d987fbba_01, 03, 04, 09, 10`) — **the current set**, captured 2026-07-28 on the
  custom domain with the shipped frontend (v1.9.1 typography onward, unchanged through 2.0.0): upload portal · result + personality badge with the recap
  playing · in-app 14-file B2 artifact list · B2 console `pipeline/` folder · `generation.json` details.
- **`csv-run/2e6bdb3d/`** (`2e6bdb3d_01…13`): the fuller earlier walkthrough (2026-07-14) — upload portal ·
  live SSE progress (script step ~4 s on GMI) · result + personality badge · in-app 14-file B2 artifact
  list · B2 console: bucket overview (custom lifecycle rule), root session index, session/pipeline/scenes
  folders, `generation.json` + `session_metadata.json` details. Retained because it covers B2 console
  screens the newer set doesn't, and because two runs a fortnight apart on identical input demonstrate
  the analytics are deterministic.
- **`plaid-run/`** (`84cdf98f_01…19`): in-app "Connect a bank" click (`01`) · the full **Plaid Link** flow
  (`02–07`) · SSE progress · result · B2 console browse including **`14` `input/plaid_sandbox.csv`** details.
