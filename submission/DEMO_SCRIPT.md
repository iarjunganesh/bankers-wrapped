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

**Audio differs between the two recordings**: mic is OFF for both, no exceptions. **Desktop/system audio must stay ON for Recording #1** — the recap video autoplays with sound at the end of the live run, and beat 7 (payoff) needs that captured audio to duck `vo_05` under. **Recording #2 has no audio at all** — it's pure silent visual capture (scrolling, tab switches, no video playback), so speakers/system audio can be OFF too; nothing in that take needs sound.

**Mouse discipline** (what makes it read as polished) — move **deliberately**, click **confidently**, **pause** on anything a judge should read. Avoid rapid scrolling, excess cursor motion, hovering, and repeated tab-switching.

---

## Step 0 — one-time prep, before recording anything

1. **Architecture diagram**: already built and ready at [`assets/architecture/`](../assets/architecture/) — `architecture-diagram-{dark,light}.png`, brand-themed (no GitHub screenshot needed). Pick the variant matching the theme you film the app in. Used **exactly once**, in the editor, at beat 6 — you never need to show this diagram live in either OBS recording.
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
| **GitHub Repo — Top** | The project's GitHub repository page, scrolled to the very top | `https://github.com/iarjunganesh/bankers-wrapped`, scrolled to show the banner, badge rows, "What Is This?", and "The Problem" sections |
| **Spreadsheet** | Excel (or Notepad/VS Code) | `data/synthetic/transactions_jan_2026.csv` open, scrolled to the top |
| **Live App** | The Banker's Wrapped Vercel web app | `https://bankers-wrapped.arjunganesh.dev`, fresh, nothing clicked |
| **Pre-Generated Recap Page** | The public share page for an already-finished demo session | `https://bankers-wrapped.arjunganesh.dev/recap/2e6bdb3d-228f-456c-971e-9855274b0d54` — use this run for on-screen numbers, *not* the live Plaid run (Plaid sandbox numbers are randomized) |
| **Backblaze B2 Console** | The Backblaze web dashboard, already logged in | Drilled into that same session's `pipeline/` folder, `generation.json` visible in the file listing (bucket `bankers-wrapped-assets` → `4d0f560b-…/2e6bdb3d-…/pipeline/`) |
| **GitHub — generation.json evidence** | The same file, downloaded from that exact B2 path and committed as evidence, viewed on GitHub (syntax-highlighted, actually readable) | `https://github.com/iarjunganesh/bankers-wrapped/blob/main/assets/csv-run/2e6bdb3d/evidence/2e6bdb3d_generation.json`, scrolled to the `"llm"` block |
| **GitHub README Page — Badges/ADRs** | The project's GitHub repository page, scrolled further down | `https://github.com/iarjunganesh/bankers-wrapped`, scrolled to the badges near the top (revisited — a *different* scroll position than the opening tab above) |
| **Codecov Page** *(optional)* | The Codecov coverage report | `https://codecov.io/gh/iarjunganesh/bankers-wrapped` |

Now start OBS recording once, and go through these in order without stopping:

1. **On GitHub Repo — Top**: sit on the banner and badge rows for a moment, then scroll slowly down through "What Is This?" and "The Problem" — this is the opening beat, give it room to be read. Hold/scroll for about 18 seconds total.
2. **Switch to the Spreadsheet**: slowly scroll down through the transaction rows. Don't click anything. Hold for about 8 seconds.
3. **Switch to the Live App**: sit on the home screen (the first screen you see before clicking any button). Don't click anything yet. Hold for about 6 seconds.
4. **Switch to the Pre-Generated Recap Page**: scroll down to where it lists the artifact files (video, images, audio, JSON files — the "Pipeline Artifacts" section). Pause on it for a few seconds so it's readable.
5. **Switch to the Backblaze B2 Console**: sit on the `pipeline/` folder listing for a couple seconds with `generation.json` visible — this proves it's really stored in B2. Then **switch to the GitHub evidence file**: scroll to the `"llm"` block and the SHA-256 hash list so both are visible on screen (same file, just readable).
6. **Switch back to the Pre-Generated Recap Page**: hit your browser's refresh button and let the page reload and finish loading.
7. **Switch to GitHub README Page — Badges/ADRs**: sit for a few seconds on the row of badges (CI, coverage, etc.) near the top, then scroll down past the architecture diagram — don't linger on it, it's not used from here (see Step 0) — the ADR list sits right underneath it now, so pause there for a couple seconds.
8. **Switch to the Codecov Page** *(optional, only if time allows)*: sit on it for 2–3 seconds.
9. Stop OBS recording.
10. Save this file separately, e.g. `main-take.mp4`.

---

## Narration Script (verbatim, source of truth)

Generated via `scripts/generate_demo_voiceover.py` — OpenAI `tts-1`, voice `nova` — which is the
single source of truth for both the text below and the committed MP3s. Edit the text in that
script, not here; re-run it, then paste the fresh measured durations into this table so the two
never drift apart (see the version-sync policy in `CLAUDE.md`).

| Clip | Text | Words | Measured |
| --- | --- | --- | --- |
| `vo_00-intro` | "Banks generate mountains of transaction data but deliver it as an unreadable table. Customers disengage. Banker's Wrapped turns that data into a personalized, narrated recap video — Genblaze is the sole AI layer, Backblaze B2 the source of truth for every session." | 42 | 16.4s |
| `vo_01-hook` | "Here's the raw material — just rows, dates, and numbers." | 10 | 3.3s |
| `vo_02-reveal` | "See it live, right now — no mockup, no slides." | 10 | 2.7s |
| `vo_03-ingestion` | "Connect a bank in one click through Plaid, or just upload a CSV. Same pipeline either way — zero friction, zero forking." | 22 | 7.3s |
| `vo_04-pipeline` | "Four typed agents take it from there — parsing, analytics, a narrative script, and scene generation — all routed through the Genblaze SDK. GMI Cloud Seedream paints five scenes in parallel, OpenAI TTS narrates them, and FFmpeg composes the final video, live, in under two minutes." | 46 | 16.9s |
| `vo_05-payoff` | "Meet the Financial Builder — your personality, your story, playing right now." | 12 | 4.5s |
| `vo_06-b2` | "Every artifact lands on Backblaze B2 — fourteen files, ten types, from the input CSV to the final video — each one hashed and verifiable, with full generation provenance you can inspect yourself." | 33 | 12.2s |
| `vo_07-durability` | "Refresh the page after a full backend redeploy — the recap still plays. B2 is the source of truth." | 19 | 6.1s |
| `vo_08-production` | "Ninety-nine percent test coverage, a hard CI gate, structured logging, and eleven architecture decision records — this isn't a prototype." | 20 | 8.5s |
| `vo_09-close` | "One connection. Five scenes. Your financial story — Banker's Wrapped, built on Genblaze and Backblaze B2." | 16 | 6.3s |

**Narration spine ≈ 1:24** (84.2s measured via ffprobe, 2026-07-25). `vo_00-intro` names **both**
sponsor technologies by role in its very first breath — Genblaze as the sole AI layer, B2 as the
source of truth — not just generic "AI platform" language, since this is the single highest-value
15 seconds in the video for the two AI/storage judging criteria. `vo_02-reveal` deliberately does
**not** re-introduce the product name/tagline — `vo_00-intro` already did that over the GitHub
repo beat, so reveal just transitions to "it's live" (no double-naming).

**Word counts above are the budget** — don't add words without removing others, and re-run
`scripts/generate_demo_voiceover.py` (then re-paste the measured durations here) after any
wording change, so the script and the committed MP3s never drift apart.

---

## Final beat timeline

The **Overlay** column is a one-line lower-third — keep it on screen ≤ 4s, one per beat, terse.
It carries the fact a muted viewer or a judge skimming with the sound off would otherwise miss,
and doubles as a captioning aid.

| # | Beat | VO clip (measured) | Source | Screen action | Overlay (lower-third) | Duration | Ends at |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Opening card | silent | editor image (`assets/demo-cards/banner-{dark,light}.png`) | Brand card | none | 3s | 0:03 |
| 2 | **NEW** — Repo intro: name, tagline, Genblaze + B2 roles, "What Is This?", "The Problem" | `vo_00-intro` (16.4s) | Recording #2 — GitHub Repo — Top | Slow scroll from banner/badges through "What Is This?" and "The Problem" — timed to narration | `Genblaze: sole AI layer · Backblaze B2: source of truth` | 19s | 0:22 |
| 3 | Hook | `vo_01-hook` (3.3s) | Recording #2 — Spreadsheet | Slow, deliberate scroll of CSV rows — let numbers actually register, even past where narration ends | `A CSV isn't a story.` | 9s | 0:31 |
| 4 | Reveal | `vo_02-reveal` (2.7s) | Recording #2 — Live App | Home screen, no clicks, hold a beat | `bankers-wrapped.arjunganesh.dev · live` | 7s | 0:38 |
| 5 | Ingestion | `vo_03-ingestion` (7.3s) | Recording #1 — trim to the full Connect-a-bank flow: institution search → First Platypus Bank → login → account selection, stop right before "Continue" | Plaid connect flow shown at natural pace, not sped up | `One click. Zero CSV export.` | 20s | 0:58 |
| 6 | Architecture + Pipeline live | `vo_04-pipeline` (16.9s) | first 8s: editor image (`assets/architecture/architecture-diagram-{dark,light}.png`); remaining ~25s: Recording #1 — jump-cut 5–6 short (3–5s) clips of the progress tracker across the full run (parsing → scripting → each scene → composing → uploading) | Diagram flash → SSE tracker advancing through more of the real pipeline stages | `4 agents · Genblaze SDK · GMI Cloud + OpenAI` | 33s | 1:31 |
| 7 | Payoff — recap plays | 5s recap audio + `vo_05-payoff` (4.5s) | Recording #1 — the finished recap playing | Let the recap's own audio play longer before ducking — this is the emotional payoff, don't rush it | `Financial Builder · 5 scenes` | 15s | 1:46 |
| 8 | B2 — share list → console → `generation.json` | `vo_06-b2` (12.2s) | Recording #2 — Pre-Generated Recap Page → Backblaze B2 Console → GitHub evidence file | Artifact list, then a real browse of the B2 folder structure, then `generation.json` on GitHub with `llm` block + SHA-256 visible — give each screen its own moment | `14 files · 10 types · SHA-256 per artifact` | 26s | 2:12 |
| 9 | Durability — reload share link | `vo_07-durability` (6.1s) | Recording #2 — Pre-Generated Recap Page (refresh) | Page reloads, still plays | `Redeploy-proof — B2 is the source of truth` | 9s | 2:21 |
| 10 | Production — CI/coverage/ADRs | `vo_08-production` (8.5s) | Recording #2 — GitHub README Page — Badges/ADRs → Codecov Page (optional) | Badges, then a real pause on the ADR list (not the diagram — see Step 0), then Codecov | `99% coverage · 12 ADRs · CI on every push` | 16s | 2:37 |
| 11 | Close | `vo_09-close` (6.3s) | editor image (`assets/demo-cards/signoff-{dark,light}.png`) | Brand card hold, fade in the live URL | `bankers-wrapped.arjunganesh.dev` | 13s | ~2:50 |

Total lands roughly **2:50** — right at the target and comfortably under the 3:00 hard cap.
The pad beyond each measured VO clip is deliberate screen time (Plaid's multi-step flow, more SSE
jump-cuts across the full pipeline run, a longer B2 browse, the recap payoff breathing) — not dead
air. If it still runs short in the edit, extend beat 6 (more SSE clips) or beat 8 (linger longer on
`generation.json`) first; if you run long, trim those same two beats first.
**Never hold a static frame > ~15s** under continuous narration.

---

## Assembly (Clipchamp on Win11, or CapCut)

You'll end up with 3 image files (opening card, `architecture-diagram.png`, closing card) and 2 video files (`live-run-take.mp4`, `main-take.mp4`). Build the final video in this order:

1. Opening card (image)
2. From **main-take.mp4**: the GitHub Repo — Top clip (banner/badges scrolling into "What Is This?" / "The Problem")
3. From **main-take.mp4**: the Spreadsheet clip
4. From **main-take.mp4**: the Live App home-screen clip
5. From **live-run-take.mp4**: trim to just the Connect-a-bank clicks through login/account selection (skip ahead to right before clicking Continue)
6. `architecture-diagram.png` (image)
7. From **live-run-take.mp4**: 3–4 short (2–3s) clips of the progress tracker at different moments (e.g. "Writing narrative script", "3/5 scenes done", "composing video") — skip over the waiting parts
8. From **live-run-take.mp4**: the finished recap playing
9. From **main-take.mp4**: the Pre-Generated Recap Page artifact-list clip, then the Backblaze B2 Console clip, then the GitHub evidence-file clip
10. From **main-take.mp4**: the page-refresh clip
11. From **main-take.mp4**: the GitHub README Page — Badges/ADRs clip, then Codecov clip if used
12. Closing card (image)

Then drop the ten `vo_NN` narration clips onto the audio track underneath, matching each one to its section above. For beat 7 (payoff) specifically: don't mute the recap clip — let its audio play ~5s, then duck it under `vo_05`. Add the lower-third overlay text from the beat timeline above, one per beat, on screen ≤ 4s.

**Edit rhythm**: cut on clicks, not mid-motion; one zoom/pan per beat, max; never hold a static frame longer than the beat's Duration column says. Watch the final cut once with **audio off** (the story must survive on picture + overlays alone) and once with **video off** (the narration must survive alone, without the overlays) — both have to pass before calling it done.

---

## Honesty rules (what not to imply on screen)

- **Never splice the pre-generated CSV run's footage into the live-run beats** (5–7) as if it
  were the live Plaid run — the Pre-Generated Recap Page is explicitly for beat 8's *static*
  artifact/B2/evidence browsing, where the pipeline events already happened; Recording #1 is
  the only footage allowed to stand in for "this is happening live."
- **Plaid sandbox numbers are randomized test data** — never caption or narrate them as if they
  represent a typical real spending pattern (this is already why beat 5/7's on-screen numbers
  should come from the CSV run, not the live Plaid run — see the Recording #2 table above).
- **The redeploy-durability beat (9) only airs if actually demonstrated** — if you skip
  triggering a real Railway redeploy before filming, cut this beat rather than showing a page
  refresh and implying redeploy-survival without having actually redeployed.
- **The 99% coverage / 12 ADR claims in beat 10 must match what `make test` and `ls docs/adr/`
  actually report on shoot day** — re-verify both numbers immediately before recording, not from
  memory of an earlier run (see `CLAUDE.md`'s version-sync policy).
- **The GitHub repo intro beat (2) must show the actual current README** — if "What Is This?" or
  "The Problem" text changes before shoot day, re-screenshot/re-scroll rather than filming a
  stale version of the page.
- Every "live" claim in the narration (vo_02, vo_04, vo_07) must be backed by footage of the
  actual hosted app at `bankers-wrapped.arjunganesh.dev` — never a local dev server standing in.

---

## Production checklist

- [ ] Record at 1920×1080; hide bookmarks/personal tabs; use a clean browser profile.
- [ ] Recording #1 (Live Pipeline) done once — only re-record if something goes visibly wrong, since each run spends GMI credit.
- [ ] Recording #2 (Main Take) can be redone freely at no extra cost.
- [ ] `architecture-diagram.png` screenshotted once in Step 0, used only at beat 6.
- [ ] Jump-cut the generation wait in beat 6 (progress bar → result); total cut **≤ 3:00**.
- [ ] Captions/subtitles on (accessibility + judges often watch muted first).
- [ ] Music: silence, or a license-free bed only. **No copyrighted tracks** (rules).
- [ ] Upload **public** (not unlisted) to YouTube; paste the URL into README (badge + links row) and SUBMISSION/DEVPOST.
- [ ] Watch once at 1.0× end-to-end to confirm nothing reads as broken (avoid featuring Plaid's random-sandbox stats — use the CSV run for on-screen numbers).
- [ ] Lower-third overlays present for every beat that specifies one (see Final beat timeline), each on screen ≤ 4s.
- [ ] Watched once with audio off (story survives on picture + overlays alone) and once with video off (narration survives alone).
- [ ] Every "live" claim in the narration is backed by footage of `bankers-wrapped.arjunganesh.dev`, not a local dev server.
- [ ] Beat 10's coverage/ADR numbers re-verified against `make test` / `ls docs/adr/*.md` on shoot day, not carried over from an earlier session.
- [ ] Beat 2's GitHub repo scroll shows the current "What Is This?" / "The Problem" text, re-captured if the README changed since this script was written.
