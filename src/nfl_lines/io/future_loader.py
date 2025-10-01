# src/nfl_lines/io/future_loader.py
from __future__ import annotations

import argparse
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, List, Dict

import pandas as pd
import pytz  # pip install pytz

from nfl_lines.utils.config import CACHE_DIR
from nfl_lines.schedule.week_windows import week_range
from nfl_lines.io.fetch_api_sports import get_games_by_date

TEMP_FILE = CACHE_DIR / "_upcoming_schedule.parquet"


def _normalize_schedule(season: int, week: int, raw: List[Dict[str, Any]]) -> pd.DataFrame:
    est_tz = pytz.timezone("US/Eastern")
    rows: List[Dict[str, Any]] = []

    for g in raw:
        game_info = g.get("game", {})
        date_info = game_info.get("date", {})
        ts = date_info.get("timestamp")

        kickoff_utc = None
        kickoff_est = None
        date_str = None

        if ts is not None:
            kickoff_dt_utc = pd.to_datetime(int(ts), unit="s", utc=True)
            kickoff_utc = kickoff_dt_utc.isoformat()

            kickoff_dt_est = kickoff_dt_utc.tz_convert(est_tz)
            date_str = kickoff_dt_est.date().isoformat()          # Eastern local date
            kickoff_est = kickoff_dt_est.strftime("%H:%M:%S")     # Eastern local time only

        teams = g.get("teams") or {}
        h = teams.get("home") or {}
        a = teams.get("away") or {}
        home_name = h.get("name") or g.get("home")
        away_name = a.get("name") or g.get("away")

        scores = g.get("scores") or {}
        home_pts = None if not scores else scores.get("home", {}).get("total")
        away_pts = None if not scores else scores.get("away", {}).get("total")

        rows.append({
            "date": date_str,            # Eastern local date (YYYY-MM-DD)
            "season": season,
            "week": week,
            "home": home_name,
            "away": away_name,
            "home_points": home_pts,
            "away_points": away_pts,
            "neutral": False,            # API sample does not expose neutral flag
            "kickoff_est": kickoff_est,  # HH:MM:SS (Eastern) — no date, no offset
            "kickoff_utc": kickoff_utc,  # ISO8601 UTC for machines
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        # Sort by Eastern local datetime (date + time)
        df["_kick"] = pd.to_datetime(df["date"] + " " + df["kickoff_est"], errors="coerce")
        df = df.sort_values(["season", "week", "_kick", "home", "away"]).drop(columns="_kick")
    return df


def fetch_week_schedule(
    season: int,
    week: int,
    *,
    api_key: Optional[str] = None,
    league_id: Optional[int] = None,
    base_url: Optional[str] = None,
) -> pd.DataFrame:
    date_from, date_to = week_range(season, week)
    d0 = datetime.fromisoformat(date_from).date()
    d1 = datetime.fromisoformat(date_to).date()

    lid = int(league_id or os.getenv("API_SPORTS_LEAGUE_ID", "1") or 1)

    raw: List[Dict[str, Any]] = []
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

    df = _normalize_schedule(season, week, raw)
    TEMP_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(TEMP_FILE, index=False)
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch future NFL week schedule (Eastern-local date/time).")
    parser.add_argument("week", type=int, help="Week number to fetch")
    parser.add_argument("--season", type=int, default=datetime.now().year, help="Season year (defaults to current year)")
    args = parser.parse_args()

    df = fetch_week_schedule(args.season, args.week)
    print(f"Wrote {len(df)} games to {TEMP_FILE}")
    # friendly console preview
    cols = ["date", "home", "away", "kickoff_est"]
    existing = [c for c in cols if c in df.columns]
    print(df[existing].to_string(index=False))
