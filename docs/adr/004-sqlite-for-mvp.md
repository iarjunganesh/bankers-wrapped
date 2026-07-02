# ADR-004: SQLite for MVP
**Status:** Accepted (amended by ADR-008, v1.7.0) | **Date:** 2026-06-25

## Decision
SQLite for MVP. PostgreSQL as documented production upgrade.

> **Amendment (v1.7.0, ADR-008):** SQLite is now a fast *cache*, not the system of
> record. The durable source of truth is the session manifest on Backblaze B2;
> `GET /recap/{id}` falls back to it when the SQLite row is missing (e.g. after a
> redeploy). PostgreSQL remains the documented scale path for the cache layer.

## Rationale
- Zero setup friction for judges
- SQLAlchemy abstraction makes swap trivial
