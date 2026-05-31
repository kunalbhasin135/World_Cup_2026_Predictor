"""Bracket prediction response schemas."""

from pydantic import BaseModel, Field

from app.models.schemas import PredictedScore


class GroupStanding(BaseModel):
    team: str
    position: int
    played: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int
    advances: bool
    advancement_note: str | None = None


class GroupPrediction(BaseModel):
    group: str
    teams: list[str]
    standings: list[GroupStanding]


class KnockoutMatchPrediction(BaseModel):
    round: str
    match_id: str
    team_a: str
    team_b: str
    predicted_winner: str
    predicted_score: PredictedScore
    team_a_win_prob: float
    draw_prob: float
    team_b_win_prob: float
    next_match_id: str | None = None
    feeds_slot: str | None = Field(
        default=None, description="Which slot (team_a/team_b) the winner fills in the next match"
    )


class BracketRound(BaseModel):
    round: str
    matches: list[KnockoutMatchPrediction]


class BracketPredictionResponse(BaseModel):
    tournament: str
    format: str
    note: str
    draw_last_updated: str | None = None
    prediction_model: str
    feature_source: str
    groups: list[GroupPrediction]
    knockout_rounds: dict[str, list[KnockoutMatchPrediction]]
    bracket_tree: list[BracketRound]
    champion: str
    runner_up: str
    third_place: str
    top_contenders: list[dict[str, str | float]]


class TeamChampionOdds(BaseModel):
    team: str
    champion_pct: float
    finalist_pct: float


class MonteCarloResponse(BaseModel):
    simulations: int
    seed: int
    prediction_model: str
    feature_source: str
    champion_odds: list[TeamChampionOdds]
    simulated_champion_favorite: str
    deterministic_champion: str
    most_likely_champion: str
    most_likely_bracket: BracketPredictionResponse


class WhatIfRequest(BaseModel):
    """Force specific knockout match winners and re-simulate the bracket."""

    overrides: dict[str, str] = Field(
        default_factory=dict,
        description="Map of match_id (e.g. M86, M100, M104) to forced winner team name",
    )
