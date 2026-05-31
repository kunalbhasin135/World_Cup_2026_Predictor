"""Data pipeline status routes."""

from fastapi import APIRouter

from app.models.schemas import DataStatusResponse
from app.services.data import feature_store
from app.services.ml import model_loader
from app.services.prediction import feature_provider
from app.services.prediction import probability_model

router = APIRouter(tags=["data"])


@router.get("/data/status", response_model=DataStatusResponse)
def get_data_status() -> DataStatusResponse:
    """Report feature data source and trained model availability."""
    return DataStatusResponse(
        feature_source=feature_provider.data_source(),
        probability_model=probability_model.model_source(),
        historical_data_available=feature_store.processed_data_available(),
        model_available=model_loader.model_available(),
        teams_with_features=len(feature_store.load_processed_team_features()),
        metadata=feature_store.load_metadata(),
        model_metadata=model_loader.load_model_metadata(),
    )
