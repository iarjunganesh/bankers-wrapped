# Brand Cards — README Banners + Demo Video Bookends

This folder holds every hand-authored brand SVG/PNG: the README's hero banner and closing
sign-off, plus the demo video's opening/closing title cards. Each pair shares one base name
across formats — the video card is the *same* brand content as the README graphic, just
rendered to a 16:9 PNG instead of a vector `<picture>` embed:

| File | Use | Format |
| --- | --- | --- |
| `banner-dark.svg` · `banner-light.svg` | README hero (top of page) | vector, `<picture>` embed |
| `banner-dark.png` · `banner-light.png` | Demo video beat 1 (0:00) — title card | 16:9 PNG, video timeline |
| `signoff-dark.svg` · `signoff-light.svg` | README closing sign-off | vector, `<picture>` embed |
| `signoff-dark.png` · `signoff-light.png` | Demo video beat 10 (~2:25) — brand / thank-you card | 16:9 PNG, video timeline |

The video cards are separate PNGs (not the `.svg` files directly) because SVGs can't fill a 16:9
frame cleanly and don't import into video editors — see [`submission/DEMO_SCRIPT.md`](../../submission/DEMO_SCRIPT.md)
for how the opening/closing cards are used in the shoot.

The architecture diagram (`assets/architecture/`) is a separate, mermaid-derived asset — see that
folder's own README.

**Which theme?** The app follows the system light/dark setting, and the landing page can be
filmed either way (`DEMO_SCRIPT` reveal beat). **Match the card to the mode you record the app in** —
dark cards if you film in dark mode (default), light cards if you film in light mode. Don't mix.

Built from the app's real brand: the `frontend/public/logo.svg` icon (5 gradient bars + wave arc),
the gradient "WRAPPED" wordmark, real Inter typography (loaded via Google Fonts in `banner.html`/
`signoff.html` — same font the app now self-hosts via `next/font/google`, not a system-font
fallback), and the exact theme tokens from `frontend/app/globals.css` (dark `#0a0a0f`; light
`#eef0f7` with the darker gradient stops the app switches to in light mode). Logo tile stays dark
in both, exactly as the app renders it.

## Editing the video-card text / re-rendering the PNGs

The `.svg` files are hand-authored directly; the video-card `.png` files are rendered from HTML
sources instead (SVG doesn't fill a 16:9 frame or import into video editors). There is **one
theme-aware HTML source per video card** — `banner.html` and `signoff.html`. Each holds **both**
themes (dark tokens by default, `[data-theme="light"]` swaps them), so you edit the wording
**once** and both PNGs stay in sync. Append `?theme=dark` or `?theme=light` to force a theme for
export; that also hides the on-page **◐ Toggle theme** button so the render is clean.

If you edit a video card's wording, keep it in sync with the corresponding `.svg`'s text (they're
meant to say the same thing) — see the SVG files' `<text>` elements directly.

Both HTML sources load real Inter from Google Fonts (`<link>` in `<head>`), so re-exporting needs
network access. `--virtual-time-budget` below gives the webfont request time to land before the
screenshot fires — drop it and you'll silently get the system-font fallback instead.

- **Preview:** open `banner.html` in any browser (fixed 1920×1080 canvas) and click **◐ Toggle theme**.
- **Re-export both PNGs** (renders at 2× via headless Edge, downscales with ffmpeg for crisp text).
  Under Git Bash on Windows, build the `file:///` URL from a **Windows-style** path (`C:/...`), not
  `$(pwd)` — a POSIX-style `/c/...` path passed inside a `file://` URL string isn't auto-translated
  and Edge reports `ERR_FILE_NOT_FOUND`:

```bash
EDGE="/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
CARDS_WIN="C:/ws/bankers-wrapped/assets/demo-cards"   # adjust to your checkout path
for card in banner signoff; do
  for theme in dark light; do
    "$EDGE" --headless=new --disable-gpu --hide-scrollbars \
      --force-device-scale-factor=2 --window-size=1920,1080 \
      --virtual-time-budget=4000 \
      --screenshot=out_2x.png "file:///$CARDS_WIN/$card.html?theme=$theme"
    ffmpeg -y -i out_2x.png -vf scale=1920:1080:flags=lanczos "$card-$theme.png"
  done
done
```
