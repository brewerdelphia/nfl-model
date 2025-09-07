## `src/nfl_model/config.py`

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Literal

class Params(BaseModel):
    home_field_points: float = 1.65
    neutral_home_field_points: float = 0.0
    qb_weight: float = 1.0
    league_total: float = 44.0
    pace_points: float = 0.0
    margin_sd: float = 13.45
    spread_cap: float = 30.0
    use_off_def_for_total: bool = True

class PipelineConfig(BaseModel):
    spread_factors: List[str] = Field(default_factory=lambda: [
        "home_field",
        "qb_adjust",
    ])
    total_factors: List[str] = Field(default_factory=lambda: [
        "off_def_total",
    ])
    spread_model: Literal["default"] = "default"
    total_model: Literal["default"] = "default"
