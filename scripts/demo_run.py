"""
Run the Banker's Wrapped demo pipeline against both synthetic datasets.

Usage:
    python scripts/demo_run.py
    python scripts/demo_run.py --base-url http://127.0.0.1:8000
    python scripts/demo_run.py --no-wait               # skip API readiness check
    python scripts/demo_run.py --dataset jan_2026       # run one dataset only
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

try:
    import httpx
except ImportError:
    print("httpx is required: pip install httpx")
    sys.exit(1)

ROOT = Path(__file__).parent.parent
SYNTHETIC_DIR = ROOT / "data" / "synthetic"

DATASETS: list[tuple[str, str]] = [
    ("transactions_jan_2026.csv", "Financial Builder"),
    ("transactions_q4_2025.csv",  "Financial Explorer"),
]


# ── helpers ───────────────────────────────────────────────────────────────────

def wait_for_api(base_url: str, timeout: int = 40) -> None:
    print(f"Waiting for API at {base_url}/health ...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = httpx.get(f"{base_url}/api/v1/health", timeout=2)
            if r.status_code == 200:
                print("  API is ready.\n")
                return
        except Exception:
            pass
        time.sleep(2)
    print(f"ERROR: API not ready after {timeout}s. Start it with: make dev")
    sys.exit(1)


def separator(title: str = "") -> None:
    line = "=" * 60
    print(f"\n{line}")
    if title:
        print(f"  {title}")
        print(line)


def run_dataset(base_url: str, csv_path: Path, expected_personality: str) -> bool:
    separator(f"{csv_path.name}  (expected: {expected_personality})")

    if not csv_path.exists():
        print(f"  SKIP: file not found at {csv_path}")
        return False

    with open(csv_path, "rb") as f:
        files = {"file": (csv_path.name, f, "text/csv")}
        print("  Sending to pipeline ... (may take 5–15 min with live providers)")
        t0 = time.time()
        try:
            r = httpx.post(
                f"{base_url}/api/v1/recap/generate",
                files=files,
                timeout=900,
            )
        except httpx.RequestError as exc:
            print(f"  REQUEST ERROR: {exc}")
            return False
        elapsed = round(time.time() - t0, 1)

    if r.status_code != 200:
        print(f"  FAILED ({r.status_code}): {r.text[:400]}")
        return False

    data: dict = r.json()
    ins: dict = data["insights"]

    match = "[OK]" if ins["personality"].lower() == expected_personality.lower().replace("financial ", "") else "[MISMATCH]"

    print(f"  Status       : OK  ({elapsed}s, {data['processing_time_ms']}ms pipeline)")
    print(f"  Session      : {data['session_id']}")
    print(f"  Personality  : {ins['personality']}  {match}")
    print(f"  Period       : {ins['period_label']}")
    print(f"  Income       : {ins['currency']} {ins['total_income']:>12,.2f}")
    print(f"  Expenses     : {ins['currency']} {ins['total_expenses']:>12,.2f}")
    print(f"  Savings rate : {ins['savings_rate']:.1%}")

    top = ins["top_categories"][:3]
    cats = ", ".join(f"{c['category']} ({c['percentage']:.0%})" for c in top)
    print(f"  Top spend    : {cats}")

    print(f"  Video URL    : {data['video_url']}")

    return True


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Banker's Wrapped demo runner")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", metavar="URL")
    parser.add_argument("--no-wait", action="store_true", help="Skip API readiness check")
    parser.add_argument(
        "--dataset",
        choices=["jan_2026", "q4_2025"],
        default=None,
        help="Run a single dataset instead of both",
    )
    args = parser.parse_args()

    if not args.no_wait:
        wait_for_api(args.base_url)

    datasets = DATASETS
    if args.dataset == "jan_2026":
        datasets = [DATASETS[0]]
    elif args.dataset == "q4_2025":
        datasets = [DATASETS[1]]

    results: list[bool] = []
    for filename, personality in datasets:
        ok = run_dataset(args.base_url, SYNTHETIC_DIR / filename, personality)
        results.append(ok)

    separator()
    passed = sum(results)
    print(f"  {passed}/{len(results)} datasets completed successfully.")
    if passed < len(results):
        sys.exit(1)


if __name__ == "__main__":
    main()
