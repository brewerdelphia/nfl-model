# fetch_api_sports.py
from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional, List

import requests

API_KEY_ENV = "API_SPORTS_KEY"
BASE_URL_ENV = "API_SPORTS_BASE_URL"
LEAGUE_ID_ENV = "API_SPORTS_LEAGUE_ID"

DEFAULT_BASE_URL = "https://v1.american-football.api-sports.io"
GAMES_ENDPOINT = "/games"


class APISportsError(RuntimeError):
    pass


def _headers(api_key: Optional[str]) -> Dict[str, str]:
    key = api_key or os.getenv(API_KEY_ENV)
    if not key:
        raise APISportsError(
            f"Missing API key. Set {API_KEY_ENV} in your environment or pass api_key=..."
        )
    return {"x-apisports-key": key}


def _base_url(base_url: Optional[str]) -> str:
    return (base_url or os.getenv(BASE_URL_ENV) or DEFAULT_BASE_URL).rstrip("/")


def _retry_get(
    url: str,
    params: Dict[str, Any],
    headers: Dict[str, str],
    *,
    timeout: int = 20,
    retries: int = 2,
    backoff: float = 1.6,
) -> Dict[str, Any]:
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=timeout)
            if resp.status_code == 429 and attempt < retries:
                time.sleep(backoff**attempt)
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            last_err = e
            if attempt < retries:
                time.sleep(backoff**attempt)
    raise APISportsError(f"GET failed after {retries} attempts: {last_err}")


def get_games_by_date(
    date_str: str,
    *,
    league_id: int,
    season: Optional[int] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch NFL games on a single date (YYYY-MM-DD).
    """
    url = f"{_base_url(base_url)}{GAMES_ENDPOINT}"
    params: Dict[str, Any] = {"league": int(league_id), "date": date_str}
    if season is not None:
        params["season"] = int(season)

    data = _retry_get(url, params, _headers(api_key))
    return data.get("response", []) if isinstance(data, dict) else []
