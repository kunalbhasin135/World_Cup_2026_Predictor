"""Load and serve static team profiles from JSON files (Phase 3 data)."""

import json
import re
from functools import lru_cache
from pathlib import Path

from app.core.config import settings
from app.models.schemas import TeamProfile
from app.services.exceptions import TeamNotFoundError


def _normalize_team_key(team_name: str) -> str:
    """Convert display name to filename-safe slug, e.g. 'Argentina' -> 'argentina'."""
    slug = team_name.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def _profile_path(team_name: str) -> Path:
    return settings.PROFILES_DIR / f"{_normalize_team_key(team_name)}.json"


@lru_cache(maxsize=128)
def _load_profile_from_disk(slug: str) -> TeamProfile | None:
    path = settings.PROFILES_DIR / f"{slug}.json"
    if not path.is_file():
        return None
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return TeamProfile.model_validate(data)


def list_available_teams() -> list[str]:
    """Return sorted team names derived from profile JSON filenames."""
    if not settings.PROFILES_DIR.is_dir():
        return []
    teams: list[str] = []
    for path in sorted(settings.PROFILES_DIR.glob("*.json")):
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        teams.append(data.get("name", path.stem.replace("-", " ").title()))
    return teams


def get_team_profile(team_name: str) -> TeamProfile:
    slug = _normalize_team_key(team_name)
    profile = _load_profile_from_disk(slug)
    if profile is None:
        raise TeamNotFoundError(team_name)
    return profile


def profile_exists(team_name: str) -> bool:
    return _profile_path(team_name).is_file()
