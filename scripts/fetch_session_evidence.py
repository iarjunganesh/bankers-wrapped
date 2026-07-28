"""
Pull a completed session's evidence JSONs out of B2 into `assets/<label>/<short-id>/evidence/`.

Used to refresh the judge-facing evidence folders after a new demo run, so the
committed artifacts match whatever session the demo video actually shows.
Resolves the session's `user_id` via the flat B2 index (ADR-008), so you only
need the session id.

Usage:
    uv run python scripts/fetch_session_evidence.py <session_id>
    uv run python scripts/fetch_session_evidence.py <session_id> --label plaid-run
    uv run python scripts/fetch_session_evidence.py <session_id> --dry-run

Read-only against B2. Costs nothing and touches no GMI credit.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from backend.config import get_settings  # noqa: E402
from backend.storage.b2_client import B2Client  # noqa: E402

# suffix → how to build the B2 key from (user_id, session_id)
ARTIFACTS: dict[str, str] = {
    "analytics": "pipeline/analytics.json",
    "generation": "pipeline/generation.json",
    "prompts": "pipeline/prompts.json",
    "script": "pipeline/script.json",
    "session-metadata": "metadata/session_metadata.json",
}


def resolve_user_id(b2: B2Client, session_id: str) -> str:
    """Look up the owning user_id from the flat session index (ADR-008)."""
    index = b2.download_json(f"index/{session_id}.json")
    for field in ("user_id", "userId", "user"):
        if isinstance(index.get(field), str):
            return index[field]
    raise SystemExit(
        f"could not find a user_id in index/{session_id}.json — keys present: "
        f"{sorted(index)}"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("session_id")
    ap.add_argument("--label", default="csv-run", help="assets/<label>/ (default: csv-run)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    s = get_settings()
    b2 = B2Client(
        endpoint_url=s.b2_endpoint_url,
        key_id=s.b2_key_id,
        application_key=s.b2_application_key,
        bucket_name=s.b2_bucket_name,
    )

    sid = args.session_id
    short = sid[:8]
    user_id = resolve_user_id(b2, sid)
    out_dir = ROOT / "assets" / args.label / short / "evidence"

    print(f"session   : {sid}")
    print(f"user_id   : {user_id}")
    print(f"target    : {out_dir.relative_to(ROOT)}")
    print()

    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    insights: dict = {}
    for suffix, rel in ARTIFACTS.items():
        key = f"{user_id}/{sid}/{rel}"
        try:
            payload = b2.download_bytes(key)
        except Exception as exc:  # noqa: BLE001
            print(f"  !! {suffix:<18} MISSING ({exc.__class__.__name__})")
            continue

        dest = out_dir / f"{short}_{suffix}.json"
        if not args.dry_run:
            dest.write_bytes(payload)
        print(f"  ok {suffix:<18} {len(payload):>7,} B  → {dest.name}")

        if suffix == "analytics":
            insights = json.loads(payload)

    if insights:
        print("\nSanity check — these are the numbers the video will show:")
        for k in (
            "period_label",
            "total_income",
            "total_expenses",
            "savings_amount",
            "savings_rate",
            "personality",
        ):
            if k in insights:
                print(f"  {k:<16} {insights[k]}")
        rate = insights.get("savings_rate")
        if isinstance(rate, (int, float)) and not (0 <= rate <= 60):
            print(
                f"\n  ⚠  savings_rate {rate}% is outside a plausible range — this looks "
                "like the incoherent Plaid sandbox fixture, not a CSV run. Do not put "
                "these numbers on screen (see submission/DEMO_SCRIPT.md honesty rules)."
            )

    print("\nRemember to update the session ids in:")
    print("  assets/README.md · submission/DEMO_SCRIPT.md · submission/SUBMISSION.md")


if __name__ == "__main__":
    main()
