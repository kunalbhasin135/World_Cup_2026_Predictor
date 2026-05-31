"""Load player squad profiles and serve scouting analysis."""

import json
import re
from functools import lru_cache

from app.core.config import settings
from app.models.player_schemas import PlayerAnalysis, PlayerProfile
from app.services import live_squad_service


def _slug(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


@lru_cache(maxsize=1)
def _load_squads() -> dict[str, list[dict]]:
    path = settings.PLAYERS_DIR / "squads.json"
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def get_team_players(team_name: str) -> list[PlayerProfile]:
    squads = _load_squads()
    key = _resolve_team_key(team_name, squads)
    if key is None:
        return []
    return [PlayerProfile.model_validate({**p, "team": key}) for p in squads[key]]


def _resolve_team_key(team_name: str, squads: dict) -> str | None:
    if team_name in squads:
        return team_name
    lower = {k.lower(): k for k in squads}
    return lower.get(team_name.strip().lower())


def to_player_analysis(profile: PlayerProfile) -> PlayerAnalysis:
    inj_status, inj_detail = live_squad_service.injury_status_for_player(
        profile.team, profile.name
    )
    return PlayerAnalysis(
        name=profile.name,
        team=profile.team,
        position=profile.position,
        role=profile.role,
        strengths=profile.strengths,
        weaknesses=profile.weaknesses,
        recent_form=profile.recent_form,
        intl_goals=profile.intl_goals,
        intl_caps=profile.intl_caps,
        analysis=profile.analysis,
        watch_out_for=profile.watch_out_for,
        injury_status=inj_status,
        injury_detail=inj_detail,
    )


def get_match_player_analysis(team_a: str, team_b: str) -> dict[str, list[PlayerAnalysis]]:
    return {
        team_a: [to_player_analysis(p) for p in get_team_players(team_a)],
        team_b: [to_player_analysis(p) for p in get_team_players(team_b)],
    }
