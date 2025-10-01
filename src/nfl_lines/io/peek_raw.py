# src/nfl_lines/io/peek_raw.py
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from typing import Any, Optional

from nfl_lines.schedule.week_windows import week_range
from nfl_lines.io.fetch_api_sports import get_games_by_date


def peek_one(
    *,
    date_iso: str,
    season: Optional[int] = None,
    league_id: Optional[int] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    index: int = 0,
) -> None:
    """Fetch games for a single ISO date and print one raw game as pretty JSON."""
    lid = int(league_id or os.getenv("API_SPORTS_LEAGUE_ID", "1") or 1)
    raw: list[dict[str, Any]] = get_games_by_date(
        date_iso,
        league_id=lid,
        season=season,
        api_key=api_key,
        base_url=base_url,
    )
    print(f"[info] date={date_iso} season={season} league_id={lid} -> {len(raw)} games")
    if not raw:
        return
    idx = max(0, min(index, len(raw) - 1))
    print(f"[info] showing game index {idx} of {len(raw)}")
    print(json.dumps(raw[idx], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Peek one raw NFL game from API by date")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--date", help="ISO date (YYYY-MM-DD) to fetch (UTC)")
    g.add_argument("--week", type=int, help="Week number; uses week start date")

    p.add_argument("--season", type=int, default=datetime.now().year, help="Season year")
    p.add_argument("--index", type=int, default=0, help="0-based index of game to show")
    args = p.parse_args()

    if args.date:
        date_iso = args.date
    else:
        # Use the first day of the week window (typically Thu)
        date_from, _ = week_range(args.season, args.week)
        date_iso = date_from

    peek_one(
        date_iso=date_iso,
        season=args.season,
        index=args.index,
        api_key=os.getenv("API_SPORTS_KEY") or os.getenv("API_SPORTS_API_KEY"),
        league_id=os.getenv("API_SPORTS_LEAGUE_ID"),
        base_url=os.getenv("API_SPORTS_BASE_URL"),
    )
