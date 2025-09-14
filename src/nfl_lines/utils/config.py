# src/nfl_lines/utils/config.py
from __future__ import annotations
from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CACHE_ROOT = Path(os.getenv("NFL_CACHE_DIR", str(PROJECT_ROOT / "cache")))
CACHE_DIR = CACHE_ROOT / "api_sports_nfl"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------
# API Sports credentials
# Best practice: use environment variables if available.
# Fallbacks are provided so scripts don't need to repeat values.
# --------------------------------------------------------------------
API_SPORTS_KEY: str | None = os.getenv("API_SPORTS_KEY") or "63bb0835254974009e585e45b61cc864"
LEAGUE_ID: int = int(os.getenv("API_SPORTS_LEAGUE_ID", "1"))
