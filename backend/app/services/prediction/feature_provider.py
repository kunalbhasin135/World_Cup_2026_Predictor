"""Load team features and head-to-head — historical data first, placeholder fallback."""

import json
import re
from functools import lru_cache

from app.core.config import settings
from app.models.domain import HeadToHeadRecord, TeamFeatures
from app.services.data import feature_store

_EXTRA_FEATURE_KEYS = {"elo_rating", "total_matches", "team_name"}


def data_source() -> str:
    """Return which feature source is active."""
    if settings.USE_HISTORICAL_FEATURES and feature_store.processed_data_available():
        return "historical"
    return "placeholder"


def _canonical_h2h_key(team_a: str, team_b: str) -> str:
    names = sorted([team_a.strip(), team_b.strip()], key=str.lower)
    return f"{names[0]}|{names[1]}"


def _to_team_features(team_name: str, data: dict) -> TeamFeatures:
    payload = {k: v for k, v in data.items() if k not in _EXTRA_FEATURE_KEYS}
    payload["team_name"] = team_name
    return TeamFeatures.model_validate(payload)


def _flip_h2h_for_team_a(
    record: dict,
    team_a: str,
    team_b: str,
    key: str,
) -> HeadToHeadRecord:
    first, _ = key.split("|")
    if team_a.strip().lower() == first.lower():
        a_wins = record["team_a_wins"]
        b_wins = record["team_b_wins"]
    else:
        a_wins = record["team_b_wins"]
        b_wins = record["team_a_wins"]

    return HeadToHeadRecord(
        team_a=team_a,
        team_b=team_b,
        team_a_wins=a_wins,
        draws=record.get("draws", 0),
        team_b_wins=b_wins,
        recent_meetings=record.get("recent_meetings", 0),
        last_meeting_score=record.get("last_meeting_score"),
        last_meeting_winner=record.get("last_meeting_winner"),
        summary=record.get("summary", ""),
        is_estimated=record.get("is_estimated", False),
    )


def _synthetic_features(team_name: str) -> TeamFeatures:
    seed = sum(ord(c) for c in team_name.lower())
    wins = 2 + (seed % 3)
    draws = 1 + (seed % 2)
    losses = max(0, 5 - wins - draws)
    results = [["W", "D", "L"][(seed + i) % 3] for i in range(5)]
    scored = round(1.0 + (seed % 8) / 10, 1)
    conceded = round(0.8 + (seed % 6) / 10, 1)
    return TeamFeatures(
        team_name=team_name,
        strength_rating=70.0 + (seed % 15),
        last_5_results="-".join(results),
        last_5_wins=wins,
        last_5_draws=draws,
        last_5_losses=losses,
        last_10_goals_scored_avg=scored,
        last_10_goals_conceded_avg=conceded,
        last_10_goal_difference=round(scored - conceded, 1),
        form_index=round(0.5 + (seed % 30) / 100, 2),
        possession_avg=45.0 + (seed % 15),
        midfield_control_index=0.5 + (seed % 25) / 100,
        transition_threat_index=0.5 + (seed % 20) / 100,
    )


@lru_cache(maxsize=1)
def _load_placeholder_team_features() -> dict[str, dict]:
    path = settings.PLACEHOLDER_DATA_DIR / "team_features.json"
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _load_placeholder_h2h() -> dict[str, dict]:
    path = settings.PLACEHOLDER_DATA_DIR / "head_to_head.json"
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


from app.services.data.team_aliases import to_dataset_name


def _resolve_team_key(team_name: str, features_map: dict[str, dict]) -> str | None:
    candidates = [team_name.strip(), to_dataset_name(team_name)]
    for name in candidates:
        if name in features_map:
            return name
    lower_map = {k.lower(): k for k in features_map}
    for name in candidates:
        hit = lower_map.get(name.lower())
        if hit:
            return hit
    return None


def _get_features_map() -> dict[str, dict]:
    if settings.USE_HISTORICAL_FEATURES:
        processed = feature_store.load_processed_team_features()
        if processed:
            return processed
    return _load_placeholder_team_features()


def _get_h2h_map() -> dict[str, dict]:
    if settings.USE_HISTORICAL_FEATURES:
        processed = feature_store.load_processed_h2h()
        if processed:
            return processed
    return _load_placeholder_h2h()


def get_team_features(team_name: str) -> TeamFeatures:
    features_map = _get_features_map()
    key = _resolve_team_key(team_name, features_map)
    if key is None:
        return _synthetic_features(team_name)
    return _to_team_features(key, features_map[key])


def get_head_to_head(team_a: str, team_b: str) -> HeadToHeadRecord:
    h2h_map = _get_h2h_map()
    key = _canonical_h2h_key(team_a, team_b)
    record = h2h_map.get(key)
    if record:
        return _flip_h2h_for_team_a(record, team_a, team_b, key)

    seed = sum(ord(c) for c in key.lower())
    meetings = 4 + (seed % 6)
    a_wins = 1 + (seed % 3)
    b_wins = 1 + ((seed * 2) % 3)
    draws = max(0, meetings - a_wins - b_wins)
    return HeadToHeadRecord(
        team_a=team_a,
        team_b=team_b,
        team_a_wins=a_wins,
        draws=draws,
        team_b_wins=b_wins,
        recent_meetings=meetings,
        summary="Estimated head-to-head — run build_features.py for historical data.",
        is_estimated=True,
    )
