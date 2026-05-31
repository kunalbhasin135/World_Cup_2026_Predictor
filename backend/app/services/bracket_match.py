"""Shared knockout match resolution for bracket simulation."""

from __future__ import annotations

import numpy as np

from app.models.bracket_schemas import KnockoutMatchPrediction
from app.models.schemas import MatchProbabilities, PredictedScore
from app.services.prediction.engine import engine
from app.services.prediction.match_resolution import pick_winner


def ml_outcome(
    team_a: str,
    team_b: str,
    *,
    allow_draw: bool,
    rng=None,
) -> tuple[str, int, int, float, float, float]:
    """Resolve match using ML win/draw/loss probabilities."""
    result = engine.predict(team_a, team_b, knockout=not allow_draw)
    pa, pd, pb = result.team_a_win_prob, result.draw_prob, result.team_b_win_prob
    sa, sb = result.predicted_score_a, result.predicted_score_b
    fa = result.features_a
    fb = result.features_b

    probs = MatchProbabilities(team_a_win=pa, draw=pd, team_b_win=pb)

    if rng is not None:
        if allow_draw:
            probs_arr = np.array([pa, pd, pb], dtype=float)
            probs_arr = probs_arr / probs_arr.sum()
            outcome = rng.choice([team_a, "draw", team_b], p=probs_arr)
        else:
            probs_arr = np.array([pa, pb], dtype=float)
            probs_arr = probs_arr / probs_arr.sum()
            outcome = rng.choice([team_a, team_b], p=probs_arr)
        winner = outcome
    else:
        winner = pick_winner(team_a, team_b, probs, fa, fb, allow_draw=allow_draw)

    if winner == team_a:
        if sa <= sb:
            sa = max(sb + 1, 1)
    elif winner == team_b:
        if sb <= sa:
            sb = max(sa + 1, 1)
    else:
        avg = max(0, min(sa, sb))
        sa = sb = avg if avg > 0 else 1

    return winner, sa, sb, pa, pd, pb


def knockout_match(
    round_name: str,
    match_id: str,
    team_a: str,
    team_b: str,
    *,
    overrides: dict[str, str] | None = None,
    rng=None,
) -> KnockoutMatchPrediction:
    winner, sa, sb, pa, pd, pb = ml_outcome(team_a, team_b, allow_draw=False, rng=rng)
    if overrides and match_id in overrides:
        forced = overrides[match_id]
        if forced in (team_a, team_b):
            winner = forced
            if winner == team_a and sa <= sb:
                sa = max(sb + 1, 1)
            elif winner == team_b and sb <= sa:
                sb = max(sa + 1, 1)
    return KnockoutMatchPrediction(
        round=round_name,
        match_id=match_id,
        team_a=team_a,
        team_b=team_b,
        predicted_winner=winner,
        predicted_score=PredictedScore(team_a=sa, team_b=sb),
        team_a_win_prob=pa,
        draw_prob=pd,
        team_b_win_prob=pb,
        next_match_id=None,
        feeds_slot=None,
    )


def select_third_place_advancers(all_third: list[dict], count: int = 8) -> set[str]:
    ranked = sorted(all_third, key=lambda r: (r["points"], r["gd"], r["goals_for"]), reverse=True)
    return {r["team"] for r in ranked[:count]}
