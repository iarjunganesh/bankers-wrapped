"""
Apply the B2 bucket lifecycle rule from infra/b2-lifecycle.json (ADR-009).

Idempotent: PUT replaces the bucket's lifecycle configuration wholesale, so
re-running always converges on the committed rule. Reads B2 credentials from
the same settings/env as the app.

Usage:
    uv run python scripts/apply_b2_lifecycle.py           # apply + verify
    uv run python scripts/apply_b2_lifecycle.py --dry-run # print payload only
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

RULES_PATH = Path(__file__).parent.parent / "infra" / "b2-lifecycle.json"


def load_lifecycle_config(path: Path = RULES_PATH) -> dict[str, Any]:
    """Load the committed lifecycle rules, stripping the JSON _comment field."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {"Rules": raw["Rules"]}


def apply_lifecycle(client: Any, bucket: str, config: dict[str, Any]) -> dict[str, Any]:
    """PUT the lifecycle configuration and read it back for verification."""
    client.put_bucket_lifecycle_configuration(
        Bucket=bucket,
        LifecycleConfiguration=config,
    )
    result: dict[str, Any] = client.get_bucket_lifecycle_configuration(Bucket=bucket)
    return result


def main() -> int:
    config = load_lifecycle_config()
    if "--dry-run" in sys.argv:
        print(json.dumps(config, indent=2))
        return 0

    import boto3
    from botocore.config import Config

    from backend.config import get_settings

    settings = get_settings()
    client = boto3.client(
        "s3",
        endpoint_url=settings.b2_endpoint_url,
        aws_access_key_id=settings.b2_key_id,
        aws_secret_access_key=settings.b2_application_key,
        config=Config(signature_version="s3v4"),
    )
    applied = apply_lifecycle(client, settings.b2_bucket_name, config)
    print(f"Lifecycle applied to bucket '{settings.b2_bucket_name}':")
    print(json.dumps(applied.get("Rules", []), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
