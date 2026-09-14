#!/usr/bin/env python3
"""Check that a triage.json ledger covers every reviewable intake index.

Usage:
    python3 scripts/validate_triage.py \\
      --intake ~/Documents/tech-briefs/radar/intake/YYYY-MM-DD.json \\
      --triage ~/Documents/tech-briefs/radar/intake/YYYY-MM-DD.triage.json

Exit 0 on a complete, unique, in-range disposition. Exit 1 with one error
per line otherwise. Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REASONS = ("marketing", "dup", "junior", "noise", "narrow")


def check(intake: dict, triage: dict) -> list[str]:
    """Return human-readable errors. Empty list = valid."""
    errors: list[str] = []
    items = intake.get("items")
    if not isinstance(items, list):
        return ["intake missing items[]"]
    expected = set(range(len(items)))
    # Prefer the crawler's own indexes when present.
    present = []
    for i, item in enumerate(items):
        if isinstance(item, dict) and "i" in item:
            present.append(item["i"])
        else:
            present.append(i)
    if set(present) != expected:
        errors.append(f"intake items[].i are not dense 0..{len(items) - 1}")
        expected = set(present)

    if not isinstance(triage, dict):
        return errors + ["triage is not an object"]
    kept = triage.get("kept")
    dropped = triage.get("dropped")
    if not isinstance(kept, list):
        errors.append("triage.kept missing or not a list")
        kept = []
    if not isinstance(dropped, dict):
        errors.append("triage.dropped missing or not an object")
        dropped = {}

    unknown = sorted(set(dropped) - set(REASONS))
    if unknown:
        errors.append(f"unknown drop reasons: {', '.join(unknown)}")
    missing_reasons = [r for r in REASONS if r not in dropped]
    if missing_reasons:
        errors.append(f"dropped missing keys (use empty lists): {', '.join(missing_reasons)}")

    seen: dict[int, str] = {}

    def take(idx, where: str) -> None:
        if not isinstance(idx, int) or isinstance(idx, bool):
            errors.append(f"{where}: {idx!r} is not an int")
            return
        if idx not in expected:
            errors.append(f"{where}: index {idx} not in intake")
            return
        if idx in seen:
            errors.append(f"index {idx} in both {seen[idx]} and {where}")
            return
        seen[idx] = where

    for idx in kept:
        take(idx, "kept")
    for reason, idxs in dropped.items():
        if not isinstance(idxs, list):
            errors.append(f"dropped.{reason} is not a list")
            continue
        for idx in idxs:
            take(idx, f"dropped.{reason}")

    missing = sorted(expected - set(seen))
    if missing:
        preview = ", ".join(str(i) for i in missing[:12])
        extra = f" (+{len(missing) - 12} more)" if len(missing) > 12 else ""
        errors.append(f"{len(missing)} index(es) undispositioned: {preview}{extra}")

    reviewable = intake.get("stats", {}).get("reviewable") if isinstance(intake.get("stats"), dict) else None
    if isinstance(reviewable, int) and reviewable != len(items):
        errors.append(f"stats.reviewable={reviewable} != len(items)={len(items)}")
    if isinstance(reviewable, int) and len(seen) == reviewable and not missing:
        pass  # arithmetic already implied
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--intake", required=True, help="path to YYYY-MM-DD.json")
    ap.add_argument("--triage", required=True, help="path to YYYY-MM-DD.triage.json")
    args = ap.parse_args()
    try:
        intake = json.loads(Path(args.intake).read_text())
    except (OSError, json.JSONDecodeError) as e:
        print(f"cannot read intake: {e}", file=sys.stderr)
        return 2
    try:
        triage = json.loads(Path(args.triage).read_text())
    except (OSError, json.JSONDecodeError) as e:
        print(f"cannot read triage: {e}", file=sys.stderr)
        return 2
    errors = check(intake, triage)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    n = len(intake["items"])
    print(f"ok: {n} reviewable indexes dispositioned once")
    return 0


if __name__ == "__main__":
    sys.exit(main())
