# Demo Video — Shooting Script (≤ 3 min)

> **Target 2:50–2:55** (hard cap 3:00) · public on YouTube · **no copyrighted music** · 1080p screen capture.
> Two OBS recordings, not one — see **Recording #1** and **Recording #2** below. The live pipeline run is captured once, separately, then jump-cut clips from it are dropped into the edit — the main take never sits and waits for it.
> Fallback: two runs are pre-generated and validated if the live run on shoot day fails or needs a retake without spending more GMI credit:
> **CSV** `2e6bdb3d…` and **Plaid** `84cdf98f…` (see [`assets/README.md`](../assets/README.md)).

**Every criterion is earned on screen** — the mapping:

| Beat | Criterion it scores |
| --- | --- |
| Plaid "Connect a bank" + CSV | Real-World Utility (zero-friction ingestion, clear market) |
| Architecture diagram · Live SSE pipeline · Genblaze routing | Genblaze Usage (3 of 4 AI steps) |
| B2 console · `generation.json` · redeploy-survives | B2 Storage & Orchestration |
| CI/coverage/ADRs/rate-limit tag | Production Readiness |

---

## Why two recordings

The live pipeline run takes ~90–120 seconds. Sitting through that live, on camera, in your main take wastes time and risks an awkward pause. Instead:

- **Recording #1 — Live Pipeline**: one single OBS take that captures the real pipeline running start to finish, banked as raw footage. You'll cut small pieces out of it later.
- **Recording #2 — Main Take**: everything else — the CSV scroll, the app's home screen, the B2 console, GitHub, Codecov. Nothing in this take waits on a live pipeline run, so you can redo it as many times as you want at no extra GMI cost.

**Shared OBS settings for both recordings** — Base + Output **1920×1080**, **30 fps**, cursor **visible**; **Display Capture** (or Window Capture of the browser); **microphone disabled** (mic OFF — narration is pre-generated, you never narrate live); MP4 (or MKV → remux) at ~12–16 Mbps; set a **Start/Stop hotkey** so you never film the OBS window.

**Audio differs between the two recordings**: mic is OFF for both, no exceptions. **Desktop/system audio must stay ON for Recording #1** — the recap video autoplays with sound at the end of the live run, and beat 6 (payoff) needs that captured audio to duck `vo_05` under. **Recording #2 has no audio at all** — it's pure silent visual capture (scrolling, tab switches, no video playback), so speakers/system audio can be OFF too; nothing in that take needs sound.

**Mouse discipline** (what makes it read as polished) — move **deliberately**, click **confidently**, **pause** on anything a judge should read. Avoid rapid scrolling, excess cursor motion, hovering, and repeated tab-switching.

---

## Step 0 — one-time prep, before recording anything

1. **Architecture diagram**: already built and ready at [`assets/architecture/`](../assets/architecture/) — `architecture-diagram-{dark,light}.png`, brand-themed (no GitHub screenshot needed). Pick the variant matching the theme you film the app in. Used **exactly once**, in the editor, at beat 5 — you never need to show this diagram live in either OBS recording.
2. **Opening/closing cards**: already built and ready at [`assets/demo-cards/`](../assets/demo-cards/) — `banner-{dark,light}.png` (opening) and `signoff-{dark,light}.png` (closing), 1920×1080. Pick the variant matching the theme you film the app in. These are inserted directly in the editor as the first/last clips — **do not record them in OBS** (a browser tab around them would show browser chrome).
3. Clean browser profile, 100% zoom, bookmarks bar hidden, notifications off, **already logged into Backblaze** (no login screen on camera).

---

## Recording #1 — Live Pipeline (record this first, by itself)

1. Open your browser to the **Live App** — `https://bankers-wrapped.arjunganesh.dev` — fresh, nothing clicked yet.
2. Start OBS recording.
3. Click the button labeled **"🏦 Connect a bank (sandbox)"**.
4. In the window that opens (Plaid), search for and select **"First Platypus Bank"**.
5. Log in with username `user_good` (matching sandbox test password).
6. Select the accounts it offers, then click **Continue**. This is the moment that kicks off the real ~90–120 second pipeline run — this is the one time you're spending real money on this demo (~$0.15–0.27 in GMI credits). Don't repeat this recording unless you have to.
7. Leave the browser tab open and don't touch anything while it runs. A progress tracker advances through steps (parsing → analyzing → writing script → generating scene images → composing video → uploading).
8. Wait until the pipeline finishes and the finished recap video starts playing automatically in the app.
9. Let the recap video play all the way through once.
10. Stop OBS recording.
11. Save this file separately, labeled clearly, e.g. `live-run-take.mp4` — you'll pull small clips out of it in the editor.

---

## Recording #2 — Main Take (record this second, one continuous take)

Open these before you start recording, arranged so you can switch between them quickly:

| Label used below | What it actually is | What to have on screen before recording |
| --- | --- | --- |
| **Spreadsheet** | Excel (or Notepad/VS Code) | `data/synthetic/transactions_jan_2026.csv` open, scrolled to the top |
| **Live App** | The Banker's Wrapped Vercel web app | `https://bankers-wrapped.arjunganesh.dev`, fresh, nothing clicked |
| **Pre-Generated Recap Page** | The public share page for an already-finished demo session | `https://bankers-wrapped.arjunganesh.dev/recap/2e6bdb3d-228f-456c-971e-9855274b0d54` — use this run for on-screen numbers, *not* the live Plaid run (Plaid sandbox numbers are randomized) |
| **Backblaze B2 Console** | The Backblaze web dashboard, already logged in | Drilled into that same session's `pipeline/` folder, `generation.json` visible in the file listing (bucket `bankers-wrapped-assets` → `4d0f560b-…/2e6bdb3d-…/pipeline/`) |
| **GitHub — generation.json evidence** | The same file, downloaded from that exact B2 path and committed as evidence, viewed on GitHub (syntax-highlighted, actually readable) | `https://github.com/iarjunganesh/bankers-wrapped/blob/main/assets/csv-run/2e6bdb3d/evidence/2e6bdb3d_generation.json`, scrolled to the `"llm"` block |
| **GitHub README Page** | The project's GitHub repository page | `https://github.com/iarjunganesh/bankers-wrapped`, scrolled to the badges near the top |
| **Codecov Page** *(optional)* | The Codecov coverage report | `https://codecov.io/gh/iarjunganesh/bankers-wrapped` |

Now start OBS recording once, and go through these in order without stopping:

1. **On the Spreadsheet**: slowly scroll down through the transaction rows. Don't click anything. Hold for about 14 seconds.
2. **Switch to the Live App**: sit on the home screen (the first screen you see before clicking any button). Don't click anything yet. Hold for about 10 seconds.
3. **Switch to the Pre-Generated Recap Page**: scroll down to where it lists the artifact files (video, images, audio, JSON files — the "Pipeline Artifacts" section). Pause on it for a few seconds so it's readable.
4. **Switch to the Backblaze B2 Console**: sit on the `pipeline/` folder listing for a couple seconds with `generation.json` visible — this proves it's really stored in B2. Then **switch to the GitHub evidence file**: scroll to the `"llm"` block and the SHA-256 hash list so both are visible on screen (same file, just readable).
5. **Switch back to the Pre-Generated Recap Page**: hit your browser's refresh button and let the page reload and finish loading.
6. **Switch to the GitHub README Page**: sit for a few seconds on the row of badges (CI, coverage, etc.) near the top, then scroll down past the architecture diagram — don't linger on it, it's not used from here (see Step 0) — the ADR list sits right underneath it now, so pause there for a couple seconds.
7. **Switch to the Codecov Page** *(optional, only if time allows)*: sit on it for 2–3 seconds.
8. Stop OBS recording.
9. Save this file separately, e.g. `main-take.mp4`.

---

## Narration Script (verbatim, source of truth)

Generated via `scripts/generate_demo_voiceover.py` — OpenAI `tts-1`, voice `nova` — which is the
single source of truth for both the text below and the committed MP3s. Edit the text in that
script, not here; re-run it, then paste the fresh measured durations into this table so the two
never drift apart (see the version-sync policy in `CLAUDE.md`).

| Clip | Text | Words | Measured |
| --- | --- | --- | --- |
| `vo_01-hook` | "Every bank app shows you the same thing: a wall of numbers, a chart you scroll past, then nothing. Your money has a story. Nobody's telling it." | 27 | 8.5s |
| `vo_02-reveal` | "This is Banker's Wrapped — an AI pipeline that turns your transactions into a narrated recap video." | 17 | 6.3s |
| `vo_03-ingestion` | "Connect a bank in one click through Plaid, or just upload a CSV. Same pipeline either way — zero friction, zero forking." | 22 | 7.4s |
| `vo_04-pipeline` | "Four typed agents take it from there — parsing, analytics, a narrative script, and scene generation — all routed through the Genblaze SDK. GMI Cloud Seedream paints five scenes in parallel, OpenAI TTS narrates them, and FFmpeg composes the final video, live, in under two minutes." | 46 | 17.0s |
| `vo_05-payoff` | "Meet the Financial Builder — your personality, your story, playing right now." | 12 | 4.6s |
| `vo_06-b2` | "Every artifact lands on Backblaze B2 — fourteen files, ten types, from the input CSV to the final video — each one hashed and verifiable, with full generation provenance you can inspect yourself." | 33 | 12.3s |
| `vo_07-durability` | "Refresh the page after a full backend redeploy — the recap still plays. B2 is the source of truth." | 19 | 6.0s |
| `vo_08-production` | "Ninety-nine percent test coverage, a hard CI gate, structured logging, and eleven architecture decision records — this isn't a prototype." | 20 | 8.4s |
| `vo_09-close` | "One connection. Five scenes. Your financial story — Banker's Wrapped, built on Genblaze and Backblaze B2." | 16 | 6.6s |

**Narration spine ≈ 1:17** (77.1s measured via ffprobe, 2026-07-25) — shorter than the previous
script (was ≈1:36), so the beat timeline below adds visual pad rather than relying on narration
length alone to carry each beat.

---

## Final beat timeline

| # | Beat | VO clip (measured) | Source | Screen action | Duration | Ends at |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Opening card | silent | editor image (`assets/demo-cards/banner-{dark,light}.png`) | Brand card | 3s | 0:03 |
| 2 | Hook | `vo_01-hook` (8.5s) | Recording #2 — Spreadsheet | Slow, deliberate scroll of CSV rows — let numbers actually register | 13s | 0:16 |
| 3 | Reveal | `vo_02-reveal` (6.3s) | Recording #2 — Live App | Home screen, no clicks, hold a beat | 9s | 0:25 |
| 4 | Ingestion | `vo_03-ingestion` (7.4s) | Recording #1 — trim to the full Connect-a-bank flow: institution search → First Platypus Bank → login → account selection, stop right before "Continue" | Plaid connect flow shown at natural pace, not sped up | 22s | 0:47 |
| 5 | Architecture + Pipeline live | `vo_04-pipeline` (17.0s) | first 8s: editor image (`assets/architecture/architecture-diagram-{dark,light}.png`); remaining ~27s: Recording #1 — jump-cut 5–6 short (3–5s) clips of the progress tracker across the full run (parsing → scripting → each scene → composing → uploading) | Diagram flash → SSE tracker advancing through more of the real pipeline stages | 35s | 1:22 |
| 6 | Payoff — recap plays | 5s recap audio + `vo_05-payoff` (4.6s) | Recording #1 — the finished recap playing | Let the recap's own audio play longer before ducking — this is the emotional payoff, don't rush it | 16s | 1:38 |
| 7 | B2 — share list → console → `generation.json` | `vo_06-b2` (12.3s) | Recording #2 — Pre-Generated Recap Page → Backblaze B2 Console → GitHub evidence file | Artifact list, then a real browse of the B2 folder structure, then `generation.json` on GitHub with `llm` block + SHA-256 visible — give each screen its own moment | 28s | 2:06 |
| 8 | Durability — reload share link | `vo_07-durability` (6.0s) | Recording #2 — Pre-Generated Recap Page (refresh) | Page reloads, still plays | 9s | 2:15 |
| 9 | Production — CI/coverage/ADRs | `vo_08-production` (8.4s) | Recording #2 — GitHub README Page → Codecov Page (optional) | Badges, then a real pause on the ADR list (not the diagram — see Step 0), then Codecov | 17s | 2:32 |
| 10 | Close | `vo_09-close` (6.6s) | editor image (`assets/demo-cards/signoff-{dark,light}.png`) | Brand card hold | 15s | ~2:47 |

Total lands roughly **2:47** — inside the 2:50–2:55 target and comfortably under the 3:00 hard cap.
The pad beyond each measured VO clip is deliberate screen time (Plaid's multi-step flow, more SSE
jump-cuts across the full pipeline run, a longer B2 browse, the recap payoff breathing) — not dead
air. If it still runs short in the edit, extend beat 5 (more SSE clips) or beat 7 (linger longer on
`generation.json`) first; if you run long, trim those same two beats first.
**Never hold a static frame > ~15s** under continuous narration.

---

## Assembly (Clipchamp on Win11, or CapCut)

You'll end up with 3 image files (opening card, `architecture-diagram.png`, closing card) and 2 video files (`live-run-take.mp4`, `main-take.mp4`). Build the final video in this order:

1. Opening card (image)
2. From **main-take.mp4**: the Spreadsheet clip
3. From **main-take.mp4**: the Live App home-screen clip
4. From **live-run-take.mp4**: trim to just the Connect-a-bank clicks through login/account selection (skip ahead to right before clicking Continue)
5. `architecture-diagram.png` (image)
6. From **live-run-take.mp4**: 3–4 short (2–3s) clips of the progress tracker at different moments (e.g. "Writing narrative script", "3/5 scenes done", "composing video") — skip over the waiting parts
7. From **live-run-take.mp4**: the finished recap playing
8. From **main-take.mp4**: the Pre-Generated Recap Page artifact-list clip, then the Backblaze B2 Console clip, then the GitHub evidence-file clip
9. From **main-take.mp4**: the page-refresh clip
10. From **main-take.mp4**: the GitHub README Page clip, then Codecov clip if used
11. Closing card (image)

Then drop the nine `vo_NN` narration clips onto the audio track underneath, matching each one to its section above. For beat 6 (payoff) specifically: don't mute the recap clip — let its audio play ~5s, then duck it under `vo_05`.

---

## Production checklist

- [ ] Record at 1920×1080; hide bookmarks/personal tabs; use a clean browser profile.
- [ ] Recording #1 (Live Pipeline) done once — only re-record if something goes visibly wrong, since each run spends GMI credit.
- [ ] Recording #2 (Main Take) can be redone freely at no extra cost.
- [ ] `architecture-diagram.png` screenshotted once in Step 0, used only at beat 5.
- [ ] Jump-cut the generation wait in beat 5 (progress bar → result); total cut **≤ 3:00**.
- [ ] Captions/subtitles on (accessibility + judges often watch muted first).
- [ ] Music: silence, or a license-free bed only. **No copyrighted tracks** (rules).
- [ ] Upload **public** (not unlisted) to YouTube; paste the URL into README (badge + links row) and SUBMISSION/DEVPOST.
- [ ] Watch once at 1.0× end-to-end to confirm nothing reads as broken (avoid featuring Plaid's random-sandbox stats — use the CSV run for on-screen numbers).
