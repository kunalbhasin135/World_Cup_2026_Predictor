"""Root and metadata routes."""

from fastapi import APIRouter

from app.core.config import settings
from app.models.schemas import ApiInfoResponse

router = APIRouter(tags=["meta"])


@router.get("/", response_model=ApiInfoResponse)
def get_api_info() -> ApiInfoResponse:
    """Return API metadata and available endpoints."""
    return ApiInfoResponse(
        name=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Predict international football match outcomes with analytics and scouting reports.",
        endpoints={
            "health": "GET /health",
            "predict": "POST /predict",
            "compare": "POST /predict/compare",
            "teams": "GET /teams",
            "team_profile": "GET /team/{team_name}",
            "data_status": "GET /data/status",
            "bracket": "GET /bracket/predictions",
            "monte_carlo": "GET /bracket/monte-carlo",
            "what_if": "POST /bracket/what-if",
            "docs": "GET /docs",
        },
    )
