"""Shared match outcome resolution — used by bracket, compare, and predictor."""

from __future__ import annotations

import math

from app.models.domain import HeadToHeadRecord, TeamFeatures
from app.models.schemas import MatchProbabilities


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def apply_strength_consistency(
    probs: MatchProbabilities,
    features_a: TeamFeatures,
    features_b: TeamFeatures,
    *,
    knockout: bool,
) -> MatchProbabilities:
    """
    Blend ML probabilities with strength/Elo prior when teams differ sharply.

    Prevents large rating gaps (e.g. Spain 78 vs Netherlands 62) from being
    inverted by asymmetric or noisy model outputs.
    """
    gap = features_a.strength_rating - features_b.strength_rating
    if abs(gap) < 8.0:
        return probs

    w = min(0.5, abs(gap) / 30.0)
    elo_a_share = _sigmoid(gap / 8.0 * 2.5)

    if knockout:
        ma = probs.team_a_win / 100.0
        mb = probs.team_b_win / 100.0
        ba = (1.0 - w) * ma + w * elo_a_share
        bb = (1.0 - w) * mb + w * (1.0 - elo_a_share)
        total = ba + bb
        if total <= 0:
            return probs
        return MatchProbabilities(
            team_a_win=round(ba / total * 100, 1),
            draw=0.0,
            team_b_win=round(bb / total * 100, 1),
        )

    draw = probs.draw
    remaining = 100.0 - draw
    win_total = probs.team_a_win + probs.team_b_win
    if win_total <= 0:
        return probs

    ca = probs.team_a_win / win_total
    cb = probs.team_b_win / win_total
    blend_a = (1.0 - w) * ca + w * elo_a_share
    blend_b = (1.0 - w) * cb + w * (1.0 - elo_a_share)
    norm = blend_a + blend_b
    return MatchProbabilities(
        team_a_win=round(remaining * blend_a / norm, 1),
        draw=round(draw, 1),
        team_b_win=round(remaining * blend_b / norm, 1),
    )


def pick_winner(
    team_a: str,
    team_b: str,
    probs: MatchProbabilities,
    features_a: TeamFeatures,
    features_b: TeamFeatures,
    *,
    allow_draw: bool,
) -> str:
    """Deterministic winner from symmetrized, strength-adjusted probabilities."""
    pa, pd, pb = probs.team_a_win, probs.draw, probs.team_b_win

    if allow_draw and pd >= pa and pd >= pb:
        return "draw"

    if abs(pa - pb) < 1.0:
        return team_a if features_a.strength_rating >= features_b.strength_rating else team_b

    return team_a if pa >= pb else team_b


def favored_team(
    team_a: str,
    team_b: str,
    probs: MatchProbabilities,
    features_a: TeamFeatures,
    features_b: TeamFeatures,
    *,
    allow_draw: bool = True,
) -> str:
    winner = pick_winner(team_a, team_b, probs, features_a, features_b, allow_draw=allow_draw)
    if winner == "draw":
        return "Draw"
    return winner
