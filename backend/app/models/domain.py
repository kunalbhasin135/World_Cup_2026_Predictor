"""Internal domain models for the prediction engine (not exposed via API)."""

from typing import Literal

from pydantic import BaseModel, Field

ConfidenceLevel = Literal["Low", "Medium", "High"]


class TeamFeatures(BaseModel):
    """Feature vector for one team — placeholder now, dataset-driven in Phase 5."""

    team_name: str
    strength_rating: float = Field(..., ge=0, le=100)
    last_5_results: str
    last_5_wins: int = Field(..., ge=0)
    last_5_draws: int = Field(..., ge=0)
    last_5_losses: int = Field(..., ge=0)
    last_10_goals_scored_avg: float = Field(..., ge=0)
    last_10_goals_conceded_avg: float = Field(..., ge=0)
    last_10_goal_difference: float
    form_index: float = Field(..., ge=0, le=1)
    possession_avg: float = Field(..., ge=0, le=100)
    midfield_control_index: float = Field(default=0.5, ge=0, le=1)
    transition_threat_index: float = Field(default=0.5, ge=0, le=1)


class HeadToHeadRecord(BaseModel):
    """Head-to-head summary between two teams (team_a is the request's first team)."""

    team_a: str
    team_b: str
    team_a_wins: int = 0
    draws: int = 0
    team_b_wins: int = 0
    recent_meetings: int = 0
    last_meeting_score: str | None = None
    last_meeting_winner: str | None = None
    summary: str = "Limited head-to-head data available for this pairing."
    is_estimated: bool = False

    @property
    def team_a_win_rate(self) -> float:
        if self.recent_meetings == 0:
            return 0.33
        return self.team_a_wins / self.recent_meetings

    @property
    def advantage_score(self) -> float:
        """Normalized H2H edge for team_a in [-1, 1]."""
        if self.recent_meetings == 0:
            return 0.0
        return (self.team_a_wins - self.team_b_wins) / self.recent_meetings


class EnginePrediction(BaseModel):
    """Raw output from the prediction engine before API enrichment."""

    team_a: str
    team_b: str
    team_a_win_prob: float
    draw_prob: float
    team_b_win_prob: float
    predicted_score_a: int
    predicted_score_b: int
    confidence: ConfidenceLevel
    reasons: list[str]
    features_a: TeamFeatures
    features_b: TeamFeatures
    head_to_head: HeadToHeadRecord
