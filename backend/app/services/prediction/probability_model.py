"""
Match outcome probability model.

Uses calibrated LR + GBM ensemble when available; dedicated knockout model for elimination games.
"""

from __future__ import annotations

import math

from app.models.domain import HeadToHeadRecord, TeamFeatures
from app.models.schemas import ConfidenceLevel, MatchProbabilities
from app.services.ml import model_loader
from app.services.ml.feature_vector import FEATURE_NAMES, build_match_vector
from app.services.ml.match_context import world_cup_inference_context
from app.services.prediction.match_resolution import apply_strength_consistency


def _normalize_probs(probs: MatchProbabilities) -> MatchProbabilities:
    total = probs.team_a_win + probs.draw + probs.team_b_win
    if total == 0:
        return MatchProbabilities(team_a_win=33.3, draw=33.4, team_b_win=33.3)
    factor = 100 / total
    a = round(probs.team_a_win * factor, 1)
    d = round(probs.draw * factor, 1)
    b = round(100 - a - d, 1)
    return MatchProbabilities(team_a_win=a, draw=d, team_b_win=b)


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _rule_based_probabilities(
    features_a: TeamFeatures,
    features_b: TeamFeatures,
    h2h: HeadToHeadRecord,
    *,
    knockout: bool = False,
) -> MatchProbabilities:
    strength_delta = (features_a.strength_rating - features_b.strength_rating) / 10.0
    form_delta = features_a.form_index - features_b.form_index
    gd_delta = (features_a.last_10_goal_difference - features_b.last_10_goal_difference) / 2.0
    h2h_delta = h2h.advantage_score

    advantage = (
        0.40 * strength_delta
        + 0.30 * form_delta * 4.0
        + 0.20 * gd_delta
        + 0.10 * h2h_delta * 2.0
    )

    if knockout:
        team_a_share = _sigmoid(advantage * 2.5)
        return MatchProbabilities(
            team_a_win=round(team_a_share * 100, 1),
            draw=0.0,
            team_b_win=round((1.0 - team_a_share) * 100, 1),
        )

    draw_pct = max(18.0, min(32.0, 28.0 - abs(advantage) * 8.0))
    remaining = 100.0 - draw_pct
    team_a_share = _sigmoid(advantage * 2.5)

    return _normalize_probs(
        MatchProbabilities(
            team_a_win=remaining * team_a_share,
            draw=draw_pct,
            team_b_win=remaining * (1.0 - team_a_share),
        )
    )


def _ensemble_proba(
    features_a: TeamFeatures,
    features_b: TeamFeatures,
    h2h: HeadToHeadRecord,
    context: dict[str, float] | None = None,
) -> list[float]:
    vector = build_match_vector(features_a, features_b, h2h, context).reshape(1, -1)

    lr = model_loader.load_ensemble_lr()
    gbm = model_loader.load_ensemble_gbm()
    if lr is not None and gbm is not None:
        meta = model_loader.load_model_metadata()
        weights = meta.get("ensemble_weights", {"logistic_regression": 0.45, "gradient_boosting": 0.55})
        lr_w = weights.get("logistic_regression", 0.45)
        gbm_w = weights.get("gradient_boosting", 0.55)
        proba = lr_w * lr.predict_proba(vector)[0] + gbm_w * gbm.predict_proba(vector)[0]
        return proba.tolist()

    legacy = model_loader.load_model()
    if legacy is not None:
        return legacy.predict_proba(vector)[0].tolist()

    return []


def _knockout_proba(
    features_a: TeamFeatures,
    features_b: TeamFeatures,
    h2h: HeadToHeadRecord,
    context: dict[str, float] | None = None,
) -> MatchProbabilities:
    ko = model_loader.load_knockout_model()
    if ko is not None:
        vector = build_match_vector(features_a, features_b, h2h, context).reshape(1, -1)
        proba = ko.predict_proba(vector)[0]
        return MatchProbabilities(
            team_a_win=round(float(proba[0] * 100), 1),
            draw=0.0,
            team_b_win=round(float(proba[1] * 100), 1),
        )

    base = _ml_probabilities(features_a, features_b, h2h, context, knockout=False)
    non_draw = base.team_a_win + base.team_b_win
    if non_draw <= 0:
        return MatchProbabilities(team_a_win=50.0, draw=0.0, team_b_win=50.0)
    return MatchProbabilities(
        team_a_win=round(base.team_a_win / non_draw * 100, 1),
        draw=0.0,
        team_b_win=round(base.team_b_win / non_draw * 100, 1),
    )


def _group_proba_one_way(
    features_a: TeamFeatures,
    features_b: TeamFeatures,
    h2h: HeadToHeadRecord,
    context: dict[str, float] | None = None,
) -> MatchProbabilities:
    proba = _ensemble_proba(features_a, features_b, h2h, context)
    if not proba:
        return _rule_based_probabilities(features_a, features_b, h2h, knockout=False)
    return _normalize_probs(
        MatchProbabilities(
            team_a_win=float(proba[0] * 100),
            draw=float(proba[1] * 100),
            team_b_win=float(proba[2] * 100),
        )
    )


def _symmetric_group_proba(
    features_a: TeamFeatures,
    features_b: TeamFeatures,
    h2h: HeadToHeadRecord,
    context: dict[str, float] | None = None,
) -> MatchProbabilities:
    """Average group-stage probabilities from both team orderings."""
    from app.services.prediction import feature_provider

    ab = _group_proba_one_way(features_a, features_b, h2h, context)
    h2h_ba = feature_provider.get_head_to_head(features_b.team_name, features_a.team_name)
    ba = _group_proba_one_way(features_b, features_a, h2h_ba, context)

    return _normalize_probs(
        MatchProbabilities(
            team_a_win=(ab.team_a_win + ba.team_b_win) / 2.0,
            draw=(ab.draw + ba.draw) / 2.0,
            team_b_win=(ab.team_b_win + ba.team_a_win) / 2.0,
        )
    )


def _symmetric_knockout_proba(
    features_a: TeamFeatures,
    features_b: TeamFeatures,
    h2h: HeadToHeadRecord,
    context: dict[str, float] | None = None,
) -> MatchProbabilities:
    """
    Average knockout probabilities from both team orderings.

    The knockout model was trained with home=team_a; averaging removes order bias
    so Portugal vs Belgium matches Belgium vs Portugal.
    """
    from app.services.prediction import feature_provider

    ab = _knockout_proba(features_a, features_b, h2h, context)
    h2h_ba = feature_provider.get_head_to_head(features_b.team_name, features_a.team_name)
    ba = _knockout_proba(features_b, features_a, h2h_ba, context)

    p_a = (ab.team_a_win + ba.team_b_win) / 2.0
    p_b = (ab.team_b_win + ba.team_a_win) / 2.0
    total = p_a + p_b
    if total > 0:
        p_a = p_a / total * 100.0
        p_b = p_b / total * 100.0

    return MatchProbabilities(
        team_a_win=round(p_a, 1),
        draw=0.0,
        team_b_win=round(p_b, 1),
    )


def _ml_probabilities(
    features_a: TeamFeatures,
    features_b: TeamFeatures,
    h2h: HeadToHeadRecord,
    context: dict[str, float] | None = None,
    *,
    knockout: bool = False,
) -> MatchProbabilities:
    if knockout:
        probs = _symmetric_knockout_proba(features_a, features_b, h2h, context)
    else:
        probs = _symmetric_group_proba(features_a, features_b, h2h, context)

    return apply_strength_consistency(probs, features_a, features_b, knockout=knockout)


def predict_probabilities(
    features_a: TeamFeatures,
    features_b: TeamFeatures,
    h2h: HeadToHeadRecord,
    *,
    knockout: bool = False,
    context: dict[str, float] | None = None,
) -> MatchProbabilities:
    ctx = context or world_cup_inference_context()
    if model_loader.model_available():
        return _ml_probabilities(features_a, features_b, h2h, ctx, knockout=knockout)
    probs = _rule_based_probabilities(features_a, features_b, h2h, knockout=knockout)
    return apply_strength_consistency(probs, features_a, features_b, knockout=knockout)


def model_source() -> str:
    if model_loader.ensemble_available():
        return "ensemble_lr_gbm"
    if model_loader.model_available():
        return "logistic_regression"
    return "rule_based"


def confidence_from_probabilities(probabilities: MatchProbabilities) -> ConfidenceLevel:
    probs = [probabilities.team_a_win, probabilities.draw, probabilities.team_b_win]
    max_prob = max(probs)
    spread = max_prob - sorted(probs)[-2]
    if max_prob >= 45 and spread >= 10:
        return "High"
    if max_prob >= 38 and spread >= 6:
        return "Medium"
    return "Low"


def get_feature_contributions(
    features_a: TeamFeatures,
    features_b: TeamFeatures,
    h2h: HeadToHeadRecord,
    context: dict[str, float] | None = None,
) -> list[dict[str, float | str]]:
    """Explain prediction via feature deltas (LR coefficients when available)."""
    vector = build_match_vector(features_a, features_b, h2h, context or world_cup_inference_context())
    lr = model_loader.load_ensemble_lr()
    contributions: list[dict[str, float | str]] = []

    if lr is not None and hasattr(lr, "calibrated_classifiers_"):
        base_est = lr.calibrated_classifiers_[0].estimator
        if hasattr(base_est, "named_steps") and "clf" in base_est.named_steps:
            coef = base_est.named_steps["clf"].coef_
            # Use team_a win class (0) coefficients
            weights = coef[0] if coef.ndim > 1 else coef
            scaled = base_est.named_steps["scaler"].transform(vector.reshape(1, -1))[0]
            for name, val, w in zip(FEATURE_NAMES, scaled, weights, strict=True):
                contributions.append(
                    {"feature": name, "value": round(float(val), 3), "impact": round(float(val * w), 4)}
                )
            contributions.sort(key=lambda x: abs(float(x["impact"])), reverse=True)
            return contributions[:8]

    # Fallback: show key deltas
    ctx = context or world_cup_inference_context()
    deltas = [
        ("strength_delta", features_a.strength_rating - features_b.strength_rating),
        ("form_delta", features_a.form_index - features_b.form_index),
        ("goal_diff_delta", features_a.last_10_goal_difference - features_b.last_10_goal_difference),
        ("h2h_advantage", h2h.advantage_score),
        ("tournament_importance", ctx.get("tournament_importance", 1.0)),
    ]
    for name, val in deltas:
        contributions.append({"feature": name, "value": round(val, 3), "impact": round(val, 4)})
    return contributions
