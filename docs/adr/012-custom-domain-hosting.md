# ADR-012: Custom Domain for the Frontend (`bankers-wrapped.arjunganesh.dev`)
**Status:** Accepted (live 2026-07-25) | **Date:** 2026-07-25

## Context
The frontend was hosted on Vercel's default project subdomain
(`bankers-wrapped.vercel.app`). The project owner has a personal domain
(`arjunganesh.dev`, registered and DNS-managed on Vercel under the same team)
and wanted the submission-facing URL to live under it instead, ahead of the
final judging push.

## Decision
Attach `bankers-wrapped.arjunganesh.dev` to the `bankers-wrapped` Vercel
project as an additional production domain (`vercel domains add
bankers-wrapped.arjunganesh.dev bankers-wrapped`), rather than moving the
apex `arjunganesh.dev` itself — the apex stays on the existing `portfolio`
project. The Railway API keeps its default `*.up.railway.app` domain
unchanged; only the frontend moved.

`CORS_ALLOW_ORIGINS` on the Railway API was previously **unset** (defaulting
to the code's `["*"]` fallback in `backend/config.py` — permissive, not
scoped to any origin). Set explicitly to
`["https://bankers-wrapped.arjunganesh.dev","https://bankers-wrapped.vercel.app"]`
so the frontend's direct browser-side `fetch`/`EventSource` calls to the
Railway API (see `frontend/app/page.tsx` — `NEXT_PUBLIC_API_URL`, not proxied
through Vercel's `vercel.json` rewrite) are correctly scoped to real origins
instead of relying on the wildcard.

## Verification (2026-07-25)
- `vercel domains verify bankers-wrapped.arjunganesh.dev` → `configured-correctly`, attached and verified for the `bankers-wrapped` project, no conflicts.
- `curl -I https://bankers-wrapped.arjunganesh.dev/` → `200`.
- `curl https://bankers-wrapped-api-production.up.railway.app/api/v1/health` → `200` after a Railway redeploy picked up the new `CORS_ALLOW_ORIGINS`.
- CORS preflight (`OPTIONS` with `Origin: https://bankers-wrapped.arjunganesh.dev`) against the Railway API → `access-control-allow-origin: https://bankers-wrapped.arjunganesh.dev`.
- Both existing pinned demo sessions' share pages resolve on the new domain: `/recap/2e6bdb3d-228f-456c-971e-9855274b0d54` and `/recap/84cdf98f-b8ce-457a-969f-724cf116c130` → `200`.

## Consequences
- `bankers-wrapped.vercel.app` still resolves and is kept in
  `CORS_ALLOW_ORIGINS` as a fallback during the cutover — not removed by this
  change.
- The Railway API's CORS policy is now explicit instead of implicitly
  wildcard-open — a small production-hardening side effect of this move, not
  its primary purpose.
- No pipeline/session data changed — B2 remains the source of truth (ADR-008)
  regardless of which frontend domain requests it.

## Alternatives considered
- Moving the apex `arjunganesh.dev` itself to the `bankers-wrapped` project —
  rejected: the apex already serves the owner's portfolio site.
- Also giving the Railway API a custom subdomain (e.g.
  `api.bankers-wrapped.arjunganesh.dev`) — deferred; out of scope for this
  change, no judging-facing benefit over the existing Railway URL.
