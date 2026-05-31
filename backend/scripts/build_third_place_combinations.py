#!/usr/bin/env python3
"""
Parse FIFA Annex C third-place combinations from Wikipedia export and write JSON.

Source table: https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_knockout_stage

Usage:
  python scripts/build_third_place_combinations.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WIKI_EXPORT = PROJECT_ROOT / "data" / "bracket" / "wikipedia_knockout_export.txt"
OUT_PATH = PROJECT_ROOT / "data" / "bracket" / "third_place_combinations.json"

SLOTS = ["1A", "1B", "1D", "1E", "1G", "1I", "1K", "1L"]
ROW_RE = re.compile(
    r"^\|\s*(\d+)\s*\|\s*([A-L])\s*\|\s*([A-L])\s*\|\s*([A-L])\s*\|\s*([A-L])\s*\|"
    r"\s*([A-L])\s*\|\s*([A-L])\s*\|\s*([A-L])\s*\|\s*([A-L])\s*\|\s*"
    r"3([A-L])\s*\|\s*3([A-L])\s*\|\s*3([A-L])\s*\|\s*3([A-L])\s*\|\s*"
    r"3([A-L])\s*\|\s*3([A-L])\s*\|\s*3([A-L])\s*\|\s*3([A-L])\s*\|"
)


def parse_table(path: Path) -> dict[str, dict[str, str]]:
    combos: dict[str, dict[str, str]] = {}
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        m = ROW_RE.match(line.strip())
        if not m:
            continue
        groups = list(m.groups()[1:9])
        third_sources = list(m.groups()[9:17])
        key = "".join(sorted(groups))
        combos[key] = dict(zip(SLOTS, third_sources, strict=True))
    return combos


def main() -> None:
    source = WIKI_EXPORT
    if len(sys.argv) > 1:
        source = Path(sys.argv[1])
    if not source.is_file():
        print(f"Missing source file: {source}")
        sys.exit(1)

    combos = parse_table(source)
    if len(combos) != 495:
        print(f"Warning: expected 495 combinations, got {len(combos)}")

    payload = {
        "source": "FIFA World Cup 2026 Regulations Annex C (via Wikipedia knockout stage article)",
        "slots": SLOTS,
        "combinations": combos,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"Wrote {len(combos)} combinations to {OUT_PATH}")


if __name__ == "__main__":
    main()
