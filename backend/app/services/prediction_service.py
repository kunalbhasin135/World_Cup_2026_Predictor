"""Facade for match predictions — validates input and maps engine output to API schemas."""

from app.models.schemas import (
    CompareMatchupResult,
    CompareRequest,
    CompareResponse,
    FeatureContribution,
    MatchProbabilities,
    ModelInfo,
    PredictRequest,
    PredictResponse,
    PredictedScore,
)
from app.services.exceptions import InvalidMatchupError
from app.services import live_squad_service
from app.services.ml import model_loader
from app.services import matchup_context_service
from app.services.odds_service import implied_odds_from_probabilities
from app.services.prediction import feature_provider
from app.services.prediction.engine import engine, features_to_form_snapshot
from app.services.prediction import probability_model, score_model
from app.services.prediction.explainer import generate_matchup_analysis
from app.services.prediction.match_resolution import favored_team
from app.services import player_service, report_service, scorer_prediction_service


def _validate_matchup(team_a: str, team_b: str) -> tuple[str, str]:
    a = team_a.strip()
    b = team_b.strip()
    if not a or not b:
        raise InvalidMatchupError("Both team names are required.")
    if a.lower() == b.lower():
        raise InvalidMatchupError("Team A and Team B must be different.")
    return a, b


def _build_model_info_from_result(result) -> ModelInfo:
    meta = model_loader.load_model_metadata()
    contributions = probability_model.get_feature_contributions(
        result.features_a, result.features_b, result.head_to_head
    )
    return ModelInfo(
        probability_model=probability_model.model_source(),
        score_model=score_model.score_model_source(),
        feature_source=feature_provider.data_source(),
        test_accuracy=meta.get("test_accuracy"),
        log_loss=meta.get("log_loss"),
        brier_score=meta.get("brier_score"),
        trained_at=meta.get("trained_at"),
        feature_contributions=[
            FeatureContribution(feature=c["feature"], value=c["value"], impact=c["impact"])
            for c in contributions
        ],
    )


def predict_match(request: PredictRequest) -> PredictResponse:
    team_a, team_b = _validate_matchup(request.team_a, request.team_b)

    use_knockout = request.knockout or bool(
        request.match_round
        and matchup_context_service.normalize_round(request.match_round) != "Group stage"
    )

    result = engine.predict(team_a, team_b, knockout=use_knockout)

    report_a = report_service.load_team_report(result.team_a)
    report_b = report_service.load_team_report(result.team_b)

    probabilities = MatchProbabilities(
        team_a_win=result.team_a_win_prob,
        draw=result.draw_prob,
        team_b_win=result.team_b_win_prob,
    )
    predicted_score = PredictedScore(
        team_a=result.predicted_score_a,
        team_b=result.predicted_score_b,
    )

    implied = implied_odds_from_probabilities(
        result.team_a,
        result.team_b,
        probabilities,
        knockout=use_knockout,
        match_round=request.match_round,
    )
    bracket_ctx = matchup_context_service.get_matchup_context(
        result.team_a, result.team_b, request.match_round
    )
    squad_status = live_squad_service.get_match_squad_status(result.team_a, result.team_b)

    return PredictResponse(
        team_a=result.team_a,
        team_b=result.team_b,
        probabilities=probabilities,
        predicted_score=predicted_score,
        confidence=result.confidence,
        favored_team=favored_team(
            result.team_a,
            result.team_b,
            probabilities,
            result.features_a,
            result.features_b,
            allow_draw=not use_knockout,
        ),
        implied_odds=implied,
        bracket_context=bracket_ctx,
        squad_status=squad_status,
        reasons=result.reasons,
        tactical_matchup=report_service.build_tactical_matchup(
            result.team_a, result.team_b, report_a, report_b
        ),
        recent_form={
            result.team_a: features_to_form_snapshot(result.features_a),
            result.team_b: features_to_form_snapshot(result.features_b),
        },
        team_reports={
            result.team_a: report_a,
            result.team_b: report_b,
        },
        matchup_analysis=generate_matchup_analysis(
            result.team_a,
            result.team_b,
            result.features_a,
            result.features_b,
            result.head_to_head,
            probabilities,
            result.confidence,
        ),
        player_analysis=player_service.get_match_player_analysis(result.team_a, result.team_b),
        predicted_scorers=scorer_prediction_service.predict_scorers(
            result.team_a,
            result.team_b,
            predicted_score,
            probabilities,
            result.features_a,
            result.features_b,
        ),
        model_info=_build_model_info_from_result(result),
    )


def compare_matchups(request: CompareRequest) -> CompareResponse:
    results: list[CompareMatchupResult] = []
    model_info: ModelInfo | None = None

    for pair in request.matchups:
        team_a, team_b = _validate_matchup(pair.team_a, pair.team_b)
        result = engine.predict(team_a, team_b)
        probabilities = MatchProbabilities(
            team_a_win=result.team_a_win_prob,
            draw=result.draw_prob,
            team_b_win=result.team_b_win_prob,
        )
        predicted_score = PredictedScore(
            team_a=result.predicted_score_a,
            team_b=result.predicted_score_b,
        )
        favored = favored_team(
            result.team_a,
            result.team_b,
            probabilities,
            result.features_a,
            result.features_b,
            allow_draw=True,
        )

        results.append(
            CompareMatchupResult(
                team_a=result.team_a,
                team_b=result.team_b,
                probabilities=probabilities,
                predicted_score=predicted_score,
                confidence=result.confidence,
                favored_team=favored,
                implied_odds=implied_odds_from_probabilities(
                    result.team_a, result.team_b, probabilities, knockout=False
                ),
            )
        )
        if model_info is None:
            model_info = _build_model_info_from_result(result)

    return CompareResponse(
        matchups=results,
        model_info=model_info or _build_model_info_from_result(engine.predict("France", "Brazil")),
    )
