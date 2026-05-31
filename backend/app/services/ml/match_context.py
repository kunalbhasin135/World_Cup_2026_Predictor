"""Match context features: venue, tournament importance, rest days."""

from __future__ import annotations

import re


def tournament_importance(tournament: str) -> float:
    """0–1 scale: friendlies low, World Cup highest."""
    t = (tournament or "").lower()
    if "world cup" in t or "fifa world" in t:
        return 1.0
    if any(k in t for k in ("euro", "copa america", "copa américa", "africa cup", "asian cup", "gold cup")):
        return 0.88
    if "nations league" in t:
        return 0.75
    if "qualif" in t or "qualification" in t:
        return 0.68
    if "friendly" in t or "friendship" in t:
        return 0.22
    if "confederations" in t:
        return 0.92
    return 0.45


def sample_weight_for_tournament(tournament: str) -> float:
    """Training sample weight — competitive matches weighted higher."""
    imp = tournament_importance(tournament)
    return 0.25 + imp * 0.85


def is_neutral_venue(neutral: bool | str | None) -> float:
    """Return 1.0 for neutral, 0.0 for home/away fixture."""
    if neutral is None:
        return 0.5
    if isinstance(neutral, str):
        return 1.0 if neutral.strip().upper() in ("TRUE", "T", "1", "YES") else 0.0
    return 1.0 if neutral else 0.0


def normalize_rest_days(days: float | None, cap: float = 14.0) -> float:
    """Days since last match, capped and scaled to 0–1."""
    if days is None or days < 0:
        return 0.5
    return min(float(days) / cap, 1.0)


def world_cup_inference_context() -> dict[str, float]:
    """Default context for World Cup 2026 predictions (neutral, full importance)."""
    return {
        "is_neutral": 1.0,
        "tournament_importance": 1.0,
        "rest_days_a": normalize_rest_days(7.0),
        "rest_days_b": normalize_rest_days(7.0),
    }


def parse_tournament_from_row(tournament: str) -> str:
    return re.sub(r"\s+", " ", (tournament or "").strip())
