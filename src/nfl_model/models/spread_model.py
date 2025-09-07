## `src/nfl_model/models/spread_model.py`

from __future__ import annotations
from typing import List
import numpy as np

from ..config import Params, PipelineConfig
from ..registry import get_factor

class SpreadModel:
    def __init__(self, params: Params, pipe: PipelineConfig):
        self.params = params
        self.factors = [get_factor(name)() for name in pipe.spread_factors]

    def compute(self, ratings_row_home: dict, ratings_row_away: dict, game_row: dict) -> float:
        base = float(ratings_row_home.get("power", 0.0)) - float(ratings_row_away.get("power", 0.0))
        spread = base
        from ..factors.base import FactorContext
        ctx = FactorContext(params=self.params, ratings_row_home=ratings_row_home, ratings_row_away=ratings_row_away, game_row=game_row)
        for f in self.factors:
            adj = f.apply(ctx)
            spread += float(adj.get("spread_delta", 0.0))
        if self.params.spread_cap is not None:
            spread = float(np.clip(spread, -self.params.spread_cap, self.params.spread_cap))
        return spread
