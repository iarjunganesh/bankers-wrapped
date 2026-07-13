# Architecture Diagram — Brand-Themed Render

The README's architecture diagram, rendered from mermaid source into brand-themed SVG/PNG
(dark + light), matching the treatment of `assets/demo-cards/banner-{dark,light}.svg` /
`signoff-{dark,light}.svg` — same font, same page background tokens — rather than GitHub's
generic mermaid theme.

| File | Use |
| --- | --- |
| `architecture-diagram.mmd` | Source of truth — edit this, not the SVGs/PNGs directly |
| `architecture-diagram-dark.svg` · `architecture-diagram-light.svg` | README embed (`<picture>`, theme-matched) |
| `architecture-diagram-dark.png` · `architecture-diagram-light.png` | Demo video Step 0 flash-cut asset (`submission/DEMO_SCRIPT.md` beat 5) — pre-built, no manual screenshot needed |
| `architecture-diagram-dark.config.json` · `architecture-diagram-light.config.json` | `mermaid-cli` theme variables (background, font, line/text color) per mode |

**Layout note:** the subgraph forces `direction LR` (mermaid-cli's bundled renderer defaults
subgraphs to top-to-bottom otherwise, unlike GitHub's own renderer) and a `PL -.-> A1` link pins
the top summary row (User → FastAPI → Agent Pipeline → B2) above the dotted drill-down, instead
of leaving relative placement to the layout engine's default guess.

## Regenerating

Keep `architecture-diagram.mmd`'s node/edge structure in sync with the copy embedded in
`README.md`'s "Architecture" section if either one changes, then re-render both themes:

```bash
cd assets/architecture
npx --yes -p @mermaid-js/mermaid-cli mmdc -i architecture-diagram.mmd \
  -o architecture-diagram-dark.svg -b "#0a0a0f" -c architecture-diagram-dark.config.json --scale 3
npx --yes -p @mermaid-js/mermaid-cli mmdc -i architecture-diagram.mmd \
  -o architecture-diagram-light.svg -b "#eef0f7" -c architecture-diagram-light.config.json --scale 3
npx --yes -p @mermaid-js/mermaid-cli mmdc -i architecture-diagram.mmd \
  -o architecture-diagram-dark.png -b "#0a0a0f" -c architecture-diagram-dark.config.json --scale 3
npx --yes -p @mermaid-js/mermaid-cli mmdc -i architecture-diagram.mmd \
  -o architecture-diagram-light.png -b "#eef0f7" -c architecture-diagram-light.config.json --scale 3
```

Do **not** pass `-w`/`-H` (fixed width/height) — that pads the canvas to the requested size
instead of fitting it to the actual diagram content, leaving large dead space. Use `--scale` only,
which raises pixel density while auto-fitting to content.
