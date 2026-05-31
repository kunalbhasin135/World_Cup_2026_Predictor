"""Monte Carlo World Cup bracket simulation."""

from __future__ import annotations

from collections import Counter
from functools import lru_cache

import numpy as np

from app.models.bracket_schemas import BracketPredictionResponse, MonteCarloResponse, TeamChampionOdds
from app.services.bracket_service import _load_groups, _run_group_stage, predict_bracket
from app.services.prediction import feature_provider
from app.services.prediction import probability_model


def run_monte_carlo(simulations: int = 500, seed: int = 42) -> MonteCarloResponse:
    """
    Run N stochastic knockout simulations.

    Group stage runs once (deterministic); knockout rounds are sampled from ML probabilities.
    """
    simulations = max(50, min(simulations, 2000))
    data = _load_groups()
    groups_raw: dict[str, list[str]] = data["groups"]
    group_predictions = _run_group_stage(groups_raw, rng=None)

    rng = np.random.default_rng(seed)
    champion_counts: Counter[str] = Counter()
    finalist_counts: Counter[str] = Counter()

    for _ in range(simulations):
        sim_rng = np.random.default_rng(rng.integers(0, 2**31 - 1))
        result = predict_bracket(
            rng=sim_rng,
            fixed_groups=group_predictions,
        )
        champion_counts[result.champion] += 1
        finalist_counts[result.champion] += 1
        finalist_counts[result.runner_up] += 1

    most_likely = predict_bracket(fixed_groups=group_predictions)

    odds = [
        TeamChampionOdds(
            team=team,
            champion_pct=round(100 * count / simulations, 1),
            finalist_pct=round(100 * finalist_counts[team] / simulations, 1),
        )
        for team, count in champion_counts.most_common()
    ]

    sim_favorite = odds[0].team if odds else most_likely.champion

    return MonteCarloResponse(
        simulations=simulations,
        seed=seed,
        prediction_model=probability_model.model_source(),
        feature_source=feature_provider.data_source(),
        champion_odds=odds[:16],
        simulated_champion_favorite=sim_favorite,
        deterministic_champion=most_likely.champion,
        most_likely_champion=sim_favorite,
        most_likely_bracket=most_likely,
    )


@lru_cache(maxsize=4)
def get_monte_carlo_cached(simulations: int, seed: int) -> MonteCarloResponse:
    return run_monte_carlo(simulations, seed)


def clear_monte_carlo_cache() -> None:
    get_monte_carlo_cached.cache_clear()
