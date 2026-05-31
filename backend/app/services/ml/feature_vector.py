"""Feature vector construction shared by training and inference."""

from __future__ import annotations

import numpy as np

from app.models.domain import HeadToHeadRecord, TeamFeatures
from app.services.ml.match_context import world_cup_inference_context

# Order must match training pipeline
FEATURE_NAMES: list[str] = [
    "strength_delta",
    "form_delta",
    "goal_diff_delta",
    "goals_scored_avg_delta",
    "goals_conceded_avg_delta",
    "h2h_advantage",
    "strength_a",
    "strength_b",
    "form_a",
    "form_b",
    "is_neutral",
    "tournament_importance",
    "rest_days_a",
    "rest_days_b",
]


def _context_values(context: dict[str, float] | None) -> tuple[float, float, float, float]:
    ctx = context or world_cup_inference_context()
    return (
        ctx.get("is_neutral", 1.0),
        ctx.get("tournament_importance", 1.0),
        ctx.get("rest_days_a", 0.5),
        ctx.get("rest_days_b", 0.5),
    )


def build_match_vector(
    features_a: TeamFeatures,
    features_b: TeamFeatures,
    h2h: HeadToHeadRecord,
    context: dict[str, float] | None = None,
) -> np.ndarray:
    """Build a 1-D feature vector for team_a vs team_b."""
    is_neutral, importance, rest_a, rest_b = _context_values(context)
    return np.array(
        [
            features_a.strength_rating - features_b.strength_rating,
            features_a.form_index - features_b.form_index,
            features_a.last_10_goal_difference - features_b.last_10_goal_difference,
            features_a.last_10_goals_scored_avg - features_b.last_10_goals_scored_avg,
            features_a.last_10_goals_conceded_avg - features_b.last_10_goals_conceded_avg,
            h2h.advantage_score,
            features_a.strength_rating,
            features_b.strength_rating,
            features_a.form_index,
            features_b.form_index,
            is_neutral,
            importance,
            rest_a,
            rest_b,
        ],
        dtype=np.float64,
    )


def build_match_vector_from_dicts(
    features_a: dict,
    features_b: dict,
    h2h_advantage: float,
    context: dict[str, float] | None = None,
) -> np.ndarray:
    """Build feature vector from raw dicts (used during training)."""
    is_neutral, importance, rest_a, rest_b = _context_values(context)
    return np.array(
        [
            features_a["strength_rating"] - features_b["strength_rating"],
            features_a["form_index"] - features_b["form_index"],
            features_a["last_10_goal_difference"] - features_b["last_10_goal_difference"],
            features_a["last_10_goals_scored_avg"] - features_b["last_10_goals_scored_avg"],
            features_a["last_10_goals_conceded_avg"] - features_b["last_10_goals_conceded_avg"],
            h2h_advantage,
            features_a["strength_rating"],
            features_b["strength_rating"],
            features_a["form_index"],
            features_b["form_index"],
            is_neutral,
            importance,
            rest_a,
            rest_b,
        ],
        dtype=np.float64,
    )
