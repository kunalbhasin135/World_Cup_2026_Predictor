"""
Simulate World Cup 2026 using the ML prediction engine.

- Group stage from official `wc2026_groups.json`
- Knockout uses FIFA fixed bracket paths + Annex C third-place combinations (495)
"""

from __future__ import annotations

import json
from functools import lru_cache
from itertools import combinations

from app.core.config import settings
from app.models.bracket_schemas import (
    BracketPredictionResponse,
    GroupPrediction,
    GroupStanding,
)
from app.services.bracket_match import ml_outcome, select_third_place_advancers
from app.services.official_knockout import build_official_knockout, normalize_override_ids
from app.services.prediction import feature_provider
from app.services.prediction import probability_model


@lru_cache(maxsize=1)
def _load_groups() -> dict:
    path = settings.DATA_DIR / "bracket" / "wc2026_groups.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _ml_outcome(
    team_a: str,
    team_b: str,
    *,
    allow_draw: bool,
    rng=None,
) -> tuple[str, int, int, float, float, float]:
    return ml_outcome(team_a, team_b, allow_draw=allow_draw, rng=rng)


def _init_record(team: str) -> dict:
    return {
        "team": team,
        "played": 0,
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "goals_for": 0,
        "goals_against": 0,
        "points": 0,
    }


def _simulate_group(
    group_name: str,
    teams: list[str],
    *,
    rng=None,
) -> tuple[GroupPrediction, list[dict]]:
    records = {t: _init_record(t) for t in teams}

    for team_a, team_b in combinations(teams, 2):
        winner, ga, gb, _, _, _ = _ml_outcome(team_a, team_b, allow_draw=True, rng=rng)
        ra, rb = records[team_a], records[team_b]
        ra["played"] += 1
        rb["played"] += 1
        ra["goals_for"] += ga
        ra["goals_against"] += gb
        rb["goals_for"] += gb
        rb["goals_against"] += ga

        if ga > gb:
            ra["wins"] += 1
            ra["points"] += 3
            rb["losses"] += 1
        elif gb > ga:
            rb["wins"] += 1
            rb["points"] += 3
            ra["losses"] += 1
        else:
            ra["draws"] += 1
            rb["draws"] += 1
            ra["points"] += 1
            rb["points"] += 1

    sorted_teams = sorted(
        records.values(),
        key=lambda r: (r["points"], r["goals_for"] - r["goals_against"], r["goals_for"]),
        reverse=True,
    )

    third_place_all: list[dict] = []
    standings: list[GroupStanding] = []

    for pos, rec in enumerate(sorted_teams, start=1):
        gd = rec["goals_for"] - rec["goals_against"]
        advances = pos <= 2
        note = "Round of 32 (top 2)" if advances else None
        if pos == 3:
            third_place_all.append({**rec, "group": group_name, "gd": gd})
        standings.append(
            GroupStanding(
                team=rec["team"],
                position=pos,
                played=rec["played"],
                wins=rec["wins"],
                draws=rec["draws"],
                losses=rec["losses"],
                goals_for=rec["goals_for"],
                goals_against=rec["goals_against"],
                goal_difference=gd,
                points=rec["points"],
                advances=advances,
                advancement_note=note,
            )
        )

    return GroupPrediction(group=group_name, teams=teams, standings=standings), third_place_all


def _select_third_place_advancers(all_third: list[dict], count: int = 8) -> set[str]:
    return select_third_place_advancers(all_third, count)


def _run_group_stage(
    groups_raw: dict[str, list[str]],
    *,
    rng=None,
) -> list[GroupPrediction]:
    """Simulate all groups; mark top two + best eight third-place teams."""
    group_predictions: list[GroupPrediction] = []
    all_third: list[dict] = []

    for gname in sorted(groups_raw.keys()):
        gp, thirds = _simulate_group(gname, groups_raw[gname], rng=rng)
        group_predictions.append(gp)
        all_third.extend(thirds)

    third_advancers = select_third_place_advancers(all_third)
    for gp in group_predictions:
        for s in gp.standings:
            if s.position == 3 and s.team in third_advancers:
                s.advances = True
                s.advancement_note = "Round of 32 (best 3rd place)"

    return group_predictions


def _assemble_bracket_response(
    data: dict,
    group_predictions: list[GroupPrediction],
    *,
    overrides: dict[str, str] | None = None,
    rng=None,
) -> BracketPredictionResponse:
    overrides = normalize_override_ids(overrides)
    knockout, tree = build_official_knockout(
        group_predictions, overrides=overrides, rng=rng
    )

    sf = knockout.get("Semi-finals", [])
    third_place_matches = knockout.get("Third place", [])
    third_place = third_place_matches[0].predicted_winner if third_place_matches else ""

    final_matches = knockout.get("Final", [])
    champion = final_matches[0].predicted_winner if final_matches else ""
    runner_up = ""
    if final_matches:
        fm = final_matches[0]
        runner_up = fm.team_b if fm.predicted_winner == fm.team_a else fm.team_a

    contenders = []
    for t in {champion, runner_up, third_place} | {m.predicted_winner for m in sf}:
        if t:
            feat = feature_provider.get_team_features(t)
            contenders.append({"team": t, "strength_rating": feat.strength_rating})
    contenders.sort(key=lambda x: x["strength_rating"], reverse=True)

    official_note = (
        " Knockout paths follow the official FIFA bracket (fixed R32 slots + Annex C "
        "third-place combinations). Group winners meet per tournament tree, not global seeding."
    )

    return BracketPredictionResponse(
        tournament=data.get("tournament", "FIFA World Cup 2026"),
        format=data.get("format", "48 teams"),
        draw_last_updated=data.get("last_updated"),
        note=(data.get("note", "") + official_note
              + " Outcomes use calibrated LR+GBM ensemble with historical Elo/form features."),
        prediction_model=probability_model.model_source(),
        feature_source=feature_provider.data_source(),
        groups=group_predictions,
        knockout_rounds=knockout,
        bracket_tree=tree,
        champion=champion,
        runner_up=runner_up,
        third_place=third_place,
        top_contenders=contenders[:5],
    )


def predict_bracket(
    *,
    overrides: dict[str, str] | None = None,
    rng=None,
    fixed_groups: list[GroupPrediction] | None = None,
    fixed_seeds: list[str] | None = None,  # deprecated, ignored
) -> BracketPredictionResponse:
    data = _load_groups()
    groups_raw: dict[str, list[str]] = data["groups"]

    if fixed_groups is not None:
        group_predictions = fixed_groups
    else:
        group_predictions = _run_group_stage(groups_raw, rng=rng)

    return _assemble_bracket_response(
        data, group_predictions, overrides=overrides, rng=rng
    )


@lru_cache(maxsize=1)
def get_bracket_prediction() -> BracketPredictionResponse:
    return predict_bracket()


def clear_bracket_cache() -> None:
    _load_groups.cache_clear()
    get_bracket_prediction.cache_clear()
    from app.services.official_knockout import _load_template, _load_third_combinations

    _load_template.cache_clear()
    _load_third_combinations.cache_clear()
    from app.services.matchup_context_service import clear_matchup_context_cache

    clear_matchup_context_cache()
    from app.services.monte_carlo_service import clear_monte_carlo_cache

    clear_monte_carlo_cache()
