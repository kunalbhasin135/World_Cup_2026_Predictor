"""
Official FIFA World Cup 2026 knockout bracket.

- Fixed R32/R16/QF/SF/F paths per tournament regulations
- Third-place R32 opponents resolved via Annex C (495 combinations)
"""

from __future__ import annotations

import json
from functools import lru_cache

from app.core.config import settings
from app.models.bracket_schemas import BracketRound, GroupPrediction, KnockoutMatchPrediction
from app.services.bracket_match import knockout_match, select_third_place_advancers

ROUND_LABELS = {
    "round_of_32": "Round of 32",
    "round_of_16": "Round of 16",
    "quarter_finals": "Quarter-finals",
    "semi_finals": "Semi-finals",
    "third_place": "Third place",
    "final": "Final",
}


@lru_cache(maxsize=1)
def _load_template() -> dict:
    path = settings.DATA_DIR / "bracket" / "official_knockout_template.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _load_third_combinations() -> dict[str, dict[str, str]]:
    path = settings.DATA_DIR / "bracket" / "third_place_combinations.json"
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data["combinations"]


def _group_tables(group_predictions: list[GroupPrediction]) -> dict[str, dict[int, str]]:
    """Map group letter -> {position: team_name}."""
    tables: dict[str, dict[int, str]] = {}
    for gp in group_predictions:
        tables[gp.group] = {s.position: s.team for s in gp.standings}
    return tables


def _qualified_third_groups(
    group_predictions: list[GroupPrediction],
    third_advancers: set[str],
) -> frozenset[str]:
    groups: set[str] = set()
    for gp in group_predictions:
        for s in gp.standings:
            if s.position == 3 and s.team in third_advancers:
                groups.add(gp.group)
    return frozenset(groups)


def _third_place_mapping(qualified_third_groups: frozenset[str]) -> dict[str, str]:
    """Slot (1A, 1B, …) -> group letter supplying the third-placed team."""
    key = "".join(sorted(qualified_third_groups))
    combos = _load_third_combinations()
    if key not in combos:
        raise KeyError(
            f"No Annex C mapping for third-place combination '{key}'. "
            f"Expected one of {len(combos)} FIFA combinations."
        )
    return combos[key]


def _resolve_pair_token(
    token: str,
    tables: dict[str, dict[int, str]],
    third_mapping: dict[str, str],
    winners: dict[str, str],
    match_participants: dict[str, tuple[str, str]],
) -> str:
    if token.startswith("W:"):
        return winners[token[2:]]
    if token.startswith("L:"):
        mid = token[2:]
        ta, tb = match_participants[mid]
        w = winners[mid]
        return tb if w == ta else ta
    if token.startswith("3:"):
        slot = token[2:]
        group = third_mapping[slot]
        return tables[group][3]
    if len(token) == 2 and token[0] in "12" and token[1].isalpha():
        pos = int(token[0])
        group = token[1]
        return tables[group][pos]
    raise ValueError(f"Unknown bracket token: {token}")


def _play_round(
    round_name: str,
    fixtures: list[dict] | dict,
    tables: dict[str, dict[int, str]],
    third_mapping: dict[str, str],
    winners: dict[str, str],
    match_participants: dict[str, tuple[str, str]],
    *,
    overrides: dict[str, str] | None,
    rng,
) -> list[KnockoutMatchPrediction]:
    items = [fixtures] if isinstance(fixtures, dict) else fixtures
    matches: list[KnockoutMatchPrediction] = []
    for fx in items:
        mid = fx["id"]
        ta = _resolve_pair_token(fx["team_a"], tables, third_mapping, winners, match_participants)
        tb = _resolve_pair_token(fx["team_b"], tables, third_mapping, winners, match_participants)
        match_participants[mid] = (ta, tb)
        m = knockout_match(round_name, mid, ta, tb, overrides=overrides, rng=rng)
        matches.append(m)
        winners[mid] = m.predicted_winner
    return matches


def build_official_knockout(
    group_predictions: list[GroupPrediction],
    *,
    overrides: dict[str, str] | None = None,
    rng=None,
) -> tuple[dict[str, list[KnockoutMatchPrediction]], list[BracketRound]]:
    """
    Build knockout rounds using FIFA paths and Annex C third-place assignment.
    """
    template = _load_template()
    tables = _group_tables(group_predictions)

    all_thirds: list[dict] = []
    for gp in group_predictions:
        for s in gp.standings:
            if s.position == 3:
                all_thirds.append(
                    {
                        "team": s.team,
                        "group": gp.group,
                        "points": s.points,
                        "gd": s.goal_difference,
                        "goals_for": s.goals_for,
                    }
                )

    third_advancers = select_third_place_advancers(all_thirds)
    qualified_groups = _qualified_third_groups(group_predictions, third_advancers)
    third_mapping = _third_place_mapping(qualified_groups)

    winners: dict[str, str] = {}
    match_participants: dict[str, tuple[str, str]] = {}
    knockout: dict[str, list[KnockoutMatchPrediction]] = {}
    tree: list[BracketRound] = []

    for key in (
        "round_of_32",
        "round_of_16",
        "quarter_finals",
        "semi_finals",
    ):
        label = ROUND_LABELS[key]
        matches = _play_round(
            label,
            template[key],
            tables,
            third_mapping,
            winners,
            match_participants,
            overrides=overrides,
            rng=rng,
        )
        knockout[label] = matches
        tree.append(BracketRound(round=label, matches=matches))

    tp_label = ROUND_LABELS["third_place"]
    tp_matches = _play_round(
        tp_label,
        template["third_place"],
        tables,
        third_mapping,
        winners,
        match_participants,
        overrides=overrides,
        rng=rng,
    )
    knockout[tp_label] = tp_matches
    tree.append(BracketRound(round=tp_label, matches=tp_matches))

    final_label = ROUND_LABELS["final"]
    final_matches = _play_round(
        final_label,
        template["final"],
        tables,
        third_mapping,
        winners,
        match_participants,
        overrides=overrides,
        rng=rng,
    )
    knockout[final_label] = final_matches
    tree.append(BracketRound(round=final_label, matches=final_matches))

    return knockout, tree


def normalize_override_ids(overrides: dict[str, str] | None) -> dict[str, str] | None:
    """Accept legacy R32-1 style IDs and map to M73+ where possible."""
    if not overrides:
        return overrides
    legacy_r32 = {f"R32-{i}": f"M{72 + i}" for i in range(1, 17)}
    legacy_r16 = {f"R16-{i}": f"M{88 + i}" for i in range(1, 9)}  # approximate — prefer M ids
    # Official R16 ids are M89,M90,... not sequential R16-N — document M ids only
    out: dict[str, str] = {}
    for k, v in overrides.items():
        out[legacy_r32.get(k, k)] = v
    return out
