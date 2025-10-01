# src/nfl_model/io/loaders.py  (append these helpers or place in a new module)
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, Sequence, Tuple
import re

import pandas as pd


# --------------------------- Public API --------------------------------------

def build_team_perspective_long(
    cache_dir: Path | str,
    seasons: Optional[Sequence[int]] = None,
    through_week: Optional[int] = None,
    include_playoffs: bool = False,
    strict_columns: bool = False,
) -> pd.DataFrame:
    """
    Load weekly cached Parquets like '2024_wk1.parquet' from `cache_dir/api_sports_nfl/`
    and return a *team-perspective* long table with two rows per game.

    Input cache schema (min):
        season:int, week:int,
        home_team:str, away_team:str,
        home_score:int, away_score:int,
        neutral:bool   # True if neutral site (e.g., SB/London); otherwise False

    Output columns:
        season:int
        week:int
        game_id:str          # "YYYY_WW_<HOME>_vs_<AWAY>", WW zero-padded
        team:str
        opp:str
        is_home:bool
        is_neutral:bool
        points_for:int
        points_against:int

    Args
    ----
    cache_dir:
        The root of your cache (e.g. project_root/"cache/api_sports_nfl").
        The function will glob for files matching: '{season}_wk*.parquet'.
    seasons:
        If provided, only load these seasons. If None, infer all seasons present.
    through_week:
        If provided, filter to games with week <= through_week (regular season).
        Playoffs are kept only if `include_playoffs=True` and your files encode them.
    include_playoffs:
        If True, do not drop non-1..18 weeks (e.g., strings like "WC","DIV","CC","SB").
        If False, keep only numeric weeks in [1..18].
    strict_columns:
        If True, raise on missing/renamed columns. If False, try to auto-map a few
        common variants (underscores/casing/space differences).

    Returns
    -------
    pd.DataFrame
        Team-perspective long frame sorted by (season, week, game_id, team).
    """
    cache_dir = Path(cache_dir)
    if (cache_dir / "api_sports_nfl").exists():
        cache_root = cache_dir / "api_sports_nfl"
    else:
        cache_root = cache_dir  # allow pointing directly at .../api_sports_nfl

    files = _list_week_files(cache_root, seasons)
    if not files:
        raise FileNotFoundError(f"No weekly parquet files found under {cache_root}")

    frames = []
    for f in files:
        df = pd.read_parquet(f)

        # Normalize columns (lightweight mapping if user isn't strict)
        df = _normalize_cache_columns(df, strict=strict_columns)

        # Filter weeks if asked
        if through_week is not None:
            # Only applies to regular-season numeric weeks
            if pd.api.types.is_integer_dtype(df["week"]):
                df = df[df["week"] <= int(through_week)]
            else:
                # if non-integer weeks exist (e.g., "WC"), leave as-is and rely on include_playoffs
                pass

        if not include_playoffs:
            # Keep only integer weeks in [1..18]
            if pd.api.types.is_integer_dtype(df["week"]):
                df = df[(df["week"] >= 1) & (df["week"] <= 18)]
            else:
                # drop non-numeric week labels
                df = df[df["week"].apply(lambda x: isinstance(x, (int, pd.Int64Dtype.type)))]

        if df.empty:
            continue

        # Build two rows per game
        long_df = _to_team_long(df)
        frames.append(long_df)

    if not frames:
        return pd.DataFrame(
            columns=[
                "season", "week", "game_id", "team", "opp",
                "is_home", "is_neutral", "points_for", "points_against"
            ]
        )

    out = pd.concat(frames, ignore_index=True)

    # Sort for deterministic downstream behavior
    out = out.sort_values(["season", "week", "game_id", "team"], kind="mergesort").reset_index(drop=True)

    # Dtypes (nice-to-have, not strictly required)
    out["season"] = out["season"].astype(int)
    # week may be Int64 (nullable); if it's numeric, cast to int
    if pd.api.types.is_integer_dtype(out["week"]):
        out["week"] = out["week"].astype(int)

    # Sanity
    expected_cols = [
        "season", "week", "game_id", "team", "opp",
        "is_home", "is_neutral", "points_for", "points_against"
    ]
    missing = [c for c in expected_cols if c not in out.columns]
    if missing:
        raise ValueError(f"Long-table missing columns: {missing}")

    return out


# --------------------------- Internals ---------------------------------------

WEEK_FILE_RE = re.compile(r"(?P<season>\d{4})_wk0*(?P<week>\d+)\.parquet$", re.IGNORECASE)

def _list_week_files(cache_root: Path, seasons: Optional[Sequence[int]]) -> list[Path]:
    """Find weekly parquet files like 2024_wk1.parquet or 2021_wk01.parquet."""
    files = []
    for p in cache_root.glob("*.parquet"):
        m = WEEK_FILE_RE.search(p.name)
        if not m:
            continue
        season = int(m.group("season"))
        if (seasons is None) or (season in seasons):
            files.append(p)
    # Stable order: by (season, week)
    def key_fn(path: Path) -> Tuple[int, int]:
        m = WEEK_FILE_RE.search(path.name)
        return (int(m.group("season")), int(m.group("week")))
    files.sort(key=key_fn)
    return files


_COL_VARIANTS = {
    "season": {"season", "Season"},
    "week": {"week", "Week"},
    "home_team": {"home_team", "homeTeam", "HomeTeam", "home team", "home"},
    "away_team": {"away_team", "awayTeam", "AwayTeam", "away team", "away"},
    "home_score": {"home_score", "homeScore", "HomeScore", "home score", "homescore", "home_pts"},
    "away_score": {"away_score", "awayScore", "AwayScore", "away score", "awayscore", "away_pts"},
    "neutral": {"neutral", "is_neutral", "neutral_site", "neutralSite", "Neutral"},
}

def _normalize_cache_columns(df: pd.DataFrame, strict: bool) -> pd.DataFrame:
    """
    Ensure required columns exist. If strict=False, try to auto-map common name variants.
    """
    colmap = {}
    lower_map = {c.lower().replace(" ", "").replace("-", "").replace("/", ""): c for c in df.columns}

    def pick(name: str, variants: set[str]) -> Optional[str]:
        for v in variants:
            key = v.lower().replace(" ", "").replace("-", "").replace("/", "")
            if key in lower_map:
                return lower_map[key]
        return None

    for canonical, variants in _COL_VARIANTS.items():
        src = pick(canonical, variants)
        if src is None:
            if strict:
                raise KeyError(f"Missing required column '{canonical}' (tried variants {sorted(variants)})")
            else:
                # provide sensible fallback defaults only where safe
                if canonical == "neutral":
                    df["neutral"] = False
                    src = "neutral"
                else:
                    raise KeyError(f"Missing required column '{canonical}' (tried variants {sorted(variants)})")
        colmap[canonical] = src

    # Rename a copy to canonical names
    out = df.rename(columns={v: k for k, v in colmap.items() if v != k}).copy()

    # Types (be tolerant—just coerce if possible)
    for c in ("season", "week"):
        if c in out.columns:
            try:
                out[c] = pd.to_numeric(out[c], errors="ignore")
            except Exception:
                pass
    for c in ("home_score", "away_score"):
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")

    if "neutral" in out.columns:
        out["neutral"] = out["neutral"].fillna(False).astype(bool)

    return out


def _make_game_id(season: int, week: int, home_team: str, away_team: str) -> str:
    """Create a deterministic human-readable game id."""
    week_str = f"{int(week):02d}" if pd.notna(week) else "??"
    # Clean team names lightly for IDs
    def clean(s: str) -> str:
        return re.sub(r"[^\w]+", "", str(s)).upper()
    return f"{int(season)}_{week_str}_{clean(home_team)}_vs_{clean(away_team)}"


def _to_team_long(df_games: pd.DataFrame) -> pd.DataFrame:
    """
    Convert a wide game table to two team-rows per game with is_neutral copied to both rows.
    Assumes columns are already normalized to canonical names.
    """
    # Synthesize a game_id
    game_id = df_games.apply(
        lambda r: _make_game_id(r["season"], r["week"], r["home_team"], r["away_team"]),
        axis=1
    )
    g = df_games.assign(game_id=game_id)

    # Home rows
    home = g[["season", "week", "game_id", "home_team", "away_team", "home_score", "away_score", "neutral"]].copy()
    home.rename(columns={
        "home_team": "team",
        "away_team": "opp",
        "home_score": "points_for",
        "away_score": "points_against",
        "neutral": "is_neutral",
    }, inplace=True)
    home["is_home"] = True

    # Away rows
    away = g[["season", "week", "game_id", "home_team", "away_team", "home_score", "away_score", "neutral"]].copy()
    away.rename(columns={
        "away_team": "team",
        "home_team": "opp",
        "away_score": "points_for",
        "home_score": "points_against",
        "neutral": "is_neutral",
    }, inplace=True)
    away["is_home"] = False

    long_df = pd.concat([home, away], ignore_index=True)

    # Order columns
    long_df = long_df[
        ["season", "week", "game_id", "team", "opp",
         "is_home", "is_neutral", "points_for", "points_against"]
    ]

    # Type hygiene
    long_df["is_home"] = long_df["is_home"].astype(bool)
    long_df["is_neutral"] = long_df["is_neutral"].astype(bool)
    long_df["points_for"] = pd.to_numeric(long_df["points_for"], errors="coerce").astype("Int64")
    long_df["points_against"] = pd.to_numeric(long_df["points_against"], errors="coerce").astype("Int64")

    return long_df
