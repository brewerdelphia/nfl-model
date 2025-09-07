## `src/nfl_model/schemas.py`

from __future__ import annotations
from pydantic import BaseModel
from typing import Optional

class TeamRating(BaseModel):
    team: str
    power: float
    off: float | None = None
    def_: float | None = None  # defensive prevention (+ better)
    qb_points: float | None = None

class Game(BaseModel):
    week: int
    date: str
    away: str
    home: str
    neutral: int = 0

class LineOutput(BaseModel):
    week: int
    date: str
    away: str
    home: str
    neutral: int
    model_spread_home: float
    model_total: float
    home_team_total: float
    away_team_total: float
    home_win_prob: float
    away_win_prob: float
    ml_home: int
    ml_away: int
