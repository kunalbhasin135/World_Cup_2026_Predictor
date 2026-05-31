"""Predict likely goal scorers from player threat indices and match context."""

from app.models.domain import TeamFeatures
from app.models.player_schemas import PlayerProfile, PredictedScorer
from app.models.schemas import MatchProbabilities, PredictedScore
from app.services import player_service

POSITION_WEIGHTS: dict[str, float] = {
    "Forward": 1.0,
    "Attacking Midfielder": 0.68,
    "Midfielder": 0.42,
    "Wing Back": 0.38,
    "Defender": 0.12,
    "Goalkeeper": 0.02,
}


def _position_weight(position: str) -> float:
    return POSITION_WEIGHTS.get(position, 0.35)


def _team_win_prob(team: str, team_a: str, team_b: str, probs: MatchProbabilities) -> float:
    if team == team_a:
        return probs.team_a_win / 100.0
    return probs.team_b_win / 100.0


def _predicted_team_goals(team: str, team_a: str, score: PredictedScore) -> int:
    return score.team_a if team == team_a else score.team_b


def _score_probability(
    player: PlayerProfile,
    team_goals: int,
    win_prob: float,
    team_features: TeamFeatures,
) -> float:
    """
    Estimate P(player scores >= 1) using threat index, role, expected team goals, and form.
    """
    base = player.scoring_threat_index * _position_weight(player.position)
    goal_factor = 0.18 + 0.22 * team_goals
    form_factor = 0.85 + team_features.form_index * 0.2
    win_factor = 1.0 + win_prob * 0.15
    recent = {"excellent": 1.12, "strong": 1.06, "mixed": 0.92, "poor": 0.85}.get(
        player.recent_form.lower(), 1.0
    )

    prob = base * goal_factor * form_factor * win_factor * recent
    return round(min(72.0, max(3.0, prob * 100)), 1)


def _rationale(
    player: PlayerProfile,
    score_prob: float,
    team_goals: int,
    win_prob: float,
) -> str:
    parts = [
        f"{player.position} with scoring threat index {player.scoring_threat_index:.2f}.",
    ]
    if player.intl_goals >= 20:
        parts.append(f"{player.intl_goals} international goals in {player.intl_caps} caps.")
    if team_goals >= 2:
        parts.append(f"Team projected for {team_goals} goals boosts finishing chances.")
    if win_prob >= 0.4:
        parts.append("Side expected to control key phases and create volume.")
    parts.append(f"Model assigns {score_prob:.0f}% chance to find the net.")
    return " ".join(parts)


def predict_scorers(
    team_a: str,
    team_b: str,
    score: PredictedScore,
    probabilities: MatchProbabilities,
    features_a: TeamFeatures,
    features_b: TeamFeatures,
    top_n: int = 8,
) -> list[PredictedScorer]:
    candidates: list[tuple[float, PlayerProfile, TeamFeatures, int, float]] = []

    for team, features in [(team_a, features_a), (team_b, features_b)]:
        team_goals = _predicted_team_goals(team, team_a, score)
        win_prob = _team_win_prob(team, team_a, team_b, probabilities)
        for player in player_service.get_team_players(team):
            if _position_weight(player.position) < 0.1:
                continue
            prob = _score_probability(player, team_goals, win_prob, features)
            candidates.append((prob, player, features, team_goals, win_prob))

    candidates.sort(key=lambda x: x[0], reverse=True)

    results: list[PredictedScorer] = []
    for rank, (prob, player, _f, team_goals, win_prob) in enumerate(candidates[:top_n], start=1):
        results.append(
            PredictedScorer(
                name=player.name,
                team=player.team,
                position=player.position,
                score_probability=prob,
                rank=rank,
                rationale=_rationale(player, prob, team_goals, win_prob),
            )
        )
    return results
