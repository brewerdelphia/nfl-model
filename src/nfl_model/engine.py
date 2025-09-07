## `src/nfl_model/engine.py`


from __future__ import annotations

from . import factors

from dataclasses import dataclass
import pandas as pd

from .config import Params, PipelineConfig
from .models.spread_model import SpreadModel
from .models.total_model import TotalModel
from .pricing.odds import win_prob_from_spread, american_odds_from_prob

@dataclass
class Engine:
    params: Params
    pipe: PipelineConfig

    def __post_init__(self):
        self._spread_model = SpreadModel(self.params, self.pipe)
        self._total_model = TotalModel(self.params, self.pipe)

    def price(self, merged: pd.DataFrame) -> pd.DataFrame:
        df = merged.copy()
        # Compute spread & totals
        df["model_spread_home"] = [
            self._spread_model.compute(rh, ra, g)
            for rh, ra, g in zip(
                df["_rat_home"], df["_rat_away"], df.to_dict(orient="records")
            )
        ]
        df["home_win_prob"] = df["model_spread_home"].apply(lambda s: win_prob_from_spread(s, self.params.margin_sd))
        df["away_win_prob"] = 1.0 - df["home_win_prob"]
        df["ml_home"] = df["home_win_prob"].apply(american_odds_from_prob)
        df["ml_away"] = df["away_win_prob"].apply(american_odds_from_prob)

        df["model_total"] = [
            self._total_model.compute(rh, ra, g)
            for rh, ra, g in zip(
                df["_rat_home"], df["_rat_away"], df.to_dict(orient="records")
            )
        ]
        df["home_team_total"] = (df["model_total"] + df["model_spread_home"]) / 2.0
        df["away_team_total"] = df["model_total"] - df["home_team_total"]

        return df
