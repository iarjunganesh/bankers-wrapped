# Demo Video — Opening / Closing Cards

Title and end cards for the ≤3-min submission video (`submission/DEMO_SCRIPT.md`, beats 1 and 10).
Ready-to-use **1920×1080 PNGs** — drop straight onto the video timeline; no export step.

> **These are the video cards, not the README banners.** The repo README uses separate vector
> banners (`assets/banner-{light,dark}.svg`, `assets/signoff-{light,dark}.svg`). These 16:9 PNGs
> exist because SVGs can't fill a 16:9 frame and don't import into video editors.

| File | Use |
| --- | --- |
| `opening-card-dark.png` · `opening-card-light.png` | Beat 1 (0:00) — title card |
| `closing-card-dark.png` · `closing-card-light.png` | Beat 10 (~2:25) — brand / thank-you card |

**Which theme?** The app follows the system light/dark setting, and the landing page can be
filmed either way (`DEMO_SCRIPT` reveal beat). **Match the card to the mode you record the app in** —
dark cards if you film in dark mode (default), light cards if you film in light mode. Don't mix.

Built from the app's real brand: the `frontend/public/logo.svg` icon (5 gradient bars + wave arc),
the gradient "WRAPPED" wordmark, Inter/Segoe typography, and the exact theme tokens from
`frontend/app/globals.css` (dark `#0a0a0f`; light `#eef0f7` with the darker gradient stops the app
switches to in light mode). Logo tile stays dark in both, exactly as the app renders it.

## Editing the text / re-rendering

There is **one theme-aware source per card** — `opening-card.html` and `closing-card.html`. Each holds
**both** themes (dark tokens by default, `[data-theme="light"]` swaps them), so you edit the wording **once**
and both PNGs stay in sync. Append `?theme=dark` or `?theme=light` to force a theme for export; that also
hides the on-page **◐ Toggle theme** button so the render is clean.

- **Preview:** open `opening-card.html` in any browser (fixed 1920×1080 canvas) and click **◐ Toggle theme**.
- **Re-export both PNGs** (renders at 2× via headless Edge, downscales with ffmpeg for crisp text):

```bash
EDGE="/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
for card in opening-card closing-card; do
  for theme in dark light; do
    "$EDGE" --headless=new --disable-gpu --hide-scrollbars \
      --force-device-scale-factor=2 --window-size=1920,1080 \
      --screenshot=out_2x.png "file:///$(pwd)/$card.html?theme=$theme"
    ffmpeg -y -i out_2x.png -vf scale=1920:1080:flags=lanczos "$card-$theme.png"
  done
done
```
