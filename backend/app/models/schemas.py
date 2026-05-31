"""Request and response schemas for the prediction API."""

from typing import Literal

from pydantic import BaseModel, Field

from app.models.player_schemas import PlayerAnalysis, PredictedScorer
from app.models.squad_schemas import SquadStatus


class PredictRequest(BaseModel):
    team_a: str = Field(..., min_length=1, description="Home or first team name")
    team_b: str = Field(..., min_length=1, description="Away or second team name")
    knockout: bool = Field(
        default=False,
        description="Use knockout model (no draw) — same as bracket elimination rounds",
    )
    match_round: str | None = Field(
        default=None,
        description=(
            "Tournament stage label, e.g. 'Semi-finals' — enables bracket path context "
            "(probability both teams reach this round and meet)"
        ),
    )


class OutcomeOdds(BaseModel):
    label: str
    probability_pct: float
    decimal_odds: float
    fractional_odds: str
    american_odds: int


class MatchImpliedOdds(BaseModel):
    market_type: str = Field(description="1x2 or match_winner")
    book_margin_pct: float
    outcomes: list[OutcomeOdds]
    disclaimer: str


class BracketMatchupContext(BaseModel):
    """How likely a fixture happens at a given round, from Monte Carlo bracket sims."""

    round: str
    team_a: str
    team_b: str
    simulations: int
    both_reach_round_pct: float = Field(
        description="Both teams appear in this knockout round (any slot)"
    )
    face_in_round_pct: float = Field(
        description="Teams are paired in the same fixture in this round"
    )
    team_a_wins_if_meet_pct: float | None = Field(
        default=None,
        description="When paired in sims, % team_a wins (stochastic knockout sample)"
    )
    scenario_note: str


class CompareMatchupPair(BaseModel):
    team_a: str
    team_b: str


class CompareRequest(BaseModel):
    """Compare multiple matchups side-by-side."""

    matchups: list[CompareMatchupPair] = Field(..., min_length=2, max_length=4)


class FeatureContribution(BaseModel):
    feature: str
    value: float
    impact: float


class ModelInfo(BaseModel):
    probability_model: str
    score_model: str
    feature_source: str
    test_accuracy: float | None = None
    log_loss: float | None = None
    brier_score: float | None = None
    trained_at: str | None = None
    feature_contributions: list[FeatureContribution] = Field(default_factory=list)


class CompareMatchupResult(BaseModel):
    team_a: str
    team_b: str
    probabilities: "MatchProbabilities"
    predicted_score: "PredictedScore"
    confidence: "ConfidenceLevel"
    favored_team: str
    implied_odds: MatchImpliedOdds | None = None


class CompareResponse(BaseModel):
    matchups: list[CompareMatchupResult]
    model_info: ModelInfo


class MatchProbabilities(BaseModel):
    team_a_win: float = Field(..., ge=0, le=100, description="Win probability for team A (%)")
    draw: float = Field(..., ge=0, le=100, description="Draw probability (%)")
    team_b_win: float = Field(..., ge=0, le=100, description="Win probability for team B (%)")


class PredictedScore(BaseModel):
    team_a: int = Field(..., ge=0)
    team_b: int = Field(..., ge=0)


ConfidenceLevel = Literal["Low", "Medium", "High"]


class RecentFormSnapshot(BaseModel):
    """Recent form metrics for one team (placeholder until dataset is connected)."""

    last_5_results: str = Field(..., description="e.g. W-W-D-L-W")
    goals_scored_avg: float
    goals_conceded_avg: float
    goal_difference: float


class TeamReport(BaseModel):
    """Scouting-style report embedded in a prediction response."""

    name: str
    style_of_play: str
    strengths: list[str]
    weaknesses: list[str]
    key_players: list[str]
    injury_news: str
    why_it_matters: str


class PredictResponse(BaseModel):
    team_a: str
    team_b: str
    probabilities: MatchProbabilities
    predicted_score: PredictedScore
    confidence: ConfidenceLevel
    favored_team: str
    implied_odds: MatchImpliedOdds | None = None
    bracket_context: BracketMatchupContext | None = None
    squad_status: dict[str, SquadStatus] = Field(default_factory=dict)
    reasons: list[str]
    tactical_matchup: list[str]
    recent_form: dict[str, RecentFormSnapshot]
    team_reports: dict[str, TeamReport]
    matchup_analysis: str
    player_analysis: dict[str, list[PlayerAnalysis]]
    predicted_scorers: list[PredictedScorer]
    model_info: ModelInfo | None = None


class TeamProfile(BaseModel):
    """Static team profile served by GET /team/{team_name}."""

    name: str
    country_code: str | None = None
    style_of_play: str
    strengths: list[str]
    weaknesses: list[str]
    key_players: list[str]
    tactical_summary: str
    why_it_matters: str
    injury_news: str = "No recent updates available."


class TeamListResponse(BaseModel):
    teams: list[str]
    count: int


class DataStatusResponse(BaseModel):
    feature_source: str
    probability_model: str
    historical_data_available: bool
    model_available: bool
    teams_with_features: int
    metadata: dict
    model_metadata: dict


class ApiInfoResponse(BaseModel):
    name: str
    version: str
    description: str
    endpoints: dict[str, str]
