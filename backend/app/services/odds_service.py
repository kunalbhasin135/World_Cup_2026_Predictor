"""Convert model win probabilities into book-style implied odds."""

from __future__ import annotations

from app.models.schemas import MatchImpliedOdds, MatchProbabilities, OutcomeOdds

# Typical 1X2 overround (~5% margin split across outcomes)
DEFAULT_MARGIN = 0.05
KNOCKOUT_MARGIN = 0.04


def _decimal_odds(probability_pct: float, margin: float) -> float:
    """Fair decimal odds with vig: lower implied prob → higher quoted price."""
    p = max(probability_pct / 100.0, 0.001)
    adjusted = p * (1.0 + margin)
    return round(1.0 / adjusted, 2)


def _fractional_odds(decimal: float) -> str:
    if decimal >= 2.0:
        num = round(decimal - 1, 2)
        return f"{num}/1"
    den = round(1 / max(decimal - 1, 0.01), 2)
    return f"1/{den}"


def _american_odds(decimal: float) -> int:
    if decimal >= 2.0:
        return int(round((decimal - 1) * 100))
    return int(round(-100 / max(decimal - 1, 0.01)))


def _build_outcome(label: str, probability_pct: float, margin: float) -> OutcomeOdds:
    decimal = _decimal_odds(probability_pct, margin)
    return OutcomeOdds(
        label=label,
        probability_pct=round(probability_pct, 1),
        decimal_odds=decimal,
        fractional_odds=_fractional_odds(decimal),
        american_odds=_american_odds(decimal),
    )


def implied_odds_from_probabilities(
    team_a: str,
    team_b: str,
    probabilities: MatchProbabilities,
    *,
    knockout: bool = False,
    match_round: str | None = None,
) -> MatchImpliedOdds:
    """
    Map ML percentages to decimal / fractional / American prices.

    These are model-implied lines (not live sportsbook feeds).
    """
    margin = KNOCKOUT_MARGIN if knockout else DEFAULT_MARGIN
    market_type = "match_winner" if knockout else "1x2"

    outcomes = [
        _build_outcome(team_a, probabilities.team_a_win, margin),
        _build_outcome(team_b, probabilities.team_b_win, margin),
    ]
    if not knockout and probabilities.draw > 0.05:
        outcomes.insert(1, _build_outcome("Draw", probabilities.draw, margin))

    round_note = f" for {match_round}" if match_round else ""
    return MatchImpliedOdds(
        market_type=market_type,
        book_margin_pct=round(margin * 100, 1),
        outcomes=outcomes,
        disclaimer=(
            "Model-implied prices from ML win probabilities — not live sportsbook odds. "
            f"Includes ~{int(margin * 100)}% book margin{round_note}."
        ),
    )
