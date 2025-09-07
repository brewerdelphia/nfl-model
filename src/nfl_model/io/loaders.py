## `src/nfl_model/io/loaders.py`

from __future__ import annotations
import pandas as pd
from pathlib import Path

REQUIRED_RATINGS = {"team", "power"}
REQUIRED_SCHEDULE = {"week", "date", "away", "home"}

def _norm_team(x: str) -> str:
    return x.strip().upper()

def load_ratings(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    cols = {c.lower(): c for c in df.columns}
    lower = df.rename(columns=str.lower)
    if not REQUIRED_RATINGS.issubset(lower.columns):
        missing = REQUIRED_RATINGS - set(lower.columns)
        raise ValueError(f"ratings missing: {missing}")
    lower["team_key"] = lower["team"].map(_norm_team)
    return lower

def load_schedule(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path).rename(columns=str.lower)
    if not REQUIRED_SCHEDULE.issubset(df.columns):
        missing = REQUIRED_SCHEDULE - set(df.columns)
        raise ValueError(f"schedule missing: {missing}")
    if "neutral" not in df.columns:
        df["neutral"] = 0
    df["home_key"] = df["home"].map(_norm_team)
    df["away_key"] = df["away"].map(_norm_team)
    return df
