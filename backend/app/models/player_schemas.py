"""Player profile schemas."""

from pydantic import BaseModel, Field


class PlayerProfile(BaseModel):
    name: str
    team: str
    position: str
    role: str
    strengths: list[str]
    weaknesses: list[str]
    recent_form: str = Field(..., description="e.g. excellent, strong, mixed")
    intl_goals: int = 0
    intl_caps: int = 0
    scoring_threat_index: float = Field(..., ge=0, le=1)
    analysis: str
    watch_out_for: str


class PlayerAnalysis(BaseModel):
    """Player scouting card in a prediction response."""

    name: str
    team: str
    position: str
    role: str
    strengths: list[str]
    weaknesses: list[str]
    recent_form: str
    intl_goals: int
    intl_caps: int
    analysis: str
    watch_out_for: str
    injury_status: str | None = Field(
        default=None, description="fit | doubtful | out | suspended | recovering"
    )
    injury_detail: str | None = None


class PredictedScorer(BaseModel):
    name: str
    team: str
    position: str
    score_probability: float = Field(..., ge=0, le=100, description="Likelihood to score at least once (%)")
    rank: int
    rationale: str
