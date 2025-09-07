## `src/nfl_model/pricing/odds.py`

from __future__ import annotations
import math

def win_prob_from_spread(spread: float, margin_sd: float = 13.45) -> float:
    z = spread / (margin_sd * math.sqrt(2))
    return 0.5 * (1 + math.erf(z))

def american_odds_from_prob(p: float) -> int:
    p = min(max(p, 1e-6), 1 - 1e-6)
    if p >= 0.5:
        return int(round(-100 * p / (1 - p)))
    return int(round(100 * (1 - p) / p))
