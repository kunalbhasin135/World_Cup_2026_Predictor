"""Orchestrates feature loading, probability/score models, and explanations."""

from app.models.domain import EnginePrediction, TeamFeatures
from app.services.ml.match_context import world_cup_inference_context
from app.services.prediction import explainer, feature_provider, probability_model, score_model


class PredictionEngine:
    """Central prediction pipeline with group-stage and knockout modes."""

    def predict(
        self,
        team_a: str,
        team_b: str,
        *,
        knockout: bool = False,
        context: dict[str, float] | None = None,
    ) -> EnginePrediction:
        features_a = feature_provider.get_team_features(team_a)
        features_b = feature_provider.get_team_features(team_b)
        h2h = feature_provider.get_head_to_head(team_a, team_b)
        ctx = context or world_cup_inference_context()

        probabilities = probability_model.predict_probabilities(
            features_a, features_b, h2h, knockout=knockout, context=ctx
        )
        predicted_score = score_model.predict_score(features_a, features_b, probabilities, context=ctx)
        confidence = probability_model.confidence_from_probabilities(probabilities)
        reasons = explainer.generate_reasons(
            team_a, team_b, features_a, features_b, h2h, probabilities
        )

        return EnginePrediction(
            team_a=features_a.team_name,
            team_b=features_b.team_name,
            team_a_win_prob=probabilities.team_a_win,
            draw_prob=probabilities.draw,
            team_b_win_prob=probabilities.team_b_win,
            predicted_score_a=predicted_score.team_a,
            predicted_score_b=predicted_score.team_b,
            confidence=confidence,
            reasons=reasons,
            features_a=features_a,
            features_b=features_b,
            head_to_head=h2h,
        )


def features_to_form_snapshot(features: TeamFeatures):
    from app.models.schemas import RecentFormSnapshot

    return RecentFormSnapshot(
        last_5_results=features.last_5_results,
        goals_scored_avg=features.last_10_goals_scored_avg,
        goals_conceded_avg=features.last_10_goals_conceded_avg,
        goal_difference=features.last_10_goal_difference,
    )


engine = PredictionEngine()
