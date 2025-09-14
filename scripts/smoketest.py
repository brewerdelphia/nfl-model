# scripts/smoketest.py
from __future__ import annotations
from pathlib import Path
import sys

# Allow running without pip install -e .
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nfl_lines.io.loader_v0 import get_week
from nfl_lines.utils.config import API_SPORTS_KEY, LEAGUE_ID, CACHE_DIR

def main():
    season, week = 2023, 3
    print(f"Using cache dir: {CACHE_DIR}")
    print(f"Running smoke test for season={season}, week={week} ...")
    df = get_week(
        season, week,
        force_refresh=False,
        api_key=API_SPORTS_KEY,
        league_id=LEAGUE_ID,
    )
    if df.empty:
        print("⚠️ No games returned!")
    else:
        print(df.head(15).to_string(index=False))

if __name__ == "__main__":
    main()
