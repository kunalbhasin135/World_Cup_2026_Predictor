"""World Cup bracket prediction routes."""

from fastapi import APIRouter, Query

from app.models.bracket_schemas import (
    BracketPredictionResponse,
    MonteCarloResponse,
    WhatIfRequest,
)
from app.services.bracket_service import get_bracket_prediction, predict_bracket
from app.services.monte_carlo_service import get_monte_carlo_cached

router = APIRouter(tags=["bracket"])


@router.get("/bracket/predictions", response_model=BracketPredictionResponse)
def read_bracket_predictions() -> BracketPredictionResponse:
    """Simulate the full World Cup 2026 group stage and knockout bracket (deterministic)."""
    return get_bracket_prediction()


@router.get("/bracket/monte-carlo", response_model=MonteCarloResponse)
def read_monte_carlo_bracket(
    simulations: int = Query(default=500, ge=50, le=2000),
    seed: int = Query(default=42, ge=0),
) -> MonteCarloResponse:
    """Run Monte Carlo bracket simulations and return champion odds."""
    return get_monte_carlo_cached(simulations, seed)


@router.post("/bracket/what-if", response_model=BracketPredictionResponse)
def what_if_bracket(request: WhatIfRequest) -> BracketPredictionResponse:
    """Re-simulate knockout bracket with forced match winners."""
    return predict_bracket(overrides=request.overrides)
