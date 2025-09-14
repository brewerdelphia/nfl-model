# src/nfl_lines/utils/parquet_utils.py
from __future__ import annotations
from pathlib import Path
import pandas as pd

from nfl_lines.utils.config import CACHE_DIR   # <-- NEW

def load_all_parquet() -> pd.DataFrame:
    files = sorted(CACHE_DIR.glob("*.parquet"))
    if not files:
        raise FileNotFoundError(f"No parquet files found in {CACHE_DIR}")
    dfs = [pd.read_parquet(f) for f in files]
    return pd.concat(dfs, ignore_index=True)

def load_season(season: int) -> pd.DataFrame:
    files = sorted(CACHE_DIR.glob(f"{season}_wk*.parquet"))
    if not files:
        raise FileNotFoundError(f"No parquet files found for season {season} in {CACHE_DIR}")
    dfs = [pd.read_parquet(f) for f in files]
    return pd.concat(dfs, ignore_index=True)
