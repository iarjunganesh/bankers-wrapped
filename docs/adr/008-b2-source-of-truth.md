# ADR-008: Backblaze B2 as the Session Source of Truth
**Status:** Accepted (implemented in v1.7.0 WS-2) | **Date:** 2026-06-30

## Decision
Persist a complete, self-contained **session manifest** to B2 at
`{user_id}/{session_id}/metadata/session_metadata.json` (insights + `b2_keys` + timings +
personality). On read, `GET /recap/{id}` uses SQLite as a fast cache but **falls back to the B2
manifest** when the row is missing. SQLite becomes a cache, not the system of record.

## Rationale
- Railway's filesystem is ephemeral — SQLite (ADR-004) is wiped on redeploy, so share links and
  notebook Scenario C 404 after a deploy. B2 is already durable and already stores everything.
- Makes B2 the orchestration backbone, not just an output bucket — directly strengthens the
  "B2 Storage & Data Orchestration" criterion.
- Eliminates the need for a Railway volume or a premature Postgres migration just to keep a demo
  session alive (supersedes the volume/Postgres workaround for this purpose).

## Consequences / risks
- The B2 manifest must contain everything `RecapResponse` needs (it currently stores a subset);
  the write path must be extended. Presigned URLs are already regenerated per request (v1.6.0).
- One extra B2 GET on cache miss — negligible latency, only on the cold path.
- Keep `SESSION_DB_PATH` (v1.6.0) as an optional volume for those who want the SQLite cache to
  persist too; B2 fallback is the durability guarantee.

## Alternatives considered
- Railway persistent volume for SQLite — works, but ties durability to one host and doesn't
  improve the B2 story.
- PostgreSQL (`DATABASE_URL`) — heavier; the code path was specced (prompt 10) but never built.
  B2-as-truth is lighter and more on-theme. Postgres remains the documented scale path.
