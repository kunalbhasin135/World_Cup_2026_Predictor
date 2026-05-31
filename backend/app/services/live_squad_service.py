"""Squad availability and injury updates — curated JSON with optional API-Football sync."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

import httpx

from app.core.config import settings
from app.models.squad_schemas import InjuryEntry, SquadStatus, SquadStatusResponse

# FIFA / API-Sports country name → our display name
_API_TEAM_ALIASES: dict[str, str] = {
    "Spain": "Spain",
    "Portugal": "Portugal",
    "France": "France",
    "England": "England",
    "Germany": "Germany",
    "Brazil": "Brazil",
    "Argentina": "Argentina",
    "Netherlands": "Netherlands",
    "Belgium": "Belgium",
    "Croatia": "Croatia",
    "USA": "USA",
    "United States": "USA",
    "Mexico": "Mexico",
    "Canada": "Canada",
    "Morocco": "Morocco",
    "Japan": "Japan",
    "Colombia": "Colombia",
    "Uruguay": "Uruguay",
}


def _slug(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


@lru_cache(maxsize=1)
def _load_curated_status() -> dict[str, dict[str, Any]]:
    path = settings.LIVE_DATA_DIR / "squad_status.json"
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data.get("teams", data)


def _resolve_team_key(team_name: str, data: dict) -> str | None:
    if team_name in data:
        return team_name
    lower = {k.lower(): k for k in data}
    return lower.get(team_name.strip().lower())


def _parse_team_status(team_key: str, raw: dict[str, Any]) -> SquadStatus:
    injuries = [InjuryEntry.model_validate(i) for i in raw.get("injuries", [])]
    return SquadStatus(
        team=team_key,
        last_updated=raw.get("last_updated", "unknown"),
        source=raw.get("source", "curated"),
        injury_summary=raw.get("injury_summary", "No injury updates on file."),
        injuries=injuries,
        squad_strength_modifier=float(raw.get("squad_strength_modifier", 1.0)),
    )


def get_squad_status(team_name: str) -> SquadStatus | None:
    data = _load_curated_status()
    key = _resolve_team_key(team_name, data)
    if key is None:
        return None
    return _parse_team_status(key, data[key])


def get_match_squad_status(team_a: str, team_b: str) -> dict[str, SquadStatus]:
    out: dict[str, SquadStatus] = {}
    for team in (team_a, team_b):
        status = get_squad_status(team)
        if status:
            out[team] = status
    return out


def injury_status_for_player(team_name: str, player_name: str) -> tuple[str | None, str | None]:
    """Return (status, detail) for a player if listed in live injury feed."""
    status = get_squad_status(team_name)
    if not status:
        return None, None
    name_lower = player_name.strip().lower()
    for entry in status.injuries:
        if entry.player.strip().lower() == name_lower:
            return entry.status, entry.detail
    return None, None


def build_injury_news(team_name: str) -> str:
    """Single paragraph for team reports from structured injury data."""
    status = get_squad_status(team_name)
    if not status:
        return "No structured injury feed for this team — check player cards below."
    if not status.injuries:
        return status.injury_summary
    lines = [status.injury_summary]
    for inj in status.injuries[:6]:
        extra = f" ({inj.expected_return})" if inj.expected_return else ""
        lines.append(f"• {inj.player}: {inj.status} — {inj.detail}{extra}")
    return " ".join(lines)


def list_squad_statuses() -> SquadStatusResponse:
    data = _load_curated_status()
    teams = [_parse_team_status(k, v) for k, v in sorted(data.items())]
    return SquadStatusResponse(
        teams=teams,
        count=len(teams),
        data_source="curated" if teams else "none",
        api_configured=bool(settings.API_FOOTBALL_KEY),
    )


async def fetch_api_football_injuries(team_id: int, season: int) -> list[dict[str, Any]]:
    """Pull injuries from API-Football (api-sports.io) when API_FOOTBALL_KEY is set."""
    if not settings.API_FOOTBALL_KEY:
        return []
    url = f"{settings.API_FOOTBALL_BASE_URL}/injuries"
    headers = {"x-apisports-key": settings.API_FOOTBALL_KEY}
    params = {"team": team_id, "season": season}
    async with httpx.AsyncClient(timeout=20.0) as client:
        res = await client.get(url, headers=headers, params=params)
        res.raise_for_status()
        payload = res.json()
    return payload.get("response", [])


def merge_api_injuries_into_status(
    team_name: str,
    api_rows: list[dict[str, Any]],
) -> SquadStatus:
    """Normalize API-Football injury rows into SquadStatus."""
    injuries: list[InjuryEntry] = []
    for row in api_rows:
        player = row.get("player", {})
        pname = player.get("name") or "Unknown"
        reason = row.get("player", {}).get("reason") or row.get("type") or "Unavailable"
        injuries.append(
            InjuryEntry(
                player=pname,
                status="out" if "injur" in str(reason).lower() else "doubtful",
                detail=str(reason),
                expected_return=None,
            )
        )
    summary = (
        f"{len(injuries)} player(s) flagged via API-Football as of "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}."
        if injuries
        else "No injuries returned from API for this window."
    )
    return SquadStatus(
        team=team_name,
        last_updated=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        source="api-football",
        injury_summary=summary,
        injuries=injuries,
        squad_strength_modifier=1.0,
    )
