"""Feature engineering from historical international match results."""

from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import pandas as pd

from app.core.config import settings
from app.services.data.match_loader import load_results, resolve_team_in_dataset, to_team_centric_frame
from app.services.data.team_aliases import to_display_name
from app.services import team_service


def _result_char(goals_for: int, goals_against: int) -> str:
    if goals_for > goals_against:
        return "W"
    if goals_for < goals_against:
        return "L"
    return "D"


def compute_elo_ratings(df: pd.DataFrame, k: float = 32.0, home_advantage: float = 65.0) -> dict[str, float]:
    """Simple Elo updated chronologically over all international matches."""
    ratings: dict[str, float] = {}

    def get_rating(team: str) -> float:
        return ratings.get(team, 1500.0)

    for row in df.sort_values("date").itertuples(index=False):
        home, away = row.home_team, row.away_team
        rh, ra = get_rating(home), get_rating(away)
        expected_home = 1.0 / (1.0 + 10 ** ((ra - rh - home_advantage) / 400.0))
        if row.home_score > row.away_score:
            score_home = 1.0
        elif row.home_score < row.away_score:
            score_home = 0.0
        else:
            score_home = 0.5

        ratings[home] = rh + k * (score_home - expected_home)
        ratings[away] = ra + k * ((1.0 - score_home) - (1.0 - expected_home))

    return ratings


def _elo_to_strength(elo: float) -> float:
    """Map Elo (~1200–2100) to a 0–100 strength rating."""
    return round(float(max(55.0, min(98.0, (elo - 1350.0) / 9.0))), 1)


def _form_index(wins: int, draws: int, losses: int) -> float:
    points = wins * 3 + draws
    max_points = (wins + draws + losses) * 3
    if max_points == 0:
        return 0.5
    return round(points / max_points, 2)


def _estimate_possession(form_index: float, goal_diff: float) -> float:
    """Proxy — possession not in results CSV; derived from form and scoring."""
    return round(max(40.0, min(65.0, 44.0 + form_index * 12.0 + goal_diff * 3.0)), 1)


def build_team_features(
    team_matches: pd.DataFrame,
    elo: float,
    display_name: str,
) -> dict:
    """Compute feature dict for one team from its chronological match rows."""
    recent = team_matches.sort_values("date", ascending=False)

    last_5 = recent.head(5)
    last_10 = recent.head(10)

    last_5_chars = [_result_char(r.goals_for, r.goals_against) for r in last_5.itertuples()]
    last_5_wins = sum(1 for c in last_5_chars if c == "W")
    last_5_draws = sum(1 for c in last_5_chars if c == "D")
    last_5_losses = sum(1 for c in last_5_chars if c == "L")

    scored_10 = last_10["goals_for"].mean() if len(last_10) else 0.0
    conceded_10 = last_10["goals_against"].mean() if len(last_10) else 0.0
    gd_10 = scored_10 - conceded_10

    form = _form_index(last_5_wins, last_5_draws, last_5_losses)
    possession = _estimate_possession(form, gd_10)

    return {
        "team_name": display_name,
        "strength_rating": _elo_to_strength(elo),
        "elo_rating": round(elo, 1),
        "last_5_results": "-".join(last_5_chars) if last_5_chars else "N/A",
        "last_5_wins": last_5_wins,
        "last_5_draws": last_5_draws,
        "last_5_losses": last_5_losses,
        "last_10_goals_scored_avg": round(float(scored_10), 2),
        "last_10_goals_conceded_avg": round(float(conceded_10), 2),
        "last_10_goal_difference": round(float(gd_10), 2),
        "form_index": form,
        "possession_avg": possession,
        "midfield_control_index": round(min(0.95, 0.45 + form * 0.35 + gd_10 * 0.08), 2),
        "transition_threat_index": round(min(0.95, 0.40 + float(scored_10) / 4.0), 2),
        "total_matches": int(len(team_matches)),
    }


def build_head_to_head(
    df: pd.DataFrame,
    team_a_display: str,
    team_b_display: str,
    dataset_a: str,
    dataset_b: str,
    recent_years: int = 30,
) -> dict:
    """Head-to-head record from match history (team_a = request order)."""
    cutoff = df["date"].max() - pd.DateOffset(years=recent_years)
    mask = (
        ((df["home_team"] == dataset_a) & (df["away_team"] == dataset_b))
        | ((df["home_team"] == dataset_b) & (df["away_team"] == dataset_a))
    ) & (df["date"] >= cutoff)

    meetings = df[mask].sort_values("date")
    if meetings.empty:
        return {
            "team_a_wins": 0,
            "draws": 0,
            "team_b_wins": 0,
            "recent_meetings": 0,
            "summary": f"No recorded meetings between {team_a_display} and {team_b_display} in the last {recent_years} years.",
        }

    a_wins = b_wins = draws = 0
    for row in meetings.itertuples(index=False):
        if row.home_score == row.away_score:
            draws += 1
        elif row.home_team == dataset_a:
            if row.home_score > row.away_score:
                a_wins += 1
            else:
                b_wins += 1
        else:
            if row.home_score > row.away_score:
                b_wins += 1
            else:
                a_wins += 1

    last = meetings.iloc[-1]
    if last["home_team"] == dataset_a:
        last_score = f"{int(last['home_score'])}-{int(last['away_score'])}"
        if last["home_score"] > last["away_score"]:
            last_winner = team_a_display
        elif last["home_score"] < last["away_score"]:
            last_winner = team_b_display
        else:
            last_winner = "draw"
    else:
        last_score = f"{int(last['away_score'])}-{int(last['home_score'])}"
        if last["away_score"] > last["home_score"]:
            last_winner = team_a_display
        elif last["away_score"] < last["home_score"]:
            last_winner = team_b_display
        else:
            last_winner = "draw"

    total = a_wins + b_wins + draws
    return {
        "team_a_wins": a_wins,
        "draws": draws,
        "team_b_wins": b_wins,
        "recent_meetings": total,
        "last_meeting_score": last_score,
        "last_meeting_winner": last_winner,
        "last_meeting_date": last["date"].strftime("%Y-%m-%d"),
        "summary": (
            f"{team_a_display} and {team_b_display} have met {total} times since "
            f"{cutoff.year} ({a_wins}W-{draws}D-{b_wins}L from {team_a_display}'s perspective)."
        ),
    }


def build_all_features(
    profile_teams: list[str] | None = None,
    results_path: Path | None = None,
    extra_teams: list[str] | None = None,
    min_matches: int = 50,
    min_year: int = 2000,
) -> tuple[dict[str, dict], dict[str, dict]]:
    """
    Build team features and head-to-head maps.

    Includes profile teams plus any extra teams (e.g. full World Cup bracket).
    Also auto-discovers national teams with enough match history in the dataset.
    """
    df = load_results(results_path)
    df_recent = df[df["date"].dt.year >= min_year]
    team_frame = to_team_centric_frame(df_recent)
    elo_map = compute_elo_ratings(df)

    requested: set[str] = set(profile_teams or team_service.list_available_teams())
    if extra_teams:
        requested.update(extra_teams)

    # Auto-include teams with sufficient recent international history
    match_counts = team_frame.groupby("team").size()
    for dataset_name, count in match_counts.items():
        if count >= min_matches:
            requested.add(to_display_name(dataset_name))

    team_features: dict[str, dict] = {}
    for display_name in sorted(requested):
        dataset_name = resolve_team_in_dataset(df, display_name)
        if dataset_name is None:
            continue
        matches = team_frame[team_frame["team"] == dataset_name]
        if len(matches) < 10:
            continue
        features = build_team_features(
            matches, elo_map.get(dataset_name, 1500.0), display_name
        )
        team_features[display_name] = features

    h2h_records: dict[str, dict] = {}
    available = sorted(team_features.keys())
    for a, b in combinations(available, 2):
        ds_a = resolve_team_in_dataset(df, a)
        ds_b = resolve_team_in_dataset(df, b)
        if not ds_a or not ds_b:
            continue
        key = f"{a}|{b}"
        h2h_records[key] = build_head_to_head(df_recent, a, b, ds_a, ds_b)

    return team_features, h2h_records


def save_processed_features(
    team_features: dict[str, dict],
    h2h_records: dict[str, dict],
    output_dir: Path | None = None,
) -> tuple[Path, Path]:
    """Write processed JSON files consumed by the prediction engine."""
    out = output_dir or settings.PROCESSED_DATA_DIR
    out.mkdir(parents=True, exist_ok=True)

    team_path = out / "team_features.json"
    h2h_path = out / "head_to_head.json"
    meta_path = out / "metadata.json"

    with team_path.open("w", encoding="utf-8") as f:
        json.dump(team_features, f, indent=2)

    with h2h_path.open("w", encoding="utf-8") as f:
        json.dump(h2h_records, f, indent=2)

    metadata = {
        "source": "martj42/international_results (Kaggle-equivalent)",
        "teams_count": len(team_features),
        "h2h_pairs_count": len(h2h_records),
        "generated_from": str(settings.RAW_DATA_DIR / "results.csv"),
    }
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return team_path, h2h_path
