# Brand Cards — README Banners + Demo Video Bookends

This folder holds every hand-authored brand SVG/PNG: the README's hero banner and closing
sign-off, plus the demo video's opening/closing title cards. **The `.svg` files are the single
source of truth** — every PNG here is rendered directly from the corresponding SVG, so there is
one design to edit, not two kept manually in sync:

| File | Use | Format |
| --- | --- | --- |
| `banner-dark.svg` · `banner-light.svg` | README hero (top of page); also the backend's `/docs` Swagger UI banner (`backend/main.py`) | vector, `<picture>` embed |
| `banner-dark.png` · `banner-light.png` | Demo video beat 1 (0:00) — title card | 16:9 (1920×1080), letterboxed, rendered from the `.svg` |
| `banner-dark-native.png` · `banner-light-native.png` | Quick raster reference at the SVG's native size | 1000×410 PNG |
| `signoff-dark.svg` · `signoff-light.svg` | README closing sign-off | vector, `<picture>` embed |
| `signoff-dark.png` · `signoff-light.png` | Demo video beat 10 (~2:25) — brand / thank-you card | 16:9 (1920×1080), letterboxed, rendered from the `.svg` |
| `signoff-dark-native.png` · `signoff-light-native.png` | Quick raster reference at the SVG's native size | 1000×450 PNG |

The 16:9 video cards **letterbox** the SVG (no crop) — the surrounding canvas is filled with the
same background color as the card itself (`#eef0f7` light / `#0a0a0f` dark), so the padding is
invisible and the card just reads as centered on a wider stage. Note: the signoff SVG does **not**
include a GitHub URL line that an earlier, separately-authored version of the video card had —
that was a content difference between two independently-maintained designs, not a rendering bug;
it was dropped intentionally when the video cards were switched to render from the SVG.

See [`submission/DEMO_SCRIPT.md`](../../submission/DEMO_SCRIPT.md) for how the opening/closing
cards are used in the shoot.

The architecture diagram (`assets/architecture/`) is a separate, mermaid-derived asset — see that
folder's own README.

**Which theme?** The app follows the system light/dark setting, and the landing page can be
filmed either way (`DEMO_SCRIPT` reveal beat). **Match the card to the mode you record the app in** —
dark cards if you film in dark mode (default), light cards if you film in light mode. Don't mix.

Built from the app's real brand: the `frontend/public/logo.svg` icon (5 gradient bars + wave arc),
the gradient "WRAPPED" wordmark, real Inter typography, and the exact theme tokens from
`frontend/app/globals.css` (dark `#0a0a0f`; light `#eef0f7` with the darker gradient stops the app
switches to in light mode). Logo tile stays dark in both, exactly as the app renders it. The `.svg`
files themselves reference Inter with system-font fallbacks (`'Inter','Segoe UI',system-ui,...`)
for standalone viewing (e.g. GitHub's README renderer); `banner.html`/`signoff.html` (below) load
real Inter from Google Fonts so the *exported PNGs* get the exact typeface regardless of what's
installed on the machine doing the export.

## Editing the card text / re-rendering the PNGs

Edit the `<text>` elements directly in the `.svg` files — that's the only place the wording lives.
`banner.html` and `signoff.html` are thin, theme-aware preview/export wrappers around the SVGs
(not a separate reimplementation), so there's nothing else to keep in sync. Append `?theme=dark`
or `?theme=light` to the HTML file's URL to force a theme for export; that also hides the on-page
**◐ Toggle theme** button so the render is clean.

- **Preview:** open `banner.html` in any browser (fixed 1920×1080 canvas) and click **◐ Toggle theme**.
- **Re-export both PNG variants per card** (native 1:1 size, and the letterboxed 1920×1080 video
  card) — renders at 2× via headless Edge with real Inter loaded, downscales with ffmpeg for crisp
  text. Under Git Bash on Windows, build the `file:///` URL from a **Windows-style** path
  (`C:/...`), not `$(pwd)` — a POSIX-style `/c/...` path passed inside a `file://` URL string isn't
  auto-translated and Edge reports `ERR_FILE_NOT_FOUND`:

```bash
EDGE="/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
CARDS_WIN="C:/ws/bankers-wrapped/assets/demo-cards"   # adjust to your checkout path
render_2x () {   # html_query  window_w  window_h  target_w  target_h  out_file
  "$EDGE" --headless=new --disable-gpu --hide-scrollbars \
    --force-device-scale-factor=2 --window-size="$2,$3" --virtual-time-budget=4000 \
    --screenshot="$CARDS_WIN/_raw.png" "file:///$CARDS_WIN/$1"
  ffmpeg -y -i "$CARDS_WIN/_raw.png" -vf "scale=$4:$5:flags=lanczos" "$CARDS_WIN/$6"
  rm -f "$CARDS_WIN/_raw.png"
}
for card in banner signoff; do
  h=410; [ "$card" = signoff ] && h=450   # signoff's canvas is taller than banner's
  for theme in dark light; do
    render_2x "$card.html?theme=$theme&native=1" 1000 "$h" 1000 "$h" "$card-$theme-native.png"
    render_2x "$card.html?theme=$theme"          1920 1080 1920 1080 "$card-$theme.png"
  done
done
```

`?native=1` switches the wrapper's canvas from the 1920×1080 letterbox to a 1:1 crop at the SVG's
own size (1000×410 for banner, 1000×450 for signoff) — same file, same source image, just a
different output frame.
