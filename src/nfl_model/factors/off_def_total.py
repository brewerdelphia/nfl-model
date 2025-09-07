## `src/nfl_model/factors/off_def_total.py`

from __future__ import annotations
from .base import Factor, FactorContext
from ..registry import register_factor

@register_factor("off_def_total")
class OffDefTotal(Factor):
    def apply(self, ctx: FactorContext):
        if not ctx.params.use_off_def_for_total:
            return {"total_delta": 0.0}
        off_h = float(ctx.ratings_row_home.get("off", 0.0) or 0.0)
        off_a = float(ctx.ratings_row_away.get("off", 0.0) or 0.0)
        def_h = float(ctx.ratings_row_home.get("def", 0.0) or ctx.ratings_row_home.get("def_", 0.0) or 0.0)
        def_a = float(ctx.ratings_row_away.get("def", 0.0) or ctx.ratings_row_away.get("def_", 0.0) or 0.0)
        # Defense is prevention: subtract
        return {"total_delta": (off_h + off_a) - (def_h + def_a)}
