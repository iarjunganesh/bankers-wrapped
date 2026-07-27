# GMI Cloud — Provider-Side Evidence

Every other evidence folder here (`csv-run/`, `plaid-run/`) is **this application's own record** of
what it did: `generation.json` and `session_metadata.json` are emitted by the pipeline itself. That
is strong provenance, but it is still one side of the conversation.

These two screenshots are the **provider's** record of the same work — GMI Cloud's own console,
confirming that the Genblaze SDK calls documented in [ADR-007](../../docs/adr/007-genblaze-sole-ai-layer.md)
actually landed on GMI infrastructure, against the models this project claims to use.

| File | What it proves |
| --- | --- |
| `01-models-and-spend.png` | GMI Cloud **Home** — the account's *recently used models* are exactly the two this project routes through Genblaze: **OpenAI `GPT-5.4-mini`** (LLM) and **BytePlus `seedream-4-0-250828`** (Text-to-Image). The **Usage By Model** chart shows real per-model spend over a 30-day window, with the `07/27/2026` tooltip breaking out `seedream-4-0-250828` **$0.15** and `gpt-5.4-mini` **$0.003** for a **$0.153** daily total. |
| `02-seedream-generation-history.png` | GMI Cloud **History** — **207 generations, kept for 60 days**, every tile tagged `seedream-4-0-250828`. Timestamps corroborate all three runs: *"an hour ago"* (the 2026-07-27 verification run) and *"13 days ago" / "14 days ago"* (the committed [`csv-run/2e6bdb3d`](../csv-run/) and [`plaid-run/84cdf98f`](../plaid-run/) sessions). The imagery visibly matches the financial-recap scene themes — savings vaults, category breakdowns, growth curves. |

## Cross-checks a judge can run

- The model ids here match `models_used` in every `*_session-metadata.json` under `csv-run/` and
  `plaid-run/`, and the `llm` / `image` blocks in each `*_generation.json`.
- `GPT-5.4-mini` appearing under *recently used models* substantiates
  [ADR-007](../../docs/adr/007-genblaze-sole-ai-layer.md)'s constraint that `GMI_CHAT_MODEL` must be
  an id GMI actually serves — GMI hosts no meta-llama models, which is why the NIM fallback exists.
- The generation timestamps line up with the session dates in the committed evidence folders.

> **Note on cost (2026-07-27):** the daily total of **$0.153** for a single 5-scene run — `seedream`
> $0.15 plus `gpt-5.4-mini` $0.003 — is the **measured** per-run GMI cost, and
> [`submission/COSTS.md`](../../submission/COSTS.md) has been reconciled against it (2026-07-28).
> An earlier planning estimate in that document assumed `$0.05/image` and put the run at ≈ $0.27;
> the measured figure implies roughly `$0.03/image`, about 37% lower. This screenshot is the source
> of truth for that number.

## What is deliberately *not* here

No credential evidence, by design. Neither image exposes an API key, organisation id, or payment
detail — the "API Keys" and "Create API Key" items visible are navigation labels only, and the
API Keys page itself is never screenshotted.

Judges do not need credentials to verify this project. Authenticity is established by the live
hosted app, the per-session `generation.json` / `session_metadata.json` provenance manifests in
`csv-run/` and `plaid-run/`, and these provider-side console views — three independent angles on
the same calls, none of which require exposing a secret.
