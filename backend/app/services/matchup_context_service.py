"""Bracket-path context: how likely two teams meet at a given knockout round."""

from __future__ import annotations

from functools import lru_cache

import numpy as np

from app.core.config import settings
from app.models.bracket_schemas import KnockoutMatchPrediction
from app.models.schemas import BracketMatchupContext
from app.services.bracket_service import _load_groups, _run_group_stage, predict_bracket

ROUND_ALIASES: dict[str, str] = {
    "group": "Group stage",
    "group stage": "Group stage",
    "r32": "Round of 32",
    "round of 32": "Round of 32",
    "r16": "Round of 16",
    "round of 16": "Round of 16",
    "qf": "Quarter-finals",
    "quarter-finals": "Quarter-finals",
    "quarterfinals": "Quarter-finals",
    "sf": "Semi-finals",
    "semi-finals": "Semi-finals",
    "semifinals": "Semi-finals",
    "semi final": "Semi-finals",
    "final": "Final",
    "f": "Final",
}


def normalize_round(label: str | None) -> str | None:
    if not label or not label.strip():
        return None
    key = label.strip().lower()
    return ROUND_ALIASES.get(key, label.strip())


def _teams_in_round(
    knockout: dict[str, list[KnockoutMatchPrediction]], round_label: str
) -> set[str]:
    teams: set[str] = set()
    for m in knockout.get(round_label, []):
        teams.add(m.team_a)
        teams.add(m.team_b)
    return teams


def _face_in_round(
    knockout: dict[str, list[KnockoutMatchPrediction]],
    round_label: str,
    team_a: str,
    team_b: str,
) -> KnockoutMatchPrediction | None:
    pair = {team_a, team_b}
    for m in knockout.get(round_label, []):
        if {m.team_a, m.team_b} == pair:
            return m
    return None


@lru_cache(maxsize=32)
def estimate_matchup_context(
    team_a: str,
    team_b: str,
    round_label: str,
    simulations: int,
    seed: int = 42,
) -> BracketMatchupContext:
    """
    Monte Carlo estimate of reaching / meeting at a knockout round.

    Uses the same bracket engine as the main tournament sim (group once, random knockouts).
    """
    simulations = max(50, min(simulations, 1000))
    normalized = normalize_round(round_label) or round_label
    data = _load_groups()
    groups_raw: dict[str, list[str]] = data["groups"]
    group_predictions = _run_group_stage(groups_raw, rng=None)

    rng = np.random.default_rng(seed)
    both_reach = 0
    face = 0
    a_wins_when_face = 0

    for _ in range(simulations):
        sim_rng = np.random.default_rng(rng.integers(0, 2**31 - 1))
        result = predict_bracket(
            rng=sim_rng,
            fixed_groups=group_predictions,
        )
        in_round = _teams_in_round(result.knockout_rounds, normalized)
        if team_a in in_round and team_b in in_round:
            both_reach += 1
        match = _face_in_round(result.knockout_rounds, normalized, team_a, team_b)
        if match:
            face += 1
            if match.predicted_winner == team_a:
                a_wins_when_face += 1

    both_pct = round(100 * both_reach / simulations, 1)
    face_pct = round(100 * face / simulations, 1)
    a_win_pct = round(100 * a_wins_when_face / face, 1) if face else None

    if face_pct < 1:
        scenario = (
            f"A {team_a} vs {team_b} {normalized} is uncommon in this draw "
            f"({face_pct}% of {simulations} sims). Direct H2H odds still show the model "
            f"favourite if the fixture were played."
        )
    else:
        scenario = (
            f"In {face_pct}% of {simulations} bracket paths, {team_a} and {team_b} meet in "
            f"the {normalized}. When paired, {team_a} wins {a_win_pct}% of those sims."
        )

    return BracketMatchupContext(
        round=normalized,
        team_a=team_a,
        team_b=team_b,
        simulations=simulations,
        both_reach_round_pct=both_pct,
        face_in_round_pct=face_pct,
        team_a_wins_if_meet_pct=a_win_pct,
        scenario_note=scenario,
    )


def get_matchup_context(
    team_a: str,
    team_b: str,
    round_label: str | None,
) -> BracketMatchupContext | None:
    normalized = normalize_round(round_label)
    if not normalized or normalized == "Group stage":
        return None
    sims = settings.MATCHUP_CONTEXT_SIMULATIONS
    return estimate_matchup_context(team_a, team_b, normalized, sims)


def clear_matchup_context_cache() -> None:
    estimate_matchup_context.cache_clear()
