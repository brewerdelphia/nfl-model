## `src/nfl_model/factors/qb_adjust.py`

from __future__ import annotations
from .base import Factor, FactorContext
from ..registry import register_factor

@register_factor("qb_adjust")
class QBAdjust(Factor):
    def apply(self, ctx: FactorContext):
        w = ctx.params.qb_weight
        h = float(ctx.ratings_row_home.get("qb_points", 0.0) or 0.0) * w
        a = float(ctx.ratings_row_away.get("qb_points", 0.0) or 0.0) * w
        return {"spread_delta": (h - a)}