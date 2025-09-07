## `src/nfl_model/factors/base.py`

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class FactorContext:
    params: Any
    ratings_row_home: dict
    ratings_row_away: dict
    game_row: dict

class Factor:
    """Base factor interface. Implement `apply` and return a dict of adjustments.
    For spread: return {"spread_delta": float}
    For total:  return {"total_delta": float}
    """
    def apply(self, ctx: FactorContext) -> Dict[str, float]:
        raise NotImplementedError

