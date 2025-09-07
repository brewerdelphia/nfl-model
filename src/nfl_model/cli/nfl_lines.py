from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import yaml

from nfl_model.config import Params, PipelineConfig
from nfl_model.io.loaders import load_ratings, load_schedule
from nfl_model.engine import Engine


def _merge(schedule, ratings):
    r = ratings.set_index("team_key").to_dict(orient="index")
    df = schedule.copy()
    df["_rat_home"] = df["home_key"].map(r.get)
    df["_rat_away"] = df["away_key"].map(r.get)
    # Fail fast if any team missing
    if df["_rat_home"].isna().any() or df["_rat_away"].isna().any():
        missing = set(df.loc[df["_rat_home"].isna(), "home_key"]).union(set(df.loc[df["_rat_away"].isna(), "away_key"]))
        raise ValueError(f"Missing ratings for: {missing}")
    return df


def main():
    ap = argparse.ArgumentParser(description="Produce NFL model lines from modular pipeline")
    ap.add_argument("--ratings", required=True, type=Path)
    ap.add_argument("--schedule", required=True, type=Path)
    ap.add_argument("--params", required=False, type=Path)
    ap.add_argument("--out", required=False, type=Path)
    args = ap.parse_args()

    ratings = load_ratings(args.ratings)
    schedule = load_schedule(args.schedule)

    params_d = {}
    pipe_d = {}
    if args.params and args.params.exists():
        cfg = yaml.safe_load(args.params.read_text()) or {}
        params_d = {k: v for k, v in cfg.items() if k not in ("spread_factors", "total_factors", "spread_model", "total_model")}
        pipe_d = {k: v for k, v in cfg.items() if k in ("spread_factors", "total_factors", "spread_model", "total_model")}

    params = Params(**params_d)
    pipe = PipelineConfig(**pipe_d)

    merged = _merge(schedule, ratings)
    eng = Engine(params, pipe)
    out = eng.price(merged)

    cols = [
        "week", "date", "away", "home", "neutral",
        "model_spread_home", "model_total", "home_team_total", "away_team_total",
        "home_win_prob", "away_win_prob", "ml_home", "ml_away",
    ]
    out = out[cols]

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        out.to_csv(args.out, index=False)
        print(f"[wrote] {args.out}")
    else:
        with pd.option_context("display.max_columns", None, "display.width", 200):
            print(out)

if __name__ == "__main__":
    main()
