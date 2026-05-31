"""Load processed feature artifacts built from historical match data."""

import json
from functools import lru_cache
from pathlib import Path

from app.core.config import settings


@lru_cache(maxsize=1)
def processed_data_available() -> bool:
    team_path = settings.PROCESSED_DATA_DIR / "team_features.json"
    return team_path.is_file()


@lru_cache(maxsize=1)
def load_processed_team_features() -> dict[str, dict]:
    path = settings.PROCESSED_DATA_DIR / "team_features.json"
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_processed_h2h() -> dict[str, dict]:
    path = settings.PROCESSED_DATA_DIR / "head_to_head.json"
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_metadata() -> dict:
    path = settings.PROCESSED_DATA_DIR / "metadata.json"
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def clear_cache() -> None:
    """Clear cached processed data (useful after rebuild)."""
    load_processed_team_features.cache_clear()
    load_processed_h2h.cache_clear()
    load_metadata.cache_clear()
    processed_data_available.cache_clear()
