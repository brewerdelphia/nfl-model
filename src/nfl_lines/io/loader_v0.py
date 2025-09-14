# src/nfl_lines/io/loader_v0.py
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional
import os
import pandas as pd

from nfl_lines.utils.config import CACHE_DIR             # <-- NEW
from nfl_lines.schedule.week_windows import week_range
from nfl_lines.io.fetch_api_sports import get_games_by_date

CANONICAL_COLUMNS = [
    "date", "season", "week", "home", "away",
    "home_points", "away_points", "neutral",
]

def _as_int_or_na(v):
    try:
        return int(v) if v is not None else None
    except Exception:
        return None

def _as_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    return str(v).strip().lower() in {"1", "true", "t", "yes", "y"}

def _normalize(season: int, week: int, raw: list[dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for g in raw:
        raw_date = g.get("date") or g.get("datetime")
        dt = pd.to_datetime(raw_date, utc=True, errors="coerce") if raw_date else pd.NaT
        date_str = dt.date().isoformat() if pd.notna(dt) else None

        teams = g.get("teams") or {}
        h = teams.get("home") or {}
        a = teams.get("away") or {}
        home_name = h.get("name") or h.get("nickname") or h.get("code") or g.get("home")
        away_name = a.get("name") or a.get("nickname") or a.get("code") or g.get("away")

        scores = g.get("scores") or g.get("score") or {}
        sh, sa = scores.get("home"), scores.get("away")
        home_pts = _as_int_or_na(sh.get("total") if isinstance(sh, dict) else sh)
        away_pts = _as_int_or_na(sa.get("total") if isinstance(sa, dict) else sa)

        neutral = (
            _as_bool(g.get("neutral"))
            or _as_bool((g.get("venue") or {}).get("neutral"))
            or _as_bool(g.get("neutral_venue"))
        )

        rows.append({
            "date": date_str,
            "season": int(season),
            "week": int(week),
            "home": home_name,
            "away": away_name,
            "home_points": home_pts,
            "away_points": away_pts,
            "neutral": bool(neutral),
        })

    df = pd.DataFrame.from_records(rows, columns=CANONICAL_COLUMNS)
    for col in ("season", "week", "home_points", "away_points"):
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    df["neutral"] = df["neutral"].fillna(False).astype(bool)
    return df

def _cache_path(season: int, week: int) -> Path:
    return CACHE_DIR / f"{int(season)}_wk{int(week)}.parquet"
    #return CACHE_DIR / f"{int(season)}_wk{int(week):02d}.parquet"

def get_week(
    season: int,
    week: int,
    *,
    force_refresh: bool = False,
    api_key: Optional[str] = None,
    league_id: Optional[int] = None,
    base_url: Optional[str] = None,
) -> pd.DataFrame:
    """
    Fetch NFL games day-by-day (Thu..Tue) for the requested week and cache to Parquet.
    Columns: ['date','season','week','home','away','home_points','away_points','neutral']
    """
    p = _cache_path(season, week)
    if p.exists() and not force_refresh:
        return pd.read_parquet(p)

    date_from, date_to = week_range(season, week)
    d0 = datetime.fromisoformat(date_from).date()
    d1 = datetime.fromisoformat(date_to).date()

    lid = int(league_id or os.getenv("API_SPORTS_LEAGUE_ID", "1") or 1)

    raw: list[dict[str, Any]] = []
    cur = d0
    while cur <= d1:
        raw.extend(
            get_games_by_date(
                cur.isoformat(),
                league_id=lid,
                season=season,
                api_key=api_key,
                base_url=base_url,
            )
        )
        cur += timedelta(days=1)

    df = _normalize(season, week, raw)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(p, index=False)
    return df
