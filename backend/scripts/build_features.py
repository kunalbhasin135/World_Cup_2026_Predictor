#!/usr/bin/env python3
"""
Download international results (if missing) and build processed team features.

Usage (from backend/):
    python scripts/build_features.py
    python scripts/build_features.py --skip-download
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running as: python scripts/build_features.py
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx

from app.core.config import settings
from app.services.data.feature_engineering import build_all_features, save_processed_features
from app.services.data.feature_store import clear_cache


def _bracket_team_names() -> list[str]:
    path = settings.DATA_DIR / "bracket" / "wc2026_groups.json"
    if not path.is_file():
        return []
    import json

    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    teams: list[str] = []
    for group_teams in data.get("groups", {}).values():
        teams.extend(group_teams)
    return teams


RESULTS_URL = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"


def download_results(dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading results -> {dest}")
    response = httpx.get(RESULTS_URL, timeout=120.0, follow_redirects=True)
    response.raise_for_status()
    dest.write_bytes(response.content)
    line_count = dest.read_text().count("\n")
    print(f"Downloaded {line_count:,} rows")
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build processed team features from match history")
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Use existing data/raw/results.csv only",
    )
    args = parser.parse_args()

    results_path = settings.RAW_DATA_DIR / "results.csv"
    if not args.skip_download and not results_path.is_file():
        download_results(results_path)
    elif not results_path.is_file():
        print(f"ERROR: {results_path} not found. Run without --skip-download.")
        sys.exit(1)
    else:
        print(f"Using existing results at {results_path}")

    bracket_teams = _bracket_team_names()
    print(f"Building features for profile + bracket teams ({len(bracket_teams)} in bracket)...")
    team_features, h2h_records = build_all_features(
        results_path=results_path,
        extra_teams=bracket_teams,
        min_matches=50,
    )
    team_path, h2h_path = save_processed_features(team_features, h2h_records)
    clear_cache()

    print(f"Wrote {len(team_features)} team feature rows -> {team_path}")
    print(f"Wrote {len(h2h_records)} head-to-head pairs -> {h2h_path}")
    print("Done. Restart the API server to pick up new features.")


if __name__ == "__main__":
    main()
