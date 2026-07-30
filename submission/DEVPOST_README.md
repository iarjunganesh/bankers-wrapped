# Banker's Wrapped

<!--
  MAINTAINER NOTE — this block is an HTML comment so the whole file stays paste-safe:
  select all, paste into Devpost, and nothing below renders as meta-commentary.

  This is a Devpost-paste mirror of the root README.md
  (https://github.com/iarjunganesh/bankers-wrapped/blob/main/README.md).
  Devpost's project-description field has no repo-root context, so every relative link and image
  path below is rewritten to an absolute github.com / raw.githubusercontent.com URL — paste this
  file's content directly into the Devpost form and every link and image still resolves.

  If you edit the README, regenerate this file rather than hand-editing it (see the version-sync
  policy in CLAUDE.md) so the two never drift apart. Verify with a normalized diff: strip this
  comment, rewrite the absolute URLs back to relative, and the result must equal README.md exactly.
  Last verified identical at v2.0.0 (2026-07-29) — 412 lines each.
-->

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/iarjunganesh/bankers-wrapped/main/assets/demo-cards/banner-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/iarjunganesh/bankers-wrapped/main/assets/demo-cards/banner-light.svg">
    <!-- ⬇ banner size — change this one width -->
    <img width="620" src="https://raw.githubusercontent.com/iarjunganesh/bankers-wrapped/main/assets/demo-cards/banner-light.svg"
         alt="Banker's Wrapped — Your financial year, told as a story. · Backblaze Generative Media Hackathon 2026"/>
  </picture>
</p>

[![CI](https://github.com/iarjunganesh/bankers-wrapped/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/iarjunganesh/bankers-wrapped/actions/workflows/ci.yml)
[![Codecov](https://codecov.io/gh/iarjunganesh/bankers-wrapped/graph/badge.svg?token=GSBUXVREL7)](https://codecov.io/gh/iarjunganesh/bankers-wrapped)
[![Release](https://img.shields.io/badge/release-latest-2ea44f?logo=github&logoColor=white)](https://github.com/iarjunganesh/bankers-wrapped/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/iarjunganesh/bankers-wrapped/blob/main/LICENSE)
[![Watch Video](https://img.shields.io/badge/%E2%96%B6_Watch-3--min_demo-FF0000?logo=youtube&logoColor=white)](https://youtu.be/eTw1TCcYFk4)

<!-- Row 2 — AI & Genblaze core -->
[![Agent Pattern](https://img.shields.io/badge/Agent_Pattern-asyncio_typed_agents-3776AB?logo=python&logoColor=white)](https://github.com/iarjunganesh/bankers-wrapped/blob/main/backend/agents/base.py)
[![Genblaze](https://img.shields.io/badge/Genblaze-SDK-7C3AED)](https://github.com/backblaze-labs/genblaze)
[![GMI Cloud](https://img.shields.io/badge/GMI_Cloud-Seedream-0066CC)](https://cloud.gmi.ai/)
[![NVIDIA NIM](https://img.shields.io/badge/NVIDIA_NIM-LLM-76B900?logo=nvidia&logoColor=white)](https://build.nvidia.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-TTS--1-412991?logo=openai&logoColor=white)](https://platform.openai.com/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-8.1.2-007808?logo=ffmpeg&logoColor=white)](https://ffmpeg.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-2.13_models-E92063?logo=pydantic&logoColor=white)](https://pydantic.dev/)
[![structlog](https://img.shields.io/badge/structlog-JSON_observability-4A90E2)](https://www.structlog.org/)
[![Plaid](https://img.shields.io/badge/Plaid-Sandbox_ingestion-111111?logo=plaid&logoColor=white)](https://plaid.com/)

<!-- Row 3 — Frontend + live Vercel app -->
[![Next.js](https://img.shields.io/badge/Next.js-16.2.11-000000?logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-19.2.8-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Node.js](https://img.shields.io/badge/Node.js-26-339933?logo=nodedotjs&logoColor=white)](https://nodejs.org/)
[![Vercel Hobby](https://img.shields.io/badge/Vercel-Hobby-000000?logo=vercel&logoColor=white)](https://vercel.com)

<!-- Row 4 — Backend -->
[![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.140-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Ruff](https://img.shields.io/badge/Ruff-lint%20%2B%20format-D7FF64?logo=ruff&logoColor=111827)](https://docs.astral.sh/ruff/)
[![pytest](https://img.shields.io/badge/pytest-9.1-0A9EDC?logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![Railway Hobby](https://img.shields.io/badge/Railway-Hobby-0B0D0E?logo=railway&logoColor=white)](https://railway.com)

<!-- Row 5 — Storage (source of truth) -->
[![Backblaze B2](https://img.shields.io/badge/Backblaze_B2-source_of_truth-E21C2A?logo=backblaze&logoColor=white)](https://www.backblaze.com/cloud-storage)
[![SQLite](https://img.shields.io/badge/SQLite-read_cache-003B57?logo=sqlite&logoColor=white)](https://sqlite.org/)

<!-- Row 6 — Hosting (live deployments) -->
[![Vercel live frontend](https://img.shields.io/badge/Vercel-live_frontend-000000?logo=vercel&logoColor=white)](https://bankers-wrapped.arjunganesh.dev)
[![Railway live API](https://img.shields.io/badge/Railway-live_API-0B0D0E?logo=railway&logoColor=white)](https://bankers-wrapped-api-production.up.railway.app/docs)

---

## What Is This?

Banker's Wrapped is an agentic AI platform that transforms raw transaction data into a **personalized narrated financial recap video** — fully generated, stored, and served via Backblaze B2, with every AI media call routed through the Genblaze SDK.

Upload a CSV. Receive a 60-second video that tells the story of your financial year. Inspired by Spotify Wrapped. Built for banking. Designed for production.

---

## The Problem

Banks generate mountains of transaction data but deliver it as an unreadable table. Customers disengage; apps go unused. Financial institutions lose the relationship. There is no moment that makes money *feel* meaningful.

Banker's Wrapped solves this with an agentic pipeline that reads your transactions, assigns a financial personality, writes a 5-scene cinematic narrative, synthesizes voice narration, generates scene images, and composes a sharable MP4 with cinematic dip-to-black transitions — end to end, no human in the loop.

---

## How It Works

1. **Upload** a CSV transaction export — or **connect a bank via Plaid Sandbox** (zero setup, no real credentials; the connector normalises Plaid transactions into the same schema)
2. **Document Agent** parses and normalizes transactions into typed records
3. **Analytics Agent** calculates income, expenses, savings rate, and top spending categories
4. **Financial Personality** is assigned: Builder · Optimizer · Explorer · Achiever
5. **Narrative Agent** generates a structured **5-scene cinematic video script** (Opening → Achievement → Insight → Advice → Close) — routed through **Genblaze chat** (ADR-007) on **GMI Cloud** (`openai/gpt-5.4-mini`), with automatic **NVIDIA NIM fallback** on provider failure or invalid JSON
6. **Scene images** generated via **Genblaze → GMI Cloud** (Seedream 4.0, 1344×768) — all 5 in parallel (with automatic 3× retry + exponential backoff)
7. **Voice narration** synthesised via **Genblaze → OpenAI TTS** (tts-1, alloy voice) — concatenated scene text
8. **FFmpeg** composes the final MP4: each scene rendered to a segment, then concat-joined with narration — **dip-to-black** transitions between scenes, browser-safe H.264 `yuv420p` + `faststart` / AAC (memory-bounded so it runs on any host)
9. **14 files** (10 artifact types) uploaded to **Backblaze B2** (video, thumbnail, script, analytics, prompts, generation provenance, 5 scenes, narration, CSV, metadata); presigned URL + download ZIP returned

---

## Architecture

<p align="center">
  <a href="https://raw.githubusercontent.com/iarjunganesh/bankers-wrapped/main/assets/architecture/architecture-diagram-light.svg" target="_blank" rel="noopener noreferrer">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/iarjunganesh/bankers-wrapped/main/assets/architecture/architecture-diagram-dark.svg">
      <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/iarjunganesh/bankers-wrapped/main/assets/architecture/architecture-diagram-light.svg">
      <img width="900" src="https://raw.githubusercontent.com/iarjunganesh/bankers-wrapped/main/assets/architecture/architecture-diagram-light.svg"
           alt="Banker's Wrapped architecture — User to FastAPI (rate-limit 5/hr) to the typed async Agent Pipeline to Backblaze B2 (14 files); the pipeline runs Document, Analytics, Narrative (Genblaze Chat on GMI Cloud, NIM fallback), and Media Agent, which fans out to GMI Cloud Seedream and OpenAI TTS before FFmpeg composes the final video"/>
    </picture>
  </a>
</p>

<sub>Click to enlarge (opens full-resolution SVG — scales without pixelation): <a href="https://raw.githubusercontent.com/iarjunganesh/bankers-wrapped/main/assets/architecture/architecture-diagram-light.svg" target="_blank" rel="noopener noreferrer">light</a> / <a href="https://raw.githubusercontent.com/iarjunganesh/bankers-wrapped/main/assets/architecture/architecture-diagram-dark.svg" target="_blank" rel="noopener noreferrer">dark</a> · Source: [`assets/architecture/architecture-diagram.mmd`](https://github.com/iarjunganesh/bankers-wrapped/blob/main/assets/architecture/architecture-diagram.mmd) — rendered to brand-themed SVG/PNG (dark + light) via `mermaid-cli`; see [`assets/architecture/README.md`](https://github.com/iarjunganesh/bankers-wrapped/blob/main/assets/architecture/README.md) for the regenerate command.</sub>

**In short:** ~2–4 minutes end to end, with image generation dominating (5 scenes generated in parallel); **14 files across 10 artifact types** persisted to Backblaze B2 as the source of truth; every artifact carries a **SHA-256** and every step logs model, latency, and retries.

> **Deep dive** → **[`docs/ARCHITECTURE.md`](https://github.com/iarjunganesh/bankers-wrapped/blob/main/docs/ARCHITECTURE.md)** — per-step pipeline timing, the full B2 storage layout, lifecycle & integrity (45-day retention + per-artifact SHA-256), and the four machine-readable provenance manifests.

### Architecture Decision Records

Twelve decisions documented (001–012), **all accepted and implemented** — see [`docs/adr/`](https://github.com/iarjunganesh/bankers-wrapped/tree/main/docs/adr) for full rationale.

| ADR | Decision |
| --- | --- |
| [001](https://github.com/iarjunganesh/bankers-wrapped/blob/main/docs/adr/001-genblaze-central.md) | Genblaze as sole media generation layer — no direct provider calls |
| [002](https://github.com/iarjunganesh/bankers-wrapped/blob/main/docs/adr/002-semantic-kernel-orchestration.md) | Lightweight typed async agent pipeline — Semantic Kernel considered, not adopted (no framework dependency) |
| [003](https://github.com/iarjunganesh/bankers-wrapped/blob/main/docs/adr/003-ffmpeg-over-remotion.md) | FFmpeg for composition; Runway ML / Luma AI excluded (impl revised in v1.6.0) |
| [004](https://github.com/iarjunganesh/bankers-wrapped/blob/main/docs/adr/004-sqlite-for-mvp.md) | SQLite for MVP, PostgreSQL as documented production upgrade |
| [005](https://github.com/iarjunganesh/bankers-wrapped/blob/main/docs/adr/005-financial-personality-core.md) | Financial Personality promoted to required scope — the emotional hook |
| [006](https://github.com/iarjunganesh/bankers-wrapped/blob/main/docs/adr/006-observability-scope.md) | structlog JSON logging only — OpenTelemetry is post-hackathon |
| [007](https://github.com/iarjunganesh/bankers-wrapped/blob/main/docs/adr/007-genblaze-sole-ai-layer.md) | Route the narrative LLM through Genblaze (GMI Cloud chat, NIM fallback) — 3 of 4 AI steps via Genblaze |
| [008](https://github.com/iarjunganesh/bankers-wrapped/blob/main/docs/adr/008-b2-source-of-truth.md) | B2 as session source of truth — SQLite is a cache; sessions survive redeploys |
| [009](https://github.com/iarjunganesh/bankers-wrapped/blob/main/docs/adr/009-b2-lifecycle-integrity.md) | B2 lifecycle rules (45-day retention) + per-artifact SHA-256 integrity |
| [010](https://github.com/iarjunganesh/bankers-wrapped/blob/main/docs/adr/010-plaid-sandbox-ingestion.md) | Plaid sandbox connector — optional "connect a bank" path (live in production) |
| [011](https://github.com/iarjunganesh/bankers-wrapped/blob/main/docs/adr/011-compositor-redesign.md) | Memory-bounded segment+concat compositor + non-blocking event loop (v1.6.0 redesign) |
| [012](https://github.com/iarjunganesh/bankers-wrapped/blob/main/docs/adr/012-custom-domain-hosting.md) | Custom domain for the frontend (`bankers-wrapped.arjunganesh.dev`) + explicit Railway CORS origins |

---

## Genblaze Integration

Genblaze is **not optional** — it is the AI orchestration layer. **Three of the four AI steps route through Genblaze**: scene images (GMI Cloud Seedream), narration audio (OpenAI TTS wrapped in `GenblazeClient`), and narrative script generation (Genblaze chat on GMI Cloud — `openai/gpt-5.4-mini` — with automatic NVIDIA NIM fallback via the same SDK wrapper). Zero direct provider API calls outside `genblaze_client.py`.

```python
# Scene images — Genblaze → GMI Cloud Seedream  (all 5 in parallel via asyncio.gather)
pr = (
    Pipeline("bankers-wrapped-image")
    .step(GMICloudImageProvider(),
          model="seedream-4-0-250828",
          prompt=scene.visual_prompt,
          modality=Modality.IMAGE,
          width=1344,
          height=768)
    .run(timeout=300, raise_on_failure=True)
)
image_bytes = httpx.get(pr.run.steps[0].assets[0].url).content

# Narration audio — OpenAI TTS wrapped inside GenblazeClient (no direct provider calls outside)
audio_result = await genblaze_client.generate_narration_audio(
    narration_text=script.full_narration,   # all 5 scene narrations joined
    model="tts-1",
    voice="alloy",
)
```

Every run produces a **SHA-256 provenance manifest** stored in B2 metadata — full model traceability per video.

Provenance is verifiable from **both sides**: the pipeline's own `generation.json` per session, and
GMI Cloud's console — see [`assets/gmi-cloud/`](https://github.com/iarjunganesh/bankers-wrapped/tree/main/assets/gmi-cloud) for the provider's record of the
same calls (recently-used models, per-model spend, and the generated scene images with timestamps
matching the committed runs).

---

## Financial Personality

The emotional centrepiece of every recap. One of four labels is assigned based on spending and saving patterns:

| Personality | Trigger | Scene 1 Hook |
| --- | --- | --- |
| **Financial Builder** | Savings rate ≥ 15% or active debt reduction | *"You're laying the foundation — brick by brick."* |
| **Financial Explorer** | Top spend in travel or entertainment | *"You invest in experiences that last a lifetime."* |
| **Financial Achiever** | Active investing or steady 8–14% savings | *"Your discipline is paying off — literally."* |
| **Financial Optimizer** | Lean discretionary spend, efficient budget | *"Every dollar has a purpose in your world."* |

The personality label opens Scene 1 and drives the entire visual and narrative tone.

---

## Tech Stack

| Layer | Technology | Role |
| --- | --- | --- |
| **Media Generation** | [![Genblaze](https://img.shields.io/badge/Genblaze-SDK-7C3AED)](https://github.com/backblaze-labs/genblaze) | Sole orchestrator for all AI media calls |
| **Storage** | [![Backblaze B2](https://img.shields.io/badge/Backblaze-B2-FF0000?logo=backblaze&logoColor=white)](https://www.backblaze.com/cloud-storage) | Structured artifact store + presigned delivery |
| **Backend** | [![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/) [![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org/) | Async agentic pipeline |
| **Agent Pattern** | [![asyncio](https://img.shields.io/badge/asyncio-typed_agents-3776AB?logo=python&logoColor=white)](https://github.com/iarjunganesh/bankers-wrapped/blob/main/backend/agents/base.py) | Hand-rolled typed async agent pipeline — no heavyweight framework (ADR-002) |
| **LLM** | [![Genblaze](https://img.shields.io/badge/Genblaze-SDK_chat-7C3AED)](https://github.com/backblaze-labs/genblaze) [![NVIDIA NIM](https://img.shields.io/badge/NVIDIA_NIM-76B900?logo=nvidia&logoColor=white)](https://build.nvidia.com/) | Narrative script — Genblaze SDK chat on GMI Cloud (`openai/gpt-5.4-mini`), automatic NVIDIA NIM fallback |
| **Images** | [![GMI Cloud](https://img.shields.io/badge/GMI_Cloud-Seedream-0066CC)](https://cloud.gmi.ai/) | Scene visuals 1344×768, seedream-4-0-250828 (via Genblaze) — 5 parallel, retry ×3 |
| **Video Compose** | [![FFmpeg](https://img.shields.io/badge/FFmpeg-8.1.2-007808?logo=ffmpeg&logoColor=white)](https://ffmpeg.org/) | Scene images + narration → H.264/AAC MP4 (segment + concat, dip-to-black) |
| **Frontend** | [![Next.js](https://img.shields.io/badge/Next.js-16.2.11-000000?logo=nextdotjs&logoColor=white)](https://nextjs.org/) [![React](https://img.shields.io/badge/React-19.2.8-61DAFB?logo=react&logoColor=black)](https://react.dev/) [![Node.js](https://img.shields.io/badge/Node.js-26-339933?logo=nodedotjs&logoColor=white)](https://nodejs.org/) | Upload portal + video player |
| **Session State** | [![Backblaze B2](https://img.shields.io/badge/B2-source_of_truth-FF0000?logo=backblaze&logoColor=white)](https://www.backblaze.com/cloud-storage) [![SQLite](https://img.shields.io/badge/SQLite-cache-003B57?logo=sqlite&logoColor=white)](https://sqlite.org/) | B2 manifest is the durable record (ADR-008); SQLite is a fast read cache |
| **Hosting** | [![Railway](https://img.shields.io/badge/Backend-Railway-0B0D0E?logo=railway&logoColor=white)](https://railway.app) [![Vercel](https://img.shields.io/badge/Frontend-Vercel-000000?logo=vercel&logoColor=white)](https://vercel.com) | Backend on Railway · Frontend on Vercel |
| **Observability** | [![structlog](https://img.shields.io/badge/structlog-JSON-4A90E2)](https://www.structlog.org/) | Structured request + agent logging |

---

## Live & Interactive Demo

| | |
| --- | --- |
| **App** | [https://bankers-wrapped.arjunganesh.dev](https://bankers-wrapped.arjunganesh.dev) ✅ live (verified 2026-07-25) — previously `bankers-wrapped.vercel.app`, still live as a fallback |
| **API** | [https://bankers-wrapped-api-production.up.railway.app](https://bankers-wrapped-api-production.up.railway.app) |
| **Demo Video** | [https://youtu.be/eTw1TCcYFk4](https://youtu.be/eTw1TCcYFk4) — 2:50, captions included |
| **Try It Now** | `make demo` — runs the full pipeline with synthetic data, no real bank account needed |

Hackathon judging criteria and submission checklist: [`submission/SUBMISSION.md`](https://github.com/iarjunganesh/bankers-wrapped/blob/main/submission/SUBMISSION.md)

### Run it yourself — the interactive notebook

[![Open in Jupyter](https://img.shields.io/badge/Demo-Jupyter%20Notebook-F37626?logo=jupyter&logoColor=white)](https://github.com/iarjunganesh/bankers-wrapped/blob/main/notebooks/DEMO_RUNBOOK.ipynb)

**[`notebooks/DEMO_RUNBOOK.ipynb`](https://github.com/iarjunganesh/bankers-wrapped/blob/main/notebooks/DEMO_RUNBOOK.ipynb)** — a self-contained interactive walkthrough of the full pipeline. No frontend, no local backend required. Just set your API keys and run against the live Railway deployment.

| Scenario | API cost | Time | What you'll see |
| --- | --- | --- | --- |
| **A — Financial Builder** (Jan 2026) | LLM + 5 images + TTS | ~2–3 min | Full end-to-end run · amber personality · 5-scene video |
| **B — Financial Explorer** (Q4 2025) | LLM + 5 images + TTS | ~2–3 min | Second personality type · teal theme · 39-transaction dataset |
| **C — Pre-generated session** | **None** | < 5 s | Fetch a completed session from B2 · inspect all 14 artifacts |
| Comparison chart | — | instant | Income vs expenses side-by-side across both datasets |
| Timing chart | — | instant | Where the ~2 min goes — image generation dominates |
| B2 inspection | — | instant | Full 14-file (10-type) B2 layout printed per session |

```bash
# Run against the live production API — no local setup needed
pip install httpx matplotlib jupyter
jupyter notebook notebooks/DEMO_RUNBOOK.ipynb
```

---

## Screenshots

Full judge-facing galleries and raw evidence for two complete runs (CSV upload and Plaid Sandbox) are organized in [`assets/README.md`](https://github.com/iarjunganesh/bankers-wrapped/blob/main/assets/README.md).

| Product Flow | B2 Provenance |
| --- | --- |
| ![Upload Portal](https://raw.githubusercontent.com/iarjunganesh/bankers-wrapped/main/assets/csv-run/d987fbba/screenshots/d987fbba_01-app-upload-portal.png) | ![B2 Bucket + Lifecycle](https://raw.githubusercontent.com/iarjunganesh/bankers-wrapped/main/assets/csv-run/2e6bdb3d/screenshots/2e6bdb3d_05-b2-bucket-overview-lifecycle.png) |
| ![Connect a Bank via Plaid](https://raw.githubusercontent.com/iarjunganesh/bankers-wrapped/main/assets/plaid-run/84cdf98f/screenshots/84cdf98f_02-plaid-connect-intro.png) | ![Session Folder](https://raw.githubusercontent.com/iarjunganesh/bankers-wrapped/main/assets/csv-run/d987fbba/screenshots/d987fbba_09-b2-pipeline-folder.png) |
| ![Generated Video Result](https://raw.githubusercontent.com/iarjunganesh/bankers-wrapped/main/assets/csv-run/d987fbba/screenshots/d987fbba_03-generated-video-result.png) | ![Generation JSON Details](https://raw.githubusercontent.com/iarjunganesh/bankers-wrapped/main/assets/csv-run/d987fbba/screenshots/d987fbba_10-b2-generation-json-details.png) |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/iarjunganesh/bankers-wrapped
cd bankers-wrapped

# 2. Configure
cp .env.example .env
# Fill in: GMI_API_KEY, NVIDIA_NIM_API_KEY, B2_KEY_ID, B2_APPLICATION_KEY, B2_ENDPOINT_URL

# 3. Install (requires Python 3.14 and ffmpeg)
make install

# 4. Start backend + frontend
make demo-start           # bash scripts/start_demo.sh
# — or backend only:
make dev                  # uvicorn on :8000 with hot-reload

# 5. Run the demo pipeline against both synthetic datasets
make demo                 # python scripts/demo_run.py

# 6. Stop all services when done
make demo-stop            # bash scripts/stop_demo.sh
```

On Windows, use the PowerShell equivalents directly:

```powershell
.\scripts\start_demo.ps1
python scripts\demo_run.py
.\scripts\stop_demo.ps1
```

---

## Synthetic Demo Data

No real bank data required. Two datasets committed to [`data/synthetic/`](https://github.com/iarjunganesh/bankers-wrapped/tree/main/data/synthetic):

| File | Period | Transactions | Personality Triggered |
| --- | --- | --- | --- |
| `transactions_jan_2026.csv` | Jan 2026 | 22 | **Financial Builder** |
| `transactions_q4_2025.csv` | Oct–Dec 2025 | 39 | **Financial Explorer** |

### CSV Schema

| Column | Type | Required | Notes |
| --- | --- | --- | --- |
| `date` | YYYY-MM-DD | ✅ | Transaction date |
| `description` | string | ✅ | Merchant or transfer description |
| `amount` | float | ✅ | Positive = income/credit, negative = expense/debit |
| `currency` | string | ❌ | ISO 4217 code (default: USD) |
| `category` | string | ❌ | Auto-inferred from description if omitted |

**Valid categories:** `income` · `savings` · `housing` · `food` · `travel` · `entertainment` · `utilities` · `investment` · `debt` · `other`

```csv
date,description,amount,currency,category
2026-01-03,Salary Deposit,6500.00,USD,income
2026-01-05,ICA Maxi Grocery,-128.40,USD,food
2026-01-15,Savings Transfer,-1200.00,USD,savings
2026-01-20,Lufthansa Flight,-312.00,USD,travel
```

```bash
# Run the full pipeline with the January demo file
make demo
# or directly via curl
curl -X POST http://localhost:8000/api/v1/recap/generate \
  -F "file=@data/synthetic/transactions_jan_2026.csv"
```

---

## Project Structure

```text
bankers-wrapped/
├── backend/
│   ├── agents/          # 4 typed async agents (Document, Analytics, Narrative, Media)
│   ├── api/
│   │   ├── limiter.py   # slowapi rate limiter (5 req/hr/IP)
│   │   ├── middleware/  # Request logging
│   │   └── v1/
│   │       ├── recap.py    # POST /generate · GET /{session_id} (B2 fallback) · /download ZIP
│   │       ├── progress.py # GET /{session_id}/progress (SSE)
│   │       ├── plaid.py    # POST /plaid/link-token · /plaid/exchange (feature-flagged)
│   │       └── health.py   # status + version + plaid_enabled
│   ├── ingest/          # PlaidConnector — sandbox "connect a bank" path (ADR-010)
│   ├── media/           # GenblazeClient (images + chat + TTS) · FFmpegComposer
│   ├── storage/         # B2Client (source of truth) · SessionStore (SQLite cache)
│   ├── models/          # Pydantic models (Transaction, Insights, Script, Session)
│   └── config.py        # Pydantic Settings
├── frontend/
│   └── app/
│       ├── page.tsx                    # Upload portal + Plaid Link + live SSE progress
│       └── recap/[session_id]/page.tsx # Public share page
├── tests/
│   ├── unit/            # Per-agent unit tests (all providers mocked)
│   ├── integration/     # API end-to-end tests (incl. B2-fallback + SSE stream)
│   └── load/            # k6 smoke test (manual — p95 + rate-limiter behavior)
├── infra/               # b2-lifecycle.json — bucket retention as code (ADR-009)
├── scripts/             # demo_run · apply_b2_lifecycle · recompose · start/stop_demo
├── notebooks/           # DEMO_RUNBOOK.ipynb — interactive pipeline walkthrough
├── data/synthetic/      # Demo CSVs — committed, no PII
├── prompts/             # LLM system prompts (narrative_agent.txt)
├── submission/          # Judge deliverables
│   ├── DEVPOST.md         # Devpost form content
│   ├── DEVPOST_README.md  # Devpost-paste mirror of this README (absolute links)
│   ├── SUBMISSION.md      # Evidence-first judging alignment + deliverables checklist
│   ├── DEMO_SCRIPT.md     # ≤3-min video shooting script + OBS runbook + narration script
│   └── COSTS.md           # Component budget — everything stays live through judging
├── docs/
│   ├── ARCHITECTURE.md  # Deep dive — timing, B2 layout, lifecycle, provenance manifests
│   └── adr/             # 12 Architecture Decision Records (all accepted)
├── Dockerfile           # python:3.14-slim + FFmpeg + uv
├── railway.json         # Railway backend deployment
├── render.yaml          # Render backend deployment (alternative)
├── CLAUDE.md            # Claude Code project context
└── .github/workflows/ci.yml # Lint → type-check → test (≥80% coverage gate) → Codecov
```

---

## Production & Quality

```text
push → ruff lint → mypy type-check → pytest (≥80% coverage gate) → Codecov
```

See [`.github/workflows/ci.yml`](https://github.com/iarjunganesh/bankers-wrapped/blob/main/.github/workflows/ci.yml). Coverage sits at **99%**; the API is rate-limited (5 uploads/hr/IP), emits structured JSON logs via structlog, wraps every media call in tenacity retries (3 attempts, exponential backoff), and exposes a `/health` endpoint.

### Load & Resilience

[`tests/load/k6_smoke.js`](https://github.com/iarjunganesh/bankers-wrapped/blob/main/tests/load/k6_smoke.js) ramps 20 concurrent users against `/health` (threshold: p95 < 500 ms), exercises the B2 fallback 404 path, and verifies the rate limiter answers `/generate` abuse with graceful 429s (never 5xx):

```bash
winget install k6   # or: brew install k6
k6 run tests/load/k6_smoke.js                                  # local backend
k6 run -e BASE_URL=https://<railway-url> tests/load/k6_smoke.js  # production
```

---

## Future Roadmap

**Shipped:** every planned workstream is implemented and live — one-click **Plaid** ingestion alongside CSV upload, the narrative LLM routed through **Genblaze → GMI Cloud** with automatic NVIDIA NIM fallback (**3 of 4 AI steps** now go through Genblaze), **B2 as the source of truth** with a SHA-256 per artifact and a committed lifecycle rule, a memory-bounded FFmpeg compositor, and 99% test coverage. Full history in the [CHANGELOG](https://github.com/iarjunganesh/bankers-wrapped/blob/main/CHANGELOG.md).

**What's next — from demo to product:**

- **Multi-period recaps** — monthly and quarterly stories, not just annual, with trend detection across periods
- **White-label widget** — an embeddable drop-in banks and fintechs ship inside their own apps (the core go-to-market)
- **Richer personalities + peer benchmarking** — more archetypes and "how you compare" framing
- **Broader ingestion** — PDF statement parsing (Azure Document Intelligence) and live Plaid **production** access beyond sandbox
- **Goal Tracking Agent** — savings-milestone and debt-payoff detection woven into the narrative
- **Deeper generative media** — animated scene clips (Genblaze → Runway) and an optional AI banker avatar (HeyGen)

---

## Disclaimer

All transaction data used in development and demonstration is **fully synthetic**. No real customer data or PII is processed, stored, or transmitted. Not affiliated with any bank or financial institution. Not financial advice.

> *Built by [Arjun Ganesh](https://github.com/iarjunganesh) for the [Backblaze Generative Media Hackathon 2026](https://backblaze-generative-media.devpost.com/).*

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/iarjunganesh/bankers-wrapped/main/assets/demo-cards/signoff-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/iarjunganesh/bankers-wrapped/main/assets/demo-cards/signoff-light.svg">
    <!-- ⬇ sign-off size — change this one width -->
    <img width="620" src="https://raw.githubusercontent.com/iarjunganesh/bankers-wrapped/main/assets/demo-cards/signoff-light.svg"
         alt="Banker's Wrapped — One connection. Five scenes. Your financial story. · Powered by Genblaze on Backblaze B2"/>
  </picture>
</p>
