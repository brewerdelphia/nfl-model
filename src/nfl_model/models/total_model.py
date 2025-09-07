## `src/nfl_model/models/total_model.py`

from __future__ import annotations
from ..config import Params, PipelineConfig
from ..registry import get_factor

class TotalModel:
    def __init__(self, params: Params, pipe: PipelineConfig):
        self.params = params
        self.factors = [get_factor(name)() for name in pipe.total_factors]

    def compute(self, ratings_row_home: dict, ratings_row_away: dict, game_row: dict) -> float:
        total = self.params.league_total + 2 * self.params.pace_points
        from ..factors.base import FactorContext
        ctx = FactorContext(params=self.params, ratings_row_home=ratings_row_home, ratings_row_away=ratings_row_away, game_row=game_row)
        for f in self.factors:
            adj = f.apply(ctx)
            total += float(adj.get("total_delta", 0.0))
        return max(0.0, total)
