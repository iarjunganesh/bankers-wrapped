# Demo Video — Shooting Script (≤ 3 min)

> **Target 2:45** (hard cap 3:00) · public on YouTube · **no copyrighted music** · 1080p screen capture.
> Record the pipeline live, then **jump-cut the ~2–3 min generation wait** so the final cut stays tight.
> Two runs are pre-generated and validated if you prefer to demo against ready results:
> **CSV** `d5b45acf…` and **Plaid** `481ede61…` (see [`assets/README.md`](../assets/README.md)).

**Every criterion is earned on screen** — the mapping:

| Beat | Criterion it scores |
| --- | --- |
| Plaid "Connect a bank" + CSV | Real-World Utility (zero-friction ingestion, clear market) |
| Live SSE pipeline · Genblaze routing | Genblaze Usage (3 of 4 AI steps) |
| B2 console · `generation.json` · redeploy-survives | B2 Storage & Orchestration |
| CI/coverage/ADRs/rate-limit tag | Production Readiness |

---

## Recording workflow (OBS)

Same approach that worked for the argus demo — **record silent screen b-roll, then lay the pre-made voiceover under it in the editor**. You never narrate live.

1. **Record the screen** in OBS (mic OFF — the narration is already generated).
2. **Voiceover is ready:** [`assets/demo-voiceover/`](../assets/demo-voiceover/) — nine `nova` clips (`vo_01…vo_09`, ~1:37 total) matching the beats below.
3. **Sync in your editor:** drop each `vo_NN` clip on the timeline, then trim/speed the screen footage under it to match the clip length.
4. **Export 1080p**, upload public to YouTube.

**OBS settings** — Base + Output **1920×1080**, **30 fps**, cursor **visible**; **Display Capture** (or Window Capture of the browser); **microphone disabled**; MP4 (or MKV → remux) at ~12–16 Mbps; set a **Start/Stop hotkey** so you never film the OBS window.

**Mouse discipline** (what makes it read as polished) — move **deliberately**, click **confidently**, **pause** on anything a judge should read. Avoid rapid scrolling, excess cursor motion, hovering, and repeated tab-switching.

## Browser tabs — open & pre-navigate before recording

Clean browser profile, 100% zoom, bookmarks bar hidden, notifications off, **already logged into Backblaze** (no login screen on camera).

1. **App (fresh):** `https://bankers-wrapped.vercel.app` — ready to click "Connect a bank" · **→ beats 2–5** (reveal, Plaid, live SSE, recap plays)
2. **CSV share page (good numbers):** `https://bankers-wrapped.vercel.app/recap/d5b45acf-3094-42b6-9147-4f0d236f4d95` · **→ beat 6** (14-file artifact list — use this run for on-screen numbers, *not* the Plaid run)
3. **B2 console — pre-open `generation.json`:** bucket `bankers-wrapped-assets` → `d5e87bd9-…/d5b45acf-…/pipeline/generation.json` (so the `llm` block + SHA-256 list is one click away) · **→ beat 6**
4. **GitHub README:** `https://github.com/iarjunganesh/bankers-wrapped` (CI badge, coverage, 11 ADRs) · **→ beat 8**
5. *(optional)* **Codecov:** `https://codecov.io/gh/iarjunganesh/bankers-wrapped` · **→ beat 8**

Keep `data/synthetic/transactions_jan_2026.csv` handy if you also want to show the CSV drag-drop.

---

## Script

> **How to read the timings.** The `[m:ss–m:ss]` ranges below are *approximate target positions* in the final cut — **not clip lengths**. Your real material is the **1:36 narration spine** (nine `vo_NN` clips) padded with silent screen action. The **authoritative timing is the Cut sheet** near the end (measured clip durations; lands ~2:24). If a beat's range looks longer than its VO clip, the gap is **silent b-roll** (navigation, the recap playing, pauses) — not more talking.

**[0:00–0:12] · Hook — the problem**
*On screen:* a raw bank-statement transaction table (boring, endless rows). Slow scroll.
> "This is how your bank shows you a year of your life. A spreadsheet nobody opens twice. Spotify turned the same kind of data into a story forty million people *shared*. Banking never did — until now."

**[0:12–0:25] · Reveal + brand**
*On screen:* cut to the Banker's Wrapped landing page (light or dark — your call), logo + "Your financial year, told as a story."
> "Banker's Wrapped turns a transaction history into a personalized, narrated recap video — generated, stored, and served end-to-end."

**[0:25–0:45] · Ingestion — the wow (Utility)**
*On screen:* click **"🏦 Connect a bank (sandbox)"** → Plaid Link opens → search → **First Platypus Bank** → `user_good` login → select accounts. (Don't dwell — 3–4 fast cuts.)
> "No CSV export, no setup. One click connects a bank through Plaid — the same rails real fintechs use. Prefer a file? Drag in a CSV and you're on the exact same pipeline."

**[0:45–1:10] · The pipeline, live (Genblaze)**
*On screen:* the 7-step SSE progress tracker running, per-step latency ticking, "Writing narrative script — 6s" visible.
> "Behind it: four AI agents. One parses and analyzes your money and assigns a financial personality. The next writes a five-scene script — that's Genblaze, routed to GMI Cloud, with an automatic NVIDIA fallback. Then Genblaze generates every scene image and the voiceover. Three of the four AI steps run through Genblaze — nothing calls a provider directly."

**[~1:10] · The payoff — the recap (Utility)**
*On screen:* the finished MP4 plays. **The recap is on screen ~10–13 s total — not 30.** Let the product's **own narration audio play alone for ~5 s** (personality badge, scene transitions, the numbers), *then* bring `vo_05` in over the top and duck the recap audio under it.
> *(let the recap's voice breathe ~5 s, then `vo_05`, lower:)* "A financial personality, five cinematic scenes, a real voice — a recap you'd actually send a friend."

**[1:40–2:05] · B2 as the source of truth (Storage)**
*On screen:* click **Share** → the public `/recap/{id}` page → expand the 14-file artifact list → cut to the **Backblaze B2 console** → open `generation.json`, highlight the `llm` block (`gmi-cloud`, tokens, cost) and the **SHA-256 per artifact**.
> "Every artifact lives on Backblaze B2 — fourteen files across ten types per session: the video, every image, the audio, and a full provenance manifest with the model, latency, and a SHA-256 for each file. B2 isn't the output bucket. It's the source of truth."

**[2:05–2:20] · Durability punchline (Storage / Production)**
*On screen:* reload the share link (optionally after a redeploy) — it still plays.
> "Redeploy the backend, and every share link still works — because the session lives on B2, not in server memory."

**[2:20–2:35] · Production readiness (rapid-fire)**
*On screen:* quick montage — green CI badge, 99% coverage, the ADR list, rate-limit / health endpoint.
> "Ninety-nine percent test coverage, CI/CD, rate limiting, eleven architecture decision records. Not a prototype — a system you could ship."

**[2:35–2:50] · Close**
*On screen:* brand card, tagline, Genblaze + B2 logos.
> "One connection. Five scenes. Your financial story — powered by Genblaze on Backblaze B2. That's Banker's Wrapped."

---

## Cut sheet — real clip durations (authoritative timing)

Measured clip lengths (ffprobe) + realistic silent b-roll padding. Lays the **1:36 narration spine** against the screen action and lands **~2:24** — comfortably under the strict **3:00** cap.

| # | Beat | Tab | VO clip (measured) | + silent b-roll | Ends at |
| --- | --- | --- | --- | --- | --- |
| 1 | Hook — statement table | title / statement | `vo_01-hook` (12.2s) | +2s | 0:14 |
| 2 | Reveal — landing page | App | `vo_02-reveal` (7.8s) | +2s | 0:24 |
| 3 | Ingestion — Plaid clicks | App | `vo_03-ingestion` (10.3s) | +6s | 0:40 |
| 4 | Pipeline — SSE (jump-cut the wait) | App | `vo_04-pipeline` (22.0s) | +8s | 1:10 |
| 5 | **Payoff — recap plays** | App | 5s recap-audio + `vo_05-payoff` (6.0s) | — | 1:23 |
| 6 | B2 — share list → console → `generation.json` | Share → B2 | `vo_06-b2` (16.2s) | +10s | 1:49 |
| 7 | Durability — reload share link | Share | `vo_07-durability` (6.9s) | +4s | 2:00 |
| 8 | Production — CI/coverage/ADRs | GitHub | `vo_08-production` (8.1s) | +6s | 2:14 |
| 9 | Close — brand card | close card | `vo_09-close` (6.9s) | +3s | ~2:24 |

**Narration spine ≈ 1:36** (`vo_full-reference.mp3` = the whole track). The padding above is **silent screen action** (navigation, the recap playing, pauses) — *not more narration* — and it's what carries the cut to ~2:24. If you run long, trim the pipeline beat (jump-cut the generation wait) and the B2 browse. **Never hold a static frame > ~15 s** under continuous narration, and **never cross 3:00**.

### Assembly (Clipchamp on Win11, or CapCut)

1. **Build the audio spine first** — drop all nine `vo_NN` clips on the audio track in order, leaving small gaps for the silent action (Plaid clicks, recap playing, B2 browse). This *defines the length* — watch it stay under ~2:45.
2. **Record screen b-roll in OBS, mic OFF** — one pass following the tab order below, jump-cutting the ~3-min generation wait.
3. **Lay footage over the spine**, trimming each section to its clip + gap.
4. **Payoff only:** don't mute the recap clip — let its audio play ~5 s, then duck it under `vo_05`.
5. **Export 1080p → upload public to YouTube.**

## Opening / closing cards

> **Pre-built and ready:** [`assets/demo-cards/`](../assets/demo-cards/) has these as **1920×1080 PNGs** (dark + light variants).
> **Add them in the editor as the first and last clips — do NOT record them in OBS** (opening a card as a
> browser tab shows the browser chrome around it). Pick the variant matching the theme you film the app in.
> Cards live in the editor; the App / B2 / GitHub tabs are the OBS-captured footage.

**Opening (0:00)** — either the boring statement table (stronger hook) or a title card:
> **Banker's Wrapped** — Your financial year, told as a story · Backblaze Generative Media Hackathon 2026

**Closing (2:35)** — brand card:
> **Banker's Wrapped**
> One connection. Five scenes. Your financial story.
> *Powered by Genblaze on Backblaze B2*

---

## Production checklist

- [ ] Record at 1920×1080; hide bookmarks/personal tabs; use a clean browser profile.
- [ ] Jump-cut the generation wait (progress bar → result); total cut **≤ 3:00**.
- [ ] Captions/subtitles on (accessibility + judges often watch muted first).
- [ ] Music: silence, or a license-free bed only. **No copyrighted tracks** (rules).
- [ ] Upload **public** (not unlisted) to YouTube; paste the URL into README (badge + links row) and SUBMISSION/DEVPOST.
- [ ] Watch once at 1.0× end-to-end to confirm nothing reads as broken (avoid featuring Plaid's random-sandbox stats — use the CSV run for on-screen numbers).
