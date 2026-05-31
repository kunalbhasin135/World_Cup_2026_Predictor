"""Squad availability and injury schemas."""

from typing import Literal

from pydantic import BaseModel, Field

InjuryStatus = Literal["fit", "doubtful", "out", "suspended", "recovering"]


class InjuryEntry(BaseModel):
    player: str
    status: InjuryStatus
    detail: str
    expected_return: str | None = None


class SquadStatus(BaseModel):
    team: str
    last_updated: str
    source: str = Field(description="curated | api-football | merged")
    injury_summary: str
    injuries: list[InjuryEntry] = Field(default_factory=list)
    squad_strength_modifier: float = Field(
        default=1.0,
        ge=0.85,
        le=1.05,
        description="Optional availability adjustment factor",
    )


class SquadStatusResponse(BaseModel):
    teams: list[SquadStatus]
    count: int
    data_source: str
    api_configured: bool
