"""Generate human-readable explanations from features and model output."""

from app.models.domain import HeadToHeadRecord, TeamFeatures
from app.models.schemas import MatchProbabilities


def _unbeaten_streak(features: TeamFeatures) -> bool:
    return features.last_5_losses == 0


def _form_label(features: TeamFeatures) -> str:
    if features.form_index >= 0.82:
        return "excellent"
    if features.form_index >= 0.72:
        return "strong"
    if features.form_index >= 0.62:
        return "decent"
    return "mixed"


def generate_reasons(
    team_a: str,
    team_b: str,
    features_a: TeamFeatures,
    features_b: TeamFeatures,
    h2h: HeadToHeadRecord,
    probabilities: MatchProbabilities,
) -> list[str]:
    reasons: list[str] = []
    favored = team_a if probabilities.team_a_win >= probabilities.team_b_win else team_b
    favored_features = features_a if favored == team_a else features_b
    underdog_features = features_b if favored == team_a else features_a

    if _unbeaten_streak(features_a):
        reasons.append(f"{team_a} unbeaten in last {features_a.last_5_wins + features_a.last_5_draws} matches.")
    if _unbeaten_streak(features_b):
        reasons.append(f"{team_b} unbeaten in last {features_b.last_5_wins + features_b.last_5_draws} matches.")

    if features_a.last_10_goal_difference > features_b.last_10_goal_difference + 0.3:
        reasons.append(
            f"{team_a} has a stronger goal difference over the last 10 matches "
            f"({features_a.last_10_goal_difference:+.1f} vs {features_b.last_10_goal_difference:+.1f})."
        )
    elif features_b.last_10_goal_difference > features_a.last_10_goal_difference + 0.3:
        reasons.append(
            f"{team_b} has a stronger goal difference over the last 10 matches "
            f"({features_b.last_10_goal_difference:+.1f} vs {features_a.last_10_goal_difference:+.1f})."
        )

    if h2h.recent_meetings > 0 and not h2h.is_estimated:
        if h2h.team_a_wins > h2h.team_b_wins:
            reasons.append(
                f"{team_a} holds a better historical record against {team_b} "
                f"({h2h.team_a_wins}W-{h2h.draws}D-{h2h.team_b_wins}L in recent meetings)."
            )
        elif h2h.team_b_wins > h2h.team_a_wins:
            reasons.append(
                f"{team_b} holds a better historical record against {team_a} "
                f"({h2h.team_b_wins}W-{h2h.draws}D-{h2h.team_a_wins}L in recent meetings)."
            )
        else:
            reasons.append(
                f"Head-to-head record is balanced ({h2h.team_a_wins}W-{h2h.draws}D-{h2h.team_b_wins}L)."
            )

    if features_a.midfield_control_index > features_b.midfield_control_index + 0.08:
        reasons.append(
            f"{team_a} shows stronger midfield control and possession numbers "
            f"({features_a.possession_avg:.0f}% avg possession vs {features_b.possession_avg:.0f}%)."
        )
    elif features_b.midfield_control_index > features_a.midfield_control_index + 0.08:
        reasons.append(
            f"{team_b} shows stronger midfield control and possession numbers "
            f"({features_b.possession_avg:.0f}% avg possession vs {features_a.possession_avg:.0f}%)."
        )

    if features_b.transition_threat_index > features_a.transition_threat_index + 0.1:
        reasons.append(f"{team_b} is dangerous in transition and counterattack.")
    if features_a.transition_threat_index > features_b.transition_threat_index + 0.1:
        reasons.append(f"{team_a} is dangerous in transition and counterattack.")

    if favored_features.form_index > underdog_features.form_index + 0.05:
        reasons.append(
            f"{favored} currently entering in {_form_label(favored_features)} form "
            f"(form index {favored_features.form_index:.2f} vs {underdog_features.form_index:.2f})."
        )

    if features_a.strength_rating > features_b.strength_rating + 3:
        reasons.append(
            f"{team_a} rated higher on team strength ({features_a.strength_rating:.0f} vs {features_b.strength_rating:.0f})."
        )
    elif features_b.strength_rating > features_a.strength_rating + 3:
        reasons.append(
            f"{team_b} rated higher on team strength ({features_b.strength_rating:.0f} vs {features_a.strength_rating:.0f})."
        )

    if not reasons:
        reasons.append(
            f"{team_a} and {team_b} are closely matched on available metrics — expect a tight contest."
        )

    return reasons[:6]


def generate_matchup_analysis(
    team_a: str,
    team_b: str,
    features_a: TeamFeatures,
    features_b: TeamFeatures,
    h2h: HeadToHeadRecord,
    probabilities: MatchProbabilities,
    confidence: str,
) -> str:
    if probabilities.team_a_win >= probabilities.team_b_win and probabilities.team_a_win >= probabilities.draw:
        outcome = f"{team_a} win"
        pct = probabilities.team_a_win
    elif probabilities.team_b_win >= probabilities.team_a_win and probabilities.team_b_win >= probabilities.draw:
        outcome = f"{team_b} win"
        pct = probabilities.team_b_win
    else:
        outcome = "draw"
        pct = probabilities.draw

    form_a = _form_label(features_a)
    form_b = _form_label(features_b)

    analysis = (
        f"{team_a} vs {team_b} pits {form_a} form against {form_b} form. "
        f"The engine projects a {outcome} ({pct:.0f}%) with {confidence.lower()} confidence. "
    )
    if h2h.summary and not h2h.is_estimated:
        analysis += f"{h2h.summary} "
    analysis += (
        f"Strength ratings ({features_a.strength_rating:.0f} vs {features_b.strength_rating:.0f}) "
        f"and recent goal trends from historical international match data."
    )
    return analysis
