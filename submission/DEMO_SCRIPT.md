# Demo Video — Shooting Script (≤ 3 min)

> **Target 2:50–2:55** (hard cap 3:00) · public on YouTube · **no copyrighted music** · 1080p.
> **One live OBS take, one 15-second evidence take, and stills** — see **Recording #1**, **Recording #2**, and **Stills** below. The live pipeline run is captured once, separately, then jump-cut clips from it are dropped into the edit. Every screen whose job is simply *to be read* is a high-resolution still with a slow move applied in the editor: sharper text than screen capture, and free to redo.
> Fallback if the live run fails and you don't want to spend more GMI credit: the pre-generated
> **CSV** run `2e6bdb3d…` (see [`assets/README.md`](../assets/README.md)). The pre-generated
> **Plaid** run `84cdf98f…` is *evidence only* — never use its numbers on screen (see Honesty rules).

**Every criterion is earned on screen** — the mapping:

| Beat | Criterion it scores |
| --- | --- |
| Plaid "Connect a bank" + CSV | Real-World Utility (zero-friction ingestion, clear market) |
| Architecture diagram · Live SSE pipeline · Genblaze routing | Genblaze Usage (3 of 4 AI steps) |
| B2 console · `generation.json` · redeploy-survives | B2 Storage & Orchestration |
| CI/coverage/ADRs/rate-limit tag | Production Readiness |

---

## Why one live take, one short take, and stills

The live pipeline run takes ~90–120 seconds and spends real GMI credit, so it is captured once and
mined for clips. But most of the rest of this video isn't motion at all — it's screens a judge is
meant to *read*: a README, a CSV, a B2 folder listing, a JSON file. Filming those as video buys
nothing and costs sharpness, because 30 fps H.264 smears exactly the small text you need legible.

So the shoot splits three ways:

- **Recording #1 — Live Pipeline**, shot as two takes: **#1a** the Plaid connect flow (free — cancelled before the exchange) and **#1b** the real CSV pipeline run start to finish. Beats 5, 6, and 7 are cut out of these. #1b is the only take that costs money.
- **Recording #2 — Durability** (OBS, ~15 seconds): the share page being reloaded. This is the one remaining beat where the motion itself *is* the evidence — no still can show that a page reloaded and still played.
- **Stills** (screenshots plus a slow move in the editor): beats 1, 2, 3, 4, 8, 10, 11. Crisper text than video capture, no fumbled mouse, and re-doable at zero cost.

**What stills cost you, and why it's an acceptable trade**: a still has no cursor, so nothing in
those beats reads as "someone is operating this right now." That's fine for beats whose job is
*evidence* — the artifact list, the B2 console, the ADR list — but would be fatal for beats whose
job is *proof of life*. Which is exactly why the live pipeline (beats 5–7) and the reload (beat 9)
stay as video. Don't let stills creep into those four beats.

**Shared OBS settings for both recordings** — Base + Output **1920×1080**, **30 fps**, cursor **visible**; **Display Capture** (or Window Capture of the browser); **microphone disabled** (mic OFF — narration is pre-generated, you never narrate live); MP4 (or MKV → remux) at ~12–16 Mbps; set a **Start/Stop hotkey** so you never film the OBS window.

**Audio**: mic is OFF for both takes, no exceptions. **Desktop/system audio must stay ON for Recording #1** — the recap video autoplays with sound at the end of the live run, and beat 7 (payoff) needs that captured audio to duck `vo_05` under. **Recording #2 needs system audio ON too** if you play the video after reloading; otherwise it can be silent.

**Mouse discipline** in both OBS takes (what makes it read as polished) — move **deliberately**, click **confidently**, **pause** on anything a judge should read. Avoid rapid scrolling, excess cursor motion, hovering, and repeated tab-switching.

---

## Step 0 — one-time prep, before recording anything

1. **Architecture diagram**: already built and ready at [`assets/architecture/`](../assets/architecture/) — `architecture-diagram-{dark,light}.png`, brand-themed (no GitHub screenshot needed). Used **exactly once**, in the editor, at beat 6 — you never show this diagram live in either OBS recording. Note it is **2352×450**, a wide strip rather than 16:9: fit it to the frame *width* and hold it static (see Motion direction for why it must not be zoomed).
2. **Opening/closing cards**: already built and ready at [`assets/demo-cards/`](../assets/demo-cards/) — `banner-{dark,light}.png` (opening) and `signoff-{dark,light}.png` (closing), exactly 1920×1080. These are inserted directly in the editor as the first/last clips — **do not record them in OBS** (a browser tab around them would show browser chrome).
3. **Pick one theme and hold it** — dark or light — across the app, the cards, and the diagram. Every committed asset ships in both variants; mixing them mid-video reads as an accident.
4. **Capture the stills** — see the [Stills](#stills--capture-list) section below. Do this before you open the editor, so assembly is one uninterrupted pass.
5. Clean browser profile, bookmarks bar hidden, notifications off, **already logged into Backblaze** (no login screen on camera), and **close every tab you aren't filming** — a row of unrelated tabs is the single most common thing that makes a demo look unrehearsed.

---

## Recording #1 — Live Pipeline (record this first, by itself)

Shot as **two separate takes**: `1a` shows the Plaid ingestion path and is free (you cancel before
the exchange, so no pipeline runs); `1b` is the actual pipeline run via CSV and is the only thing
in this entire shoot that spends GMI credit. Splitting them means you can retake the Plaid half as
often as you like without touching the reserve.

> **Why the run is CSV, not Plaid** — Plaid's sandbox fixture is the same for every institution
> and is internally incoherent (it reports the GUSTO payroll credit as an *outflow*), which makes
> the recap render an impossible 1358% savings rate. See the Honesty rules. The CSV path produces
> a coherent story: $13,850 income, $4,352.38 expenses, 8.7% savings, Financial Builder.

**Both takes must match visually** — same window size, same page zoom, same theme, same tabs — or
the cut between them inside beat 5 will jump. Set the window up once and don't touch it between takes.
In both, confirm the address bar reads **`arjunganesh.dev`**, not `vercel.app`.

### Recording #1a — Plaid connect (free, retake freely)

System audio not needed; nothing plays.

1. Open `https://bankers-wrapped.arjunganesh.dev`, fresh, nothing clicked.
2. Start OBS.
3. Click **"🏦 Connect a bank (sandbox)"**, search for and select **"First Platypus Bank"**, log in
   with username `user_good`, and let it show the account list.
4. **Close the Plaid dialog without clicking Continue.** Continue triggers the exchange and a paid
   run, and you do not want a Plaid-derived recap.
5. Stop OBS. Save as `plaid-connect-take.mp4`.

### Recording #1b — CSV pipeline run (the one paid take)

**System audio ON** — beat 7 needs the recap's own audio to duck `vo_05` under.

1. Same window, back on the home screen.
2. Start OBS.
3. Start a run from the CSV path — **"Try demo dataset"** or drag in
   `data/synthetic/transactions_jan_2026.csv`. This is the one time you spend real money
   (~$0.15 in GMI credits — the measured per-run cost; see `submission/COSTS.md`).
4. Don't touch anything while it runs. The progress tracker advances through parsing → analyzing →
   writing script → generating scene images → composing video → uploading.
5. Wait for the recap video to start playing automatically, then let it play through once with the
   personality badge and stats on screen.
6. Stop OBS. Save as `csv-run-take.mp4`.

**Before you cut anything, sanity-check the result page**: savings rate should read around **8.7%**
and expenses should be below income. If you see 1358%, you started the run from the wrong path.

---

## Recording #2 — Durability reload (OBS, ~15 seconds)

The one beat left that has to be motion. **Skip this section entirely if you aren't airing beat 9** —
see Honesty rules; it only airs if you actually redeployed.

1. Trigger a real Railway redeploy and wait for the backend to come back up.
2. Open `https://bankers-wrapped.arjunganesh.dev/recap/2e6bdb3d-228f-456c-971e-9855274b0d54`.
3. Start OBS. Keep the **URL bar in frame** — it's what makes this beat mean anything.
4. Click reload. Let the page fully repaint: thumbnail, personality badge, stats, artifact list.
5. Press play and let the video run 2–3 seconds.
6. Stop OBS. Save as `durability-take.mp4`.

*Optional, only if you'd rather show live navigation than the committed B2 screenshots in beat 8*:
keep recording and browse the B2 console from the bucket root down into
`4d0f560b-…/2e6bdb3d-…/pipeline/` until `generation.json` is visible. A live drill-down is more
convincing than four stills of the same path — and it's also four more chances to fumble. Either is
defensible; pick one and don't mix both inside the same beat.

---

## Stills — capture list

Two capture types, and the difference decides whether a still can move:

- **Type A — page capture** (no browser chrome, high resolution, pannable). In Edge/Chrome:
  `Ctrl+Shift+M` for the device toolbar → set a **viewport width** (see below) and **DPR 2** →
  `Ctrl+Shift+P` → **"Capture full size screenshot"**. You get a full-page-tall PNG at twice the
  viewport width. Shown at 1920 in the frame it's a clean downscale — visibly sharper than any
  screen recording — and the spare height is what a slow vertical pan spends.
- **Type B — window capture** (native 1920×1080, **includes the URL bar**). `Win+Shift+S`, or a
  single OBS frame. Use only where the live domain has to be visible. No spare pixels, so these are
  held static.

| Still | Beat | Type | What to capture | Move |
| --- | --- | --- | --- | --- |
| `s01-repo-top.png` | 2 | A | `github.com/iarjunganesh/bankers-wrapped`, **full-page capture** (1920×12476 — native frame width, so the pan renders 1:1 with no rescaling). The pan is **pre-rendered** to `assets/demo-video/beat02-repo-pan.mp4` — drop that in, don't re-do the move by hand | (baked into the clip) |
| `s02-csv` | 3 | A | `data/synthetic/transactions_jan_2026.csv` as GitHub renders it (crisp and pannable). Fallback: an Excel window as Type B, held static | Slow vertical pan down the rows |
| `s03-app-home` | 4 | **B** | `bankers-wrapped.arjunganesh.dev` home screen, **URL bar visible**, nothing clicked | Static hold |
| `s04-artifact-list` | 8 | *committed* | [`2e6bdb3d_04-app-b2-artifact-list.png`](../assets/csv-run/2e6bdb3d/screenshots/2e6bdb3d_04-app-b2-artifact-list.png) | Static hold |
| `s05-b2-pipeline` | 8 | *committed* | [`2e6bdb3d_09-b2-pipeline-folder.png`](../assets/csv-run/2e6bdb3d/screenshots/2e6bdb3d_09-b2-pipeline-folder.png) | Static hold |
| `s06-b2-generation` | 8 | *committed* | [`2e6bdb3d_10-b2-generation-json-details.png`](../assets/csv-run/2e6bdb3d/screenshots/2e6bdb3d_10-b2-generation-json-details.png) | Static hold |
| `s07-evidence-json` | 8 | A | The committed `generation.json` on GitHub — `"llm"` block through the SHA-256 list | Slow pan from `llm` down to the hashes |
| `s08-badges` | 10 | A | README badge rows (CI, coverage, release, licence) | Static hold |
| `s09-adrs` | 10 | A | README ADR list (sits just under the architecture diagram) | Slow pan down |
| `s10-codecov` | 10 | A | `codecov.io/gh/iarjunganesh/bankers-wrapped` | Static hold |

`s04`–`s06` are **already in the repo** — captured from the real `2e6bdb3d` run and committed as
evidence, so there's nothing to re-shoot and nothing a judge could call staged. They're
1920×947–1059, i.e. **no headroom**: scale to fit and hold static.

**Viewport width when capturing Type A** — this is the setting that decides whether the beat looks
composed or empty. GitHub's README sits in a centred column only ~800 px wide, so captured at a
1920 px viewport it fills under half the frame and reads as a strip of text floating in whitespace.
Capture **GitHub and Codecov pages at a 1200–1280 px viewport** instead: the column then fills the
frame, and at DPR 2 you still get a 2400–2560 px-wide PNG, comfortably above the 1920 you need. The
app's own pages are full-bleed, so capture those at a **1920 px viewport**. Don't also change page
zoom — viewport width alone does the job, and stacking the two makes the result hard to predict.

---

## Motion direction — how to move a still without being annoying

The move exists to keep the frame from looking frozen, **not** to be noticed. If a viewer could
describe the camera move afterwards, it was too big.

- **One move per still. Never combine** a zoom with a pan.
- **Barely perceptible**: a push-in runs **100% → ~105%** across the *entire* clip, never more. A pan
  should take the whole beat to travel its distance.
- **Only move if you have the pixels.** A 1920-wide still in a 1920-wide frame has none, so any zoom
  is an upscale and will look softer than the screen recording you replaced. Type A captures
  (2400–3840 wide) have headroom; Type B, the demo cards (exactly 1920×1080), and the committed B2
  screenshots do not. Those get held static — that's the correct call, not a compromise.
- **The move has to be motivated.** Pan down means "keep reading." Push in means "look at this
  specific thing." Hold means "this is dense, read it." Nothing else earns a move.
- **The architecture diagram is held static** — at 2352×450 it fits the frame *width*, and any
  push-in crops the outer nodes, which are the ones the narration is naming. Set the editor's
  canvas background to `#0a0a0f` (dark) or `#eef0f7` (light) so the bands above and below match the
  diagram's own background and the letterbox is invisible.
- **Cuts**: hard cut between beats. Inside a beat, a 200–300 ms cross-dissolve between stills of the
  same screen family (the three B2 screens) reads as navigation.
- **Banned outright**: spin, bounce or elastic easing, glitch and whip transitions, animated text
  pop-ins, drop shadows on stills, and more than one move per beat. Each of these reads as
  "template" and pulls attention off the thing being claimed.

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
| `vo_08-production` | "Ninety-nine percent test coverage, a hard CI gate, structured logging, and twelve architecture decision records — this isn't a prototype." | 20 | 8.4s |
| `vo_09-close` | "One connection. Five scenes. Your financial story — Banker's Wrapped, built on Genblaze and Backblaze B2." | 16 | 6.3s |

**Narration spine ≈ 1:24** (84.1s measured via ffprobe; `vo_08` re-measured 2026-07-27). `vo_00-intro` names **both**
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
| 1 | Opening card | silent | still — `assets/demo-cards/banner-{dark,light}.png` | Brand card, **static** — it's exactly 1920×1080, so any zoom upscales it | none | 3s | 0:03 |
| 2 | Repo intro: name, tagline, Genblaze + B2 roles, "What Is This?", "The Problem" | `vo_00-intro` (16.4s) | **`beat02-repo-pan.mp4`** (pre-rendered from `s01-repo-top.jpeg`) | Slow vertical drift, already baked in: opens on the wordmark + badge rows, closes on the full "How It Works" list. Deliberately stops before the architecture diagram and ADR table so beats 6 and 10 aren't pre-empted | `Genblaze: sole AI layer · Backblaze B2: source of truth` | 19s | 0:22 |
| 3 | Hook | `vo_01-hook` (3.3s) | still `s02-csv` | Slow vertical pan down the transaction rows — let the numbers register, even past where narration ends | `A CSV isn't a story.` | 9s | 0:31 |
| 4 | Reveal | `vo_02-reveal` (2.7s) | still `s03-app-home` (Type B — URL bar in frame) | Static hold; the visible live URL is the whole point of the beat | `bankers-wrapped.arjunganesh.dev · live` | 7s | 0:38 |
| 5 | Ingestion — both paths | `vo_03-ingestion` (7.3s) | **#1a** `plaid-connect-take.mp4` (~12s): institution search → First Platypus Bank → login → account list; then **#1b** `csv-run-take.mp4` (~8s): the CSV path starting the run | Shows the two doors the narration names, then the one that actually opens this run. Cut away from Plaid on the account list — never imply it produced the recap | `Two ways in — Plaid or CSV. Same pipeline.` | 20s | 0:58 |
| 6 | Architecture + Pipeline live | `vo_04-pipeline` (16.9s) | first 8s: still — `assets/architecture/architecture-diagram-{dark,light}.png`; remaining ~25s: **#1b** `csv-run-take.mp4` — jump-cut 5–6 short (3–5s) clips of the progress tracker across the full run (parsing → scripting → each scene → composing → uploading) | Diagram **static**, fit to frame width, canvas background matched to the diagram's own — then cut to the SSE tracker advancing through the real pipeline stages | `4 agents · Genblaze SDK · GMI Cloud + OpenAI` | 33s | 1:31 |
| 7 | Payoff — recap plays | 5s recap audio + `vo_05-payoff` (4.5s) | **#1b** `csv-run-take.mp4` — the finished recap playing (personality badge + stats are coherent and safe to show) | Let the recap's own audio play longer before ducking — this is the emotional payoff, don't rush it | `Financial Builder · 5 scenes` | 15s | 1:46 |
| 8 | B2 — share list → console → `generation.json` | `vo_06-b2` (12.2s) | stills `s04` → `s05` → `s06` → `s07` | Four screens, ~6.5s each: artifact list, B2 `pipeline/` folder, `generation.json` details, then the readable evidence file. Cross-dissolve (200–300 ms) between the two B2 screens so the drill-down reads as navigation; slow pan on `s07` from `llm` to the hashes | `14 files · 10 types · SHA-256 per artifact` | 26s | 2:12 |
| 9 | Durability — reload share link | `vo_07-durability` (6.1s) | Recording #2 — `durability-take.mp4` | Page reloads with the URL bar in frame, still plays. **Motion, not a still — a still cannot prove this** | `Redeploy-proof — B2 is the source of truth` | 9s | 2:21 |
| 10 | Production — CI/coverage/ADRs | `vo_08-production` (8.4s) | stills `s08` → `s09` → `s10` | Badges held static, then a slow pan down the ADR list (not the diagram — see Step 0), then Codecov held 2–3s | `99% coverage · 12 ADRs · CI on every push` | 16s | 2:37 |
| 11 | Close | `vo_09-close` (6.3s) | still — `assets/demo-cards/signoff-{dark,light}.png` | Brand card held **static** (exactly 1920×1080), live URL fading in over it | `bankers-wrapped.arjunganesh.dev` | 13s | ~2:50 |

Total lands roughly **2:50** — right at the target and comfortably under the 3:00 hard cap.
The pad beyond each measured VO clip is deliberate screen time (Plaid's multi-step flow, more SSE
jump-cuts across the full pipeline run, a longer look through the B2 artifacts, the recap payoff
breathing) — not dead air. If it still runs short in the edit, extend beat 6 (more SSE clips) or
beat 8 (linger longer on `generation.json`) first; if you run long, trim those same two beats first.
**Never hold a static frame > ~15s** under continuous narration — which is the real ceiling on how
long any single still can sit on screen, moving or not.

---

## Assembly (Clipchamp on Win11, or CapCut)

You'll end up with **12 images on the timeline** (opening card, `s02`–`s10`, architecture diagram,
closing card — `s01` isn't placed directly, it's the source of the pre-rendered pan) and **3 video
files** (`beat02-repo-pan.mp4`, `plaid-connect-take.mp4`, `csv-run-take.mp4`), plus
`durability-take.mp4` if you're airing beat 9. Set the project canvas background
to `#0a0a0f` (dark) or `#eef0f7` (light) *before* laying anything down, so every letterboxed still
sits on matching colour instead of default black. Then build in this order:

| # | Beat | Source | Move |
| --- | --- | --- | --- |
| 1 | 1 | `banner-{dark,light}.png` | static |
| 2 | 2 | **`beat02-repo-pan.mp4`** (pre-rendered, exactly 19s) | pan baked in — drop on timeline as-is |
| 3 | 3 | `s02-csv` | pan down |
| 4 | 4 | `s03-app-home` | static |
| 5 | 5a | **plaid-connect-take.mp4** — Connect-a-bank clicks through login and account list, stopping before "Continue" | native |
| 5b | 5b | **csv-run-take.mp4** — the CSV path starting the run | native |
| 6 | 6a | `architecture-diagram-{dark,light}.png` | static, fit to width |
| 7 | 6b | **csv-run-take.mp4** — 5–6 short (3–5s) clips of the progress tracker at different moments ("Writing narrative script", "3/5 scenes done", "composing video", "uploading"), skipping the waiting parts | native |
| 8 | 7 | **csv-run-take.mp4** — the finished recap playing | native |
| 9 | 8 | `s04` → `s05` → `s06` → `s07` | static ×3 (cross-dissolve between the B2 pair), pan on `s07` |
| 10 | 9 | **durability-take.mp4** — the reload | native |
| 11 | 10 | `s08` → `s09` → `s10` | static, pan, static |
| 12 | 11 | `signoff-{dark,light}.png` | static |

Then drop the ten `vo_NN` narration clips onto the audio track underneath, matching each one to its
beat. For beat 7 (payoff) specifically: don't mute the recap clip — let its own audio play ~5s, then
duck it under `vo_05`. Add the lower-third overlay text from the beat timeline above, one per beat,
on screen ≤ 4s.

**Edit rhythm**: in the live footage, cut on clicks rather than mid-motion; everywhere else, land
the cut on a narration phrase boundary, never mid-sentence. One move per beat, max, and never hold
a frame longer than the beat's Duration column says. Because most of this timeline is now stills,
the cuts are carrying the pace that a moving cursor used to carry — sloppy cut placement shows up
far more than it would have in a screen recording. Watch the final cut once with **audio off** (the story must survive on picture +
overlays alone) and once with **video off** (the narration must survive alone, without the
overlays) — both have to pass before calling it done.

---

## Honesty rules (what not to imply on screen)

- **Never present pre-generated material as live.** Recording #1 is the only footage allowed to
  stand in for "this is happening right now." The committed runs (`2e6bdb3d`, `84cdf98f`) belong to
  beat 8's *static* artifact/B2/evidence stills, where the pipeline events already happened.
- **Never show a Plaid-derived recap result** (verified 2026-07-27). Plaid's sandbox returns the
  same fixture for *every* institution — the transaction set is bound to the `user_good` test user,
  not the bank — and that fixture is internally incoherent: it reports the
  `ACH Electronic Credit GUSTO PAY` payroll row as `amount=+5850, pfc=TRANSFER_OUT`, i.e. money
  *leaving* the account, while the only inflows it marks are a $4.22 interest payment and a $500
  airline refund. Every institution tested (Canandaigua, Chiphone, Conservation Employees,
  Equitable) yields ~$1,512 income against ~$33,448 expenses and a **1358% savings rate**, and the
  UI duly prints "Saved 1359% of income — well above average". This is Plaid's data, not a bug in
  the connector — the sign handling in `backend/ingest/plaid_connector.py` is correct — so no code
  change and no different bank rescues it. **Plaid appears in beat 5 as a connect flow only** (no
  numbers on screen); the recap shown from beat 6 onward always comes from a CSV run.
- **`vo_05` says "Financial Builder" out loud.** The synthetic CSV reliably classifies as Financial
  Builder (8.7% savings rate), so this should hold — but glance at the badge on the result page
  before cutting beat 7. If it differs, re-run `scripts/generate_demo_voiceover.py --beat payoff`
  with the correct name and re-paste the measured duration.
- **Stills are honest; a still implying motion is not.** A high-resolution screenshot of the real
  hosted app, the real B2 console, or a committed evidence file is exactly as truthful as filming
  the same screen — nothing is being staged. What's not allowed is using a still where the *change*
  is the claim, which is the entire reason beat 9 stayed on video.
- **The redeploy-durability beat (9) only airs if actually demonstrated** — if you skip
  triggering a real Railway redeploy before filming, cut this beat rather than showing a page
  refresh and implying redeploy-survival without having actually redeployed.
- **The 99% coverage / 12 ADR claims in beat 10 must match what `make test` and `ls docs/adr/`
  actually report on shoot day** — re-verify both numbers immediately before recording, not from
  memory of an earlier run (see `CLAUDE.md`'s version-sync policy). *(Resolved 2026-07-27:
  `vo_08` previously said "eleven" against 12 ADRs on screen; regenerated to "twelve", 8.4s.)*
- **The GitHub repo intro beat (2) must show the actual current README** — if "What Is This?" or
  "The Problem" text changes before shoot day, re-screenshot/re-scroll rather than filming a
  stale version of the page.
- Every "live" claim in the narration (vo_02, vo_04, vo_07) must be backed by footage of the
  actual hosted app at `bankers-wrapped.arjunganesh.dev` — never a local dev server standing in.

---

## Production checklist

- [ ] Record at 1920×1080; hide bookmarks/personal tabs; close every tab not being filmed; clean browser profile.
- [ ] Recording #1a (Plaid connect) done — cancelled before "Continue", so no credit spent; retake freely.
- [ ] Recording #1b (CSV run) done once — only re-record if something goes visibly wrong, since each run spends GMI credit.
- [ ] #1a and #1b shot at the same window size / zoom / theme so the beat-5 cut doesn't jump.
- [ ] Recording #2 (Durability, ~15s) done *after* a real Railway redeploy — or beat 9 cut entirely.
- [ ] All ten stills captured: `s01`–`s03` and `s07`–`s10` fresh, `s04`–`s06` pulled from the committed `assets/csv-run/2e6bdb3d/screenshots/`.
- [ ] Beat 2's pan starts on the README banner, not on the repo file listing above it.
- [ ] Every still is either Type A (has pan headroom) or held static — no still is zoomed without spare pixels.
- [ ] One theme held throughout — app, cards, and diagram all dark or all light, never mixed.
- [ ] Editor canvas background set to `#0a0a0f` / `#eef0f7` so letterboxed stills sit on matching colour, not black.
- [ ] No still that lacks spare pixels has a zoom on it (demo cards, `s03`, `s04`–`s06`, architecture diagram are all static).
- [ ] Architecture diagram used only at beat 6, fit to frame width, held static.
- [ ] Live-run personality matches `vo_05`'s "Financial Builder" — otherwise beat 7 footage swapped or VO re-generated.
- [ ] Jump-cut the generation wait in beat 6 (progress bar → result); total cut **≤ 3:00**.
- [ ] Captions/subtitles on (accessibility + judges often watch muted first).
- [ ] Music: silence, or a license-free bed only. **No copyrighted tracks** (rules).
- [ ] Upload **public** (not unlisted) to YouTube; paste the URL into README (badge + links row) and SUBMISSION/DEVPOST.
- [ ] Address bar reads `bankers-wrapped.arjunganesh.dev` in **every** frame that shows it — no `vercel.app`.
- [ ] The recap shown from beat 6 onward came from the **CSV** path; the Plaid dialog was cancelled before Continue.
- [ ] Result page sanity-checked before editing: savings rate plausible, expenses below income (not the 1358% Plaid figure).
- [ ] Watch once at 1.0× end-to-end to confirm nothing reads as broken.
- [ ] Lower-third overlays present for every beat that specifies one (see Final beat timeline), each on screen ≤ 4s.
- [ ] Watched once with audio off (story survives on picture + overlays alone) and once with video off (narration survives alone).
- [ ] Every "live" claim in the narration is backed by footage of `bankers-wrapped.arjunganesh.dev`, not a local dev server.
- [ ] Beat 10's coverage/ADR numbers re-verified against `make test` / `ls docs/adr/*.md` on shoot day, not carried over from an earlier session.
- [ ] Beat 2's GitHub repo scroll shows the current "What Is This?" / "The Problem" text, re-captured if the README changed since this script was written.
