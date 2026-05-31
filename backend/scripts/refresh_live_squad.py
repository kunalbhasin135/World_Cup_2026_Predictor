#!/usr/bin/env python3
"""
Refresh data/live/squad_status.json from API-Football when API_FOOTBALL_KEY is set.

Usage:
  cd backend && source .venv/bin/activate
  export API_FOOTBALL_KEY=your_key
  python scripts/refresh_live_squad.py

Team IDs are API-Football national team identifiers — update mapping as needed.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.services import live_squad_service

# National team IDs on api-sports.io (examples — verify on provider dashboard)
TEAM_API_IDS: dict[str, int] = {
    "Spain": 9,
    "Portugal": 27,
    "France": 2,
    "England": 10,
    "Germany": 25,
    "Brazil": 6,
    "Argentina": 26,
    "Netherlands": 1118,
    "Belgium": 1,
    "Croatia": 3,
    "USA": 2384,
    "Mexico": 16,
    "Canada": 5529,
    "Morocco": 31,
    "Japan": 12,
    "Colombia": 8,
    "Uruguay": 7,
}


async def main() -> None:
    if not settings.API_FOOTBALL_KEY:
        print("Set API_FOOTBALL_KEY in backend/.env to fetch live injuries.")
        sys.exit(1)

    path = settings.LIVE_DATA_DIR / "squad_status.json"
    existing: dict = {}
    if path.is_file():
        with path.open(encoding="utf-8") as f:
            existing = json.load(f)

    teams_out = existing.get("teams", {})
    season = settings.API_FOOTBALL_SEASON

    for team_name, team_id in TEAM_API_IDS.items():
        print(f"Fetching injuries: {team_name} (id={team_id})...")
        try:
            rows = await live_squad_service.fetch_api_football_injuries(team_id, season)
            status = live_squad_service.merge_api_injuries_into_status(team_name, rows)
            teams_out[team_name] = status.model_dump()
        except Exception as exc:
            print(f"  skip {team_name}: {exc}")

    payload = {
        "last_updated": teams_out.get("Spain", {}).get("last_updated", "unknown"),
        "source": "api-football",
        "teams": teams_out,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"Wrote {path}")


if __name__ == "__main__":
    asyncio.run(main())
