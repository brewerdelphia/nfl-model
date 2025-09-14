# scripts/cache_tool.py
from __future__ import annotations
from pathlib import Path
import sys
import argparse
from datetime import date, datetime

# path shim so we can run without pip install -e .
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nfl_lines.utils.config import CACHE_DIR, API_SPORTS_KEY, LEAGUE_ID
from nfl_lines.schedule.week_windows import WEEK1_THURSDAY, week_range, REGULAR_SEASON_WEEKS
from nfl_lines.io.loader_v0 import get_week, _cache_path

CURRENT_SEASON_DEFAULT = max(WEEK1_THURSDAY)  # latest season you have an anchor for

def last_completed_week(season: int, today: date) -> int:
    if season not in WEEK1_THURSDAY:
        return 0
    w1 = WEEK1_THURSDAY[season]
    if today < w1:
        return 0
    delta_days = (today - w1).days
    cw = min((delta_days // 7) + 1, REGULAR_SEASON_WEEKS)
    _, to_iso = week_range(season, cw)
    end_tue = datetime.fromisoformat(to_iso).date()
    if today <= end_tue:
        cw -= 1
    return max(0, cw)

def ensure_week(season: int, week: int, *, refresh: bool) -> int:
    """Return rows written/loaded; refresh=True forces re-pull."""
    p = _cache_path(season, week)
    if p.exists() and not refresh:
        # no API call; read just to report size
        import pandas as pd
        n = len(pd.read_parquet(p))
        print(f"  ✓ {p.name} (exists, {n} rows)")
        return n
    df = get_week(season, week, force_refresh=refresh,
                  api_key=API_SPORTS_KEY, league_id=LEAGUE_ID)
    n = len(df)
    print(f"  → {p.name} ({'refreshed' if refresh else 'created'}: {n} rows)")
    return n

def cmd_update(args: argparse.Namespace) -> None:
    season = args.season or CURRENT_SEASON_DEFAULT
    today = date.today()
    last_done = last_completed_week(season, today)
    print(f"Using cache dir: {CACHE_DIR}")
    if last_done == 0:
        print(f"No completed weeks yet for {season} (or no anchor).")
        return
    print(f"== Update {season} up to week {last_done} ==")
    for wk in range(1, last_done + 1):
        ensure_week(season, wk, refresh=args.refresh)

def cmd_backfill(args: argparse.Namespace) -> None:
    seasons = args.seasons
    print(f"Using cache dir: {CACHE_DIR}")
    for s in seasons:
        if s not in WEEK1_THURSDAY:
            print(f"!! Skip {s}: no Week-1 anchor in WEEK1_THURSDAY")
            continue
        print(f"== Backfill season {s} ==")
        for wk in range(1, REGULAR_SEASON_WEEKS + 1):
            ensure_week(s, wk, refresh=args.refresh)

def cmd_refresh(args: argparse.Namespace) -> None:
    print(f"Using cache dir: {CACHE_DIR}")
    ensure_week(args.season, args.week, refresh=True)

def cmd_status(args: argparse.Namespace) -> None:
    from collections import defaultdict
    import pandas as pd
    print(f"Using cache dir: {CACHE_DIR}")
    counts = defaultdict(int)
    sizes = {}
    for f in sorted(Path(CACHE_DIR).glob("*.parquet")):
        try:
            df = pd.read_parquet(f, columns=["season","week"])
            if len(df):
                s = int(df["season"].iloc[0])
                w = int(df["week"].iloc[0])
                counts[(s,w)] = len(df)
                sizes[(s,w)] = f.stat().st_size
        except Exception:
            pass
    if not counts:
        print("No parquet files found.")
        return
    by_season = {}
    for (s,w), n in counts.items():
        by_season.setdefault(s, []).append((w, n))
    for s in sorted(by_season):
        ws = sorted(by_season[s], key=lambda x: x[0])
        have = [w for w,_ in ws]
        print(f"Season {s}: weeks present = {have[:10]}{'...' if len(have)>10 else ''}  total_files={len(ws)}")

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cache_tool",
        description="Manage NFL Parquet cache (update/backfill/refresh/status). Cache-first; API only when needed or --refresh.")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("update", help="Update current (or given) season up to last completed week.")
    sp.add_argument("--season", type=int, help=f"Season to update (default: {CURRENT_SEASON_DEFAULT})")
    sp.add_argument("--refresh", action="store_true", help="Force rebuild existing weeks.")
    sp.set_defaults(func=cmd_update)

    sp = sub.add_parser("backfill", help="Backfill one or more seasons (all 18 weeks).")
    sp.add_argument("seasons", nargs="+", type=int, help="Seasons to backfill, e.g. 2023 2024")
    sp.add_argument("--refresh", action="store_true", help="Force rebuild existing weeks.")
    sp.set_defaults(func=cmd_backfill)

    sp = sub.add_parser("refresh", help="Refresh one specific (season, week).")
    sp.add_argument("season", type=int)
    sp.add_argument("week", type=int)
    sp.set_defaults(func=cmd_refresh)

    sp = sub.add_parser("status", help="Print what weeks you already have in cache.")
    sp.set_defaults(func=cmd_status)

    return p

def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
