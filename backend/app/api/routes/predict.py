"""Match prediction routes."""

from fastapi import APIRouter, HTTPException, status

from app.models.schemas import CompareRequest, CompareResponse, PredictRequest, PredictResponse
from app.services.exceptions import InvalidMatchupError
from app.services.prediction_service import compare_matchups, predict_match

router = APIRouter(tags=["predictions"])


@router.post("/predict", response_model=PredictResponse)
def create_prediction(request: PredictRequest) -> PredictResponse:
    """Predict the outcome of a match between two national teams."""
    try:
        return predict_match(request)
    except InvalidMatchupError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/predict/compare", response_model=CompareResponse)
def compare_predictions(request: CompareRequest) -> CompareResponse:
    """Compare 2–4 matchups side-by-side with shared model metadata."""
    try:
        return compare_matchups(request)
    except InvalidMatchupError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
