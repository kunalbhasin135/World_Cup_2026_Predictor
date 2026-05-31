"""Poisson regression scoreline predictor with xG fallback."""

from app.models.domain import TeamFeatures
from app.models.schemas import MatchProbabilities, PredictedScore
from app.services.ml import model_loader
from app.services.ml.feature_vector import build_match_vector
from app.services.ml.match_context import world_cup_inference_context
from app.services.prediction import feature_provider


def _expected_goals(attack: TeamFeatures, defense: TeamFeatures) -> float:
    base = 1.15
    attack_factor = attack.last_10_goals_scored_avg / 1.5
    defense_factor = defense.last_10_goals_conceded_avg / 1.0
    strength_boost = attack.strength_rating / 100.0
    return base * attack_factor * defense_factor * (0.85 + 0.15 * strength_boost)


def _round_goals(xg: float) -> int:
    if xg < 0.35:
        return 0
    if xg < 1.15:
        return 1
    if xg < 2.0:
        return 2
    return min(4, round(xg))


def _poisson_score(
    features_a: TeamFeatures,
    features_b: TeamFeatures,
    h2h,
    context: dict[str, float] | None = None,
) -> PredictedScore | None:
    home_model = model_loader.load_poisson_home()
    away_model = model_loader.load_poisson_away()
    if home_model is None or away_model is None:
        return None

    vector = build_match_vector(features_a, features_b, h2h, context).reshape(1, -1)
    xg_a = max(0.05, float(home_model.predict(vector)[0]))
    xg_b = max(0.05, float(away_model.predict(vector)[0]))
    return PredictedScore(team_a=_round_goals(xg_a), team_b=_round_goals(xg_b))


def predict_score(
    features_a: TeamFeatures,
    features_b: TeamFeatures,
    probabilities: MatchProbabilities,
    *,
    context: dict[str, float] | None = None,
) -> PredictedScore:
    ctx = context or world_cup_inference_context()
    h2h = feature_provider.get_head_to_head(features_a.team_name, features_b.team_name)
    poisson = _poisson_score(features_a, features_b, h2h, ctx)

    if poisson is not None:
        score_a, score_b = poisson.team_a, poisson.team_b
    else:
        xg_a = _expected_goals(features_a, features_b)
        xg_b = _expected_goals(features_b, features_a)
        score_a = _round_goals(xg_a)
        score_b = _round_goals(xg_b)

    if probabilities.team_a_win > probabilities.team_b_win and probabilities.team_a_win > probabilities.draw:
        if score_a <= score_b:
            score_a = score_b + 1
    elif probabilities.team_b_win > probabilities.team_a_win and probabilities.team_b_win > probabilities.draw:
        if score_b <= score_a:
            score_b = score_a + 1
    elif probabilities.draw >= probabilities.team_a_win and probabilities.draw >= probabilities.team_b_win:
        if score_a != score_b:
            avg = max(score_a, score_b)
            score_a = score_b = avg

    return PredictedScore(team_a=score_a, team_b=score_b)


def score_model_source() -> str:
    return "poisson_regression" if model_loader.poisson_available() else "expected_goals"
