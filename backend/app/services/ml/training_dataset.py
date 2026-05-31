"""Build point-in-time training dataset from chronological match history."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

import numpy as np
import pandas as pd

from app.services.data.feature_engineering import _elo_to_strength, _form_index
from app.services.data.match_loader import load_results
from app.services.ml.feature_vector import FEATURE_NAMES, build_match_vector_from_dicts
from app.services.ml.match_context import (
    is_neutral_venue,
    normalize_rest_days,
    sample_weight_for_tournament,
    tournament_importance,
)


def _rolling_team_features(matches: list[tuple[int, int]], elo: float) -> dict | None:
    if len(matches) < 5:
        return None

    recent = matches[-10:]
    last_5 = matches[-5:]
    last_5_chars = ["W" if gf > ga else "L" if gf < ga else "D" for gf, ga in last_5]
    last_5_wins = sum(1 for c in last_5_chars if c == "W")
    last_5_draws = sum(1 for c in last_5_chars if c == "D")
    last_5_losses = sum(1 for c in last_5_chars if c == "L")
    scored = sum(gf for gf, _ in recent) / len(recent)
    conceded = sum(ga for _, ga in recent) / len(recent)
    form = _form_index(last_5_wins, last_5_draws, last_5_losses)

    return {
        "strength_rating": _elo_to_strength(elo),
        "form_index": form,
        "last_10_goal_difference": round(scored - conceded, 3),
        "last_10_goals_scored_avg": round(scored, 3),
        "last_10_goals_conceded_avg": round(conceded, 3),
    }


def _h2h_advantage(home: str, away: str, pair_results: list[int]) -> float:
    if not pair_results:
        return 0.0
    a, _ = sorted([home, away])
    avg = sum(pair_results) / len(pair_results)
    return -avg if home != a else avg


def _days_since(last_date: datetime | None, current: datetime) -> float | None:
    if last_date is None:
        return None
    return max(0.0, (current - last_date).days)


def build_training_dataset(
    min_year: int = 2000,
    min_team_matches: int = 10,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Walk matches chronologically and build labeled rows without data leakage.

    Returns X, y (0=home win, 1=draw, 2=away win), sample_weights,
    y_home_goals, y_away_goals for Poisson models.
    """
    df = load_results()
    df = df[df["date"].dt.year >= min_year].sort_values("date").reset_index(drop=True)

    team_matches: dict[str, list[tuple[int, int]]] = defaultdict(list)
    last_match_date: dict[str, datetime] = {}
    pair_results: dict[tuple[str, str], list[int]] = defaultdict(list)
    elo: dict[str, float] = defaultdict(lambda: 1500.0)

    k = 32.0
    home_adv = 65.0

    X_rows: list[np.ndarray] = []
    y_rows: list[int] = []
    weight_rows: list[float] = []
    home_goals_rows: list[int] = []
    away_goals_rows: list[int] = []

    for row in df.itertuples(index=False):
        home, away = row.home_team, row.away_team
        hs, aws = int(row.home_score), int(row.away_score)
        match_date = pd.Timestamp(row.date).to_pydatetime()
        tournament = getattr(row, "tournament", "") or ""
        neutral = getattr(row, "neutral", False)

        home_feats = _rolling_team_features(team_matches[home], elo[home])
        away_feats = _rolling_team_features(team_matches[away], elo[away])

        if home_feats and away_feats:
            if len(team_matches[home]) >= min_team_matches and len(team_matches[away]) >= min_team_matches:
                pair_key = tuple(sorted([home, away]))
                h2h = _h2h_advantage(home, away, pair_results[pair_key])
                context = {
                    "is_neutral": is_neutral_venue(neutral),
                    "tournament_importance": tournament_importance(tournament),
                    "rest_days_a": normalize_rest_days(_days_since(last_match_date.get(home), match_date)),
                    "rest_days_b": normalize_rest_days(_days_since(last_match_date.get(away), match_date)),
                }
                vector = build_match_vector_from_dicts(home_feats, away_feats, h2h, context)
                if hs > aws:
                    label = 0
                elif hs == aws:
                    label = 1
                else:
                    label = 2
                X_rows.append(vector)
                y_rows.append(label)
                weight_rows.append(sample_weight_for_tournament(tournament))
                home_goals_rows.append(hs)
                away_goals_rows.append(aws)

        team_matches[home].append((hs, aws))
        team_matches[away].append((aws, hs))
        last_match_date[home] = match_date
        last_match_date[away] = match_date

        pair_key = tuple(sorted([home, away]))
        a, b = pair_key
        if hs == aws:
            result_for_a = 0
        elif (hs > aws and home == a) or (aws > hs and away == a):
            result_for_a = 1
        else:
            result_for_a = -1
        pair_results[pair_key].append(result_for_a)

        rh, ra = elo[home], elo[away]
        expected_home = 1.0 / (1.0 + 10 ** ((ra - rh - home_adv) / 400.0))
        score_home = 1.0 if hs > aws else 0.0 if hs < aws else 0.5
        elo[home] = rh + k * (score_home - expected_home)
        elo[away] = ra + k * ((1.0 - score_home) - (1.0 - expected_home))

    X = np.vstack(X_rows)
    y = np.array(y_rows, dtype=np.int64)
    weights = np.array(weight_rows, dtype=np.float64)
    y_home = np.array(home_goals_rows, dtype=np.int64)
    y_away = np.array(away_goals_rows, dtype=np.int64)
    return X, y, weights, y_home, y_away


def build_knockout_dataset(
    min_year: int = 2000,
    min_team_matches: int = 10,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Non-draw outcomes only: 0=team_a (home) win, 1=team_b (away) win."""
    X, y, weights, _, _ = build_training_dataset(min_year, min_team_matches)
    mask = y != 1
    y_ko = np.where(y[mask] == 0, 0, 1)
    return X[mask], y_ko, weights[mask]


def dataset_summary(y: np.ndarray) -> dict:
    total = len(y)
    return {
        "total_samples": total,
        "home_win_pct": round(100 * (y == 0).sum() / total, 1),
        "draw_pct": round(100 * (y == 1).sum() / total, 1),
        "away_win_pct": round(100 * (y == 2).sum() / total, 1),
        "feature_names": FEATURE_NAMES,
    }
