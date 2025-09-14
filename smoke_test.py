# smoketest.py
"""
Quick smoke test for nfl-model Phase 1.
Fetches one week of NFL games and prints first rows.
"""
from nfl_lines.io.loader_v0 import get_week

# 🔑 Set your credentials here if you don’t want to rely on environment variables
API_SPORTS_KEY = "63bb0835254974009e585e45b61cc864"
API_SPORTS_LEAGUE_ID = 1   # NFL

def main():
    season, week = 2023, 4
    print(f"Running smoke test for season={season}, week={week} ...")
    df = get_week(
        season,
        week,
        force_refresh=True,
        api_key=API_SPORTS_KEY,
        league_id=API_SPORTS_LEAGUE_ID,
    )
    if df.empty:
        print("⚠️ No games returned!")
    else:
        print(df.head(15).to_string(index=False))

if __name__ == "__main__":
    main()
