"""Load and normalize international match results."""

from pathlib import Path

import pandas as pd

from app.core.config import settings
from app.services.data.team_aliases import to_dataset_name, to_display_name


def load_results(path: Path | None = None) -> pd.DataFrame:
    """Load raw results CSV and normalize column types."""
    csv_path = path or settings.RAW_DATA_DIR / "results.csv"
    if not csv_path.is_file():
        raise FileNotFoundError(
            f"Results file not found at {csv_path}. "
            "Run: python scripts/build_features.py"
        )

    df = pd.read_csv(csv_path, parse_dates=["date"])
    df = df.dropna(subset=["home_team", "away_team", "home_score", "away_score"])
    df["home_score"] = df["home_score"].astype(int)
    df["away_score"] = df["away_score"].astype(int)
    df = df.sort_values("date").reset_index(drop=True)
    return df


def to_team_centric_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Expand each match into two rows — one per team perspective."""
    home = df.assign(
        team=df["home_team"],
        opponent=df["away_team"],
        goals_for=df["home_score"],
        goals_against=df["away_score"],
        is_home=True,
    )
    away = df.assign(
        team=df["away_team"],
        opponent=df["home_team"],
        goals_for=df["away_score"],
        goals_against=df["home_score"],
        is_home=False,
    )
    cols = ["date", "team", "opponent", "goals_for", "goals_against", "is_home", "tournament"]
    return pd.concat([home[cols], away[cols]], ignore_index=True).sort_values(
        ["team", "date"]
    )


def resolve_team_in_dataset(df: pd.DataFrame, display_name: str) -> str | None:
    """Return the dataset team name if the team has match history."""
    dataset_name = to_dataset_name(display_name)
    teams = set(df["home_team"]) | set(df["away_team"])
    if dataset_name in teams:
        return dataset_name
    if display_name in teams:
        return display_name
    return None
