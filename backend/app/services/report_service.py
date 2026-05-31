"""Team report and tactical analysis helpers for prediction responses."""

from app.models.schemas import TeamReport
from app.services.exceptions import TeamNotFoundError
from app.services import live_squad_service, team_service


def profile_to_report(profile) -> TeamReport:
    return TeamReport(
        name=profile.name,
        style_of_play=profile.style_of_play,
        strengths=profile.strengths,
        weaknesses=profile.weaknesses,
        key_players=profile.key_players,
        injury_news=profile.injury_news,
        why_it_matters=profile.why_it_matters,
    )


def fallback_report(team_name: str) -> TeamReport:
    return TeamReport(
        name=team_name,
        style_of_play="Profile pending — add JSON in data/profiles/.",
        strengths=["Data not yet loaded"],
        weaknesses=["Data not yet loaded"],
        key_players=["TBD"],
        injury_news="No recent updates available.",
        why_it_matters=f"Full scouting report for {team_name} will be available once a profile is added.",
    )


def load_team_report(team_name: str) -> TeamReport:
    try:
        profile = team_service.get_team_profile(team_name)
        report = profile_to_report(profile)
        live_news = live_squad_service.build_injury_news(team_name)
        if live_news and "No structured injury" not in live_news:
            report = report.model_copy(update={"injury_news": live_news})
        return report
    except TeamNotFoundError:
        return fallback_report(team_name)


def build_tactical_matchup(
    team_a: str,
    team_b: str,
    report_a: TeamReport,
    report_b: TeamReport,
) -> list[str]:
    bullets = [
        f"{report_a.name}: {report_a.style_of_play}",
        f"{report_b.name}: {report_b.style_of_play}",
        f"Key battle — {report_a.name} ({', '.join(report_a.strengths[:2])}) "
        f"vs {report_b.name} ({', '.join(report_b.weaknesses[:2])}).",
    ]
    try:
        profile_a = team_service.get_team_profile(team_a)
        profile_b = team_service.get_team_profile(team_b)
        bullets.append(f"Tactical edge ({profile_a.name}): {profile_a.tactical_summary}")
        bullets.append(f"Counter-plan ({profile_b.name}): {profile_b.tactical_summary}")
    except TeamNotFoundError:
        pass
    return bullets
