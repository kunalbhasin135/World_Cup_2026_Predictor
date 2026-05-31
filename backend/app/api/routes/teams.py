"""Team profile routes."""

from fastapi import APIRouter, HTTPException, status

from app.models.schemas import TeamListResponse, TeamProfile
from app.models.squad_schemas import SquadStatus, SquadStatusResponse
from app.services.exceptions import TeamNotFoundError
from app.services import live_squad_service
from app.services.team_service import get_team_profile, list_available_teams

router = APIRouter(tags=["teams"])


@router.get("/teams", response_model=TeamListResponse)
def read_team_list() -> TeamListResponse:
    """Return all teams that have a static profile JSON file."""
    teams = list_available_teams()
    return TeamListResponse(teams=teams, count=len(teams))


@router.get("/team/{team_name}", response_model=TeamProfile)
def read_team_profile(team_name: str) -> TeamProfile:
    """Return the static scouting profile for a national team."""
    try:
        return get_team_profile(team_name)
    except TeamNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get("/squads/status", response_model=SquadStatusResponse)
def read_all_squad_status() -> SquadStatusResponse:
    """Structured injury / availability feed for tracked nations."""
    return live_squad_service.list_squad_statuses()


@router.get("/squads/{team_name}/status", response_model=SquadStatus)
def read_squad_status(team_name: str) -> SquadStatus:
    squad = live_squad_service.get_squad_status(team_name)
    if squad is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No squad status on file for '{team_name}'.",
        )
    return squad
