## `src/nfl_model/factors/home_field.py`

from __future__ import annotations
from .base import Factor, FactorContext
from ..registry import register_factor

@register_factor("home_field")
class HomeField(Factor):
    def apply(self, ctx: FactorContext):
        neutral = int(ctx.game_row.get("neutral", 0))
        hfa = ctx.params.neutral_home_field_points if neutral else ctx.params.home_field_points
        return {"spread_delta": hfa}

