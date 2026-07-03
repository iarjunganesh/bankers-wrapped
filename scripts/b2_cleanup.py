"""
B2 cleanup utility for Banker's Wrapped.

Usage:
  # List all sessions with sizes
  python scripts/b2_cleanup.py list

    # Read-only audit for missing subfolders and screenshot candidates
    python scripts/b2_cleanup.py audit

  # Delete all except the sessions you want to keep
  python scripts/b2_cleanup.py clean --keep <session_id1> <session_id2>

  # Dry-run (shows what would be deleted, touches nothing)
  python scripts/b2_cleanup.py clean --keep <session_id1> --dry-run

Reads B2 credentials from environment variables (same as the app):
  B2_KEY_ID, B2_APPLICATION_KEY, B2_ENDPOINT_URL, B2_BUCKET_NAME
"""

from __future__ import annotations

import argparse
import os
import sys

import boto3
from botocore.config import Config

# ── Connect ───────────────────────────────────────────────────────────────────


def _client():
    endpoint = os.environ.get("B2_ENDPOINT_URL", "")
    key_id   = os.environ.get("B2_KEY_ID", "")
    app_key  = os.environ.get("B2_APPLICATION_KEY", "")
    if not all([endpoint, key_id, app_key]):
        sys.exit("Missing B2_ENDPOINT_URL / B2_KEY_ID / B2_APPLICATION_KEY env vars")
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=key_id,
        aws_secret_access_key=app_key,
        config=Config(signature_version="s3v4"),
    )


def _bucket():
    b = os.environ.get("B2_BUCKET_NAME", "")
    if not b:
        sys.exit("Missing B2_BUCKET_NAME env var")
    return b


# ── Discover sessions ─────────────────────────────────────────────────────────


def list_sessions(s3, bucket: str) -> list[dict]:
    """
    Return a list of session records:
      { user_id, session_id, prefix, objects, total_bytes, newest_ts }
    """
    sessions = []

    # Top-level prefixes are user UUIDs
    paginator = s3.get_paginator("list_objects_v2")
    user_pages = paginator.paginate(Bucket=bucket, Delimiter="/")
    user_prefixes = []
    for page in user_pages:
        for cp in page.get("CommonPrefixes", []):
            user_prefixes.append(cp["Prefix"])

    for user_prefix in user_prefixes:
        user_id = user_prefix.rstrip("/")
        # Second level: session UUIDs
        sess_pages = paginator.paginate(Bucket=bucket, Prefix=user_prefix, Delimiter="/")
        for page in sess_pages:
            for cp in page.get("CommonPrefixes", []):
                session_prefix = cp["Prefix"]
                session_id = session_prefix.replace(user_prefix, "").rstrip("/")

                # List all objects under this session
                obj_pages = paginator.paginate(Bucket=bucket, Prefix=session_prefix)
                objects = []
                for op in obj_pages:
                    for obj in op.get("Contents", []):
                        objects.append(obj)

                if not objects:
                    continue

                total_bytes = sum(o["Size"] for o in objects)
                newest_ts   = max(o["LastModified"] for o in objects)
                sessions.append({
                    "user_id":     user_id,
                    "session_id":  session_id,
                    "prefix":      session_prefix,
                    "objects":     objects,
                    "total_bytes": total_bytes,
                    "newest_ts":   newest_ts,
                })

    sessions.sort(key=lambda s: s["newest_ts"])
    return sessions


# ── CLI commands ──────────────────────────────────────────────────────────────


def cmd_list(args):  # type: ignore[no-untyped-def]
    s3     = _client()
    bucket = _bucket()
    sessions = list_sessions(s3, bucket)

    if not sessions:
        print("Bucket is empty.")
        return

    grand_total = 0
    print(f"\n{'#':<3}  {'Created':<22}  {'Size':>8}  {'Files':>5}  Session ID")
    print("-" * 80)
    for i, sess in enumerate(sessions, 1):
        ts    = sess["newest_ts"].strftime("%Y-%m-%d %H:%M UTC")
        mb    = sess["total_bytes"] / 1_048_576
        files = len(sess["objects"])
        sid   = sess["session_id"]
        print(f"{i:<3}  {ts:<22}  {mb:>7.1f}M  {files:>5}  {sid}")
        grand_total += sess["total_bytes"]

    print("-" * 80)
    print(f"Total: {len(sessions)} sessions  {grand_total / 1_048_576:.1f} MB\n")
    print("To keep specific sessions run:")
    print("  python scripts/b2_cleanup.py clean --keep <session_id> [<session_id> ...]\n")


def cmd_clean(args):  # type: ignore[no-untyped-def]
    keep_ids = set(args.keep) if args.keep else set()
    dry_run  = args.dry_run

    s3     = _client()
    bucket = _bucket()
    sessions = list_sessions(s3, bucket)

    to_delete = [s for s in sessions if s["session_id"] not in keep_ids]
    to_keep   = [s for s in sessions if s["session_id"] in keep_ids]

    if not to_delete:
        print("Nothing to delete — all sessions are in the keep list.")
        return

    del_bytes = sum(s["total_bytes"] for s in to_delete)
    del_files = sum(len(s["objects"]) for s in to_delete)
    print(f"\nWill DELETE {len(to_delete)} session(s)  "
          f"({del_files} files, {del_bytes / 1_048_576:.1f} MB):")
    for sess in to_delete:
        ts = sess["newest_ts"].strftime("%Y-%m-%d %H:%M UTC")
        mb = sess["total_bytes"] / 1_048_576
        print(f"  {ts}  {mb:>6.1f} MB  {sess['session_id']}")

    if to_keep:
        print(f"\nWill KEEP {len(to_keep)} session(s):")
        for sess in to_keep:
            ts = sess["newest_ts"].strftime("%Y-%m-%d %H:%M UTC")
            mb = sess["total_bytes"] / 1_048_576
            print(f"  {ts}  {mb:>6.1f} MB  {sess['session_id']}")

    if dry_run:
        print("\n[dry-run] Nothing was deleted.")
        return

    confirm = input(f"\nType YES to delete {del_files} objects: ").strip()
    if confirm != "YES":
        print("Aborted.")
        return

    # Collect ALL versions (current + previous + hide markers) for sessions
    # being deleted so B2 actually frees storage, not just hides the files.
    keep_prefixes = {s["prefix"] for s in to_keep}
    version_paginator = s3.get_paginator("list_object_versions")
    all_versions: list[dict] = []
    for page in version_paginator.paginate(Bucket=bucket):
        for entry in page.get("Versions", []) + page.get("DeleteMarkers", []):
            if not any(entry["Key"].startswith(p) for p in keep_prefixes):
                all_versions.append({"Key": entry["Key"], "VersionId": entry["VersionId"]})

    deleted = 0
    for chunk_start in range(0, len(all_versions), 1000):
        chunk = all_versions[chunk_start : chunk_start + 1000]
        resp = s3.delete_objects(Bucket=bucket, Delete={"Objects": chunk})
        deleted += len(resp.get("Deleted", []))

    for sess in to_delete:
        print(f"  Deleted session {sess['session_id']}  ({len(sess['objects'])} current files)")

    print(f"\nDone. {deleted} object versions permanently removed (includes hidden B2 versions).")


def cmd_audit(args):  # type: ignore[no-untyped-def]
    """
    Read-only session audit.
    Reports whether each session has the expected subfolders and key files.
    """
    s3     = _client()
    bucket = _bucket()
    sessions = list_sessions(s3, bucket)

    if not sessions:
        print("Bucket is empty.")
        return

    required_subfolders = {"input", "pipeline", "output", "metadata"}

    print("\nSession audit (read-only):")
    print("-" * 120)
    print(f"{'#':<3} {'session_id':<36} {'files':>5}  {'missing_subfolders':<40} {'has_output_mp4':<14} {'has_metadata_json':<17}")
    print("-" * 120)

    intact = []
    incomplete = []

    for i, sess in enumerate(sessions, 1):
        prefix = sess["prefix"]
        keys = [o["Key"] for o in sess["objects"]]

        subfolders = set()
        for key in keys:
            rel = key[len(prefix):]
            if "/" in rel:
                subfolders.add(rel.split("/", 1)[0])

        missing = sorted(required_subfolders - subfolders)
        has_output_mp4 = any(key.startswith(prefix + "output/") and key.lower().endswith(".mp4") for key in keys)
        has_metadata_json = any(
            key.startswith(prefix + "metadata/") and key.lower().endswith("session_metadata.json")
            for key in keys
        )

        miss_txt = ",".join(missing) if missing else "-"
        print(f"{i:<3} {sess['session_id']:<36} {len(keys):>5}  {miss_txt:<40} {str(has_output_mp4):<14} {str(has_metadata_json):<17}")

        record = {
            "session_id": sess["session_id"],
            "files": len(keys),
            "newest_ts": sess["newest_ts"],
            "missing": missing,
            "has_output_mp4": has_output_mp4,
            "has_metadata_json": has_metadata_json,
        }
        if not missing and has_output_mp4 and has_metadata_json:
            intact.append(record)
        else:
            incomplete.append(record)

    print("-" * 120)
    print(f"Total sessions: {len(sessions)}")
    print(f"Intact sessions: {len(intact)}")
    print(f"Incomplete sessions: {len(incomplete)}")

    if incomplete:
        print("\nIncomplete details:")
        for rec in incomplete:
            print(
                f"- {rec['session_id']} | files={rec['files']} | "
                f"missing_subfolders={rec['missing'] if rec['missing'] else '[]'} | "
                f"has_output_mp4={rec['has_output_mp4']} | has_metadata_json={rec['has_metadata_json']}"
            )

    # Screenshot guidance: newest complete sessions first.
    if intact:
        ranked = sorted(intact, key=lambda r: r["newest_ts"], reverse=True)
        top = ranked[:3]
        print("\nRecommended screenshot session IDs (newest intact first):")
        for rec in top:
            print(f"- {rec['session_id']}")

    print("\nSafety note: 'audit' is read-only and does not delete or modify any B2 objects.")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Banker's Wrapped — B2 cleanup")
    sub    = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List all sessions with sizes")
    sub.add_parser("audit", help="Read-only audit for missing subfolders and key outputs")

    clean_p = sub.add_parser("clean", help="Delete sessions not in --keep list")
    clean_p.add_argument("--keep", nargs="*", metavar="SESSION_ID",
                         help="Session IDs to preserve (all others are deleted)")
    clean_p.add_argument("--dry-run", action="store_true",
                         help="Show what would be deleted without deleting")

    args = parser.parse_args()
    if args.command == "list":
        cmd_list(args)
    elif args.command == "audit":
        cmd_audit(args)
    elif args.command == "clean":
        cmd_clean(args)


if __name__ == "__main__":
    main()
