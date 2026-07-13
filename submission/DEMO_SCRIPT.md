# Demo Video — Shooting Script (≤ 3 min)

> **Target 2:50–2:55** (hard cap 3:00) · public on YouTube · **no copyrighted music** · 1080p screen capture.
> Two OBS recordings, not one — see **Recording #1** and **Recording #2** below. The live pipeline run is captured once, separately, then jump-cut clips from it are dropped into the edit — the main take never sits and waits for it.
> Fallback: two runs are pre-generated and validated if the live run on shoot day fails or needs a retake without spending more GMI credit:
> **CSV** `d5b45acf…` and **Plaid** `481ede61…` (see [`assets/README.md`](../assets/README.md)).

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

**Mouse discipline** (what makes it read as polished) — move **deliberately**, click **confidently**, **pause** on anything a judge should read. Avoid rapid scrolling, excess cursor motion, hovering, and repeated tab-switching.

---

## Step 0 — one-time prep, before recording anything

1. **Architecture diagram screenshot**: on the **GitHub README Page** (`https://github.com/iarjunganesh/bankers-wrapped`), screenshot just the rendered architecture diagram (the boxes-and-arrows graph near the top, under the "Architecture" heading). Save it as `architecture-diagram.png`. This image is used **exactly once**, in the editor, at beat 5. You never need to show this diagram live in either OBS recording.
2. **Opening/closing cards**: already built and ready at [`assets/demo-cards/`](../assets/demo-cards/) — `opening-card-{dark,light}.png` and `closing-card-{dark,light}.png`, 1920×1080. Pick the variant matching the theme you film the app in. These are inserted directly in the editor as the first/last clips — **do not record them in OBS** (a browser tab around them would show browser chrome).
3. Clean browser profile, 100% zoom, bookmarks bar hidden, notifications off, **already logged into Backblaze** (no login screen on camera).

---

## Recording #1 — Live Pipeline (record this first, by itself)

1. Open your browser to the **Live App** — `https://bankers-wrapped.vercel.app` — fresh, nothing clicked yet.
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
| **Live App** | The Banker's Wrapped Vercel web app | `https://bankers-wrapped.vercel.app`, fresh, nothing clicked |
| **Pre-Generated Recap Page** | The public share page for an already-finished demo session | `https://bankers-wrapped.vercel.app/recap/d5b45acf-3094-42b6-9147-4f0d236f4d95` — use this run for on-screen numbers, *not* the live Plaid run (Plaid sandbox numbers are randomized) |
| **Backblaze B2 Console** | The Backblaze web dashboard, already logged in | Drilled into that same session's `pipeline/` folder, one click away from opening `generation.json` (bucket `bankers-wrapped-assets` → `d5e87bd9-…/d5b45acf-…/pipeline/generation.json`) |
| **GitHub README Page** | The project's GitHub repository page | `https://github.com/iarjunganesh/bankers-wrapped`, scrolled to the badges near the top |
| **Codecov Page** *(optional)* | The Codecov coverage report | `https://codecov.io/gh/iarjunganesh/bankers-wrapped` |

Now start OBS recording once, and go through these in order without stopping:

1. **On the Spreadsheet**: slowly scroll down through the transaction rows. Don't click anything. Hold for about 14 seconds.
2. **Switch to the Live App**: sit on the home screen (the first screen you see before clicking any button). Don't click anything yet. Hold for about 10 seconds.
3. **Switch to the Pre-Generated Recap Page**: scroll down to where it lists the artifact files (video, images, audio, JSON files — the "Pipeline Artifacts" section). Pause on it for a few seconds so it's readable.
4. **Switch to the Backblaze B2 Console**: click into `generation.json` and hover near the `"llm"` block and the SHA-256 hash list so both are visible on screen.
5. **Switch back to the Pre-Generated Recap Page**: hit your browser's refresh button and let the page reload and finish loading.
6. **Switch to the GitHub README Page**: sit for a few seconds on the row of badges (CI, coverage, etc.) near the top, then scroll *past* the architecture diagram — don't linger on it, it's not used from here (see Step 0) — down to wherever the ADR list is (the architecture decision records), and pause there for a couple seconds.
7. **Switch to the Codecov Page** *(optional, only if time allows)*: sit on it for 2–3 seconds.
8. Stop OBS recording.
9. Save this file separately, e.g. `main-take.mp4`.

---

## Final beat timeline

| # | Beat | VO clip (measured) | Source | Screen action | Duration | Ends at |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Opening card | silent | editor image (`assets/demo-cards/opening-card`) | Brand card | 3s | 0:03 |
| 2 | Hook | `vo_01-hook` (12.2s) | Recording #2 — Spreadsheet | Slow scroll of CSV rows | 14s | 0:17 |
| 3 | Reveal | `vo_02-reveal` (7.8s) | Recording #2 — Live App | Home screen, no clicks | 10s | 0:27 |
| 4 | Ingestion | `vo_03-ingestion` (10.3s) | Recording #1 — trim to Connect-a-bank clicks through login/account selection, stop right before "Continue" | Plaid connect flow | 17s | 0:44 |
| 5 | Architecture + Pipeline live | `vo_04-pipeline` (22.0s) | first 7s: editor image (`architecture-diagram.png`); remaining ~25s: Recording #1 — jump-cut 3–4 short (2–3s) clips of the progress tracker at different moments | Diagram flash → SSE tracker advancing | 32s | 1:16 |
| 6 | Payoff — recap plays | 5s recap audio + `vo_05-payoff` (6.0s) | Recording #1 — the finished recap playing | Let the recap's own audio play ~5s, then bring in `vo_05` and duck the recap audio under it | 15s | 1:31 |
| 7 | B2 — share list → console → `generation.json` | `vo_06-b2` (16.2s) | Recording #2 — Pre-Generated Recap Page → Backblaze B2 Console | Artifact list, then `generation.json` with `llm` block + SHA-256 visible | 27s | 1:58 |
| 8 | Durability — reload share link | `vo_07-durability` (6.9s) | Recording #2 — Pre-Generated Recap Page (refresh) | Page reloads, still plays | 12s | 2:10 |
| 9 | Production — CI/coverage/ADRs | `vo_08-production` (8.1s) | Recording #2 — GitHub README Page → Codecov Page (optional) | Badges, then ADR list (not the diagram — see Step 0) | 15s | 2:25 |
| 10 | Close | `vo_09-close` (6.9s) | editor image (`assets/demo-cards/closing-card`) | Brand card hold | 13s | ~2:38 |

**Narration spine ≈ 1:36** across the nine `vo_NN` clips (`vo_full-reference.mp3` = the whole track). Total lands roughly **2:38–2:53** depending on how tight the pad trims run in the edit — comfortably inside the 2:50–2:55 target and the 3:00 hard cap. If you run long, trim the B2 browse (beat 7) or the SSE jump-cuts (beat 5) first. **Never hold a static frame > ~15s** under continuous narration.

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
8. From **main-take.mp4**: the Pre-Generated Recap Page artifact-list clip, then the Backblaze B2 Console clip
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
