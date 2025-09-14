#week_windows.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta

# One anchor per season: the **Thursday** of NFL Week 1 (Regular Season).
# Add new seasons as they’re announced.
WEEK1_THURSDAY: dict[int, date] = {
    2013: date(2013, 9, 5),
    2014: date(2014, 9, 4),
    2015: date(2015, 9, 10),
    2016: date(2016, 9, 8),
    2017: date(2017, 9, 7),
    2018: date(2018, 9, 6),
    2019: date(2019, 9, 5),
    2020: date(2020, 9, 10),
    2021: date(2021, 9, 9),
    2022: date(2022, 9, 8),
    2023: date(2023, 9, 7),
    2024: date(2024, 9, 5),
    2025: date(2025, 9, 4),
    #2026: date(2026, 9, 10), # placeholder – to confirm
    #2027: date(2027, 9, 9),  # placeholder – to confirm
    #2028: date(2028, 9, 7),  # placeholder – to confirm
    #2029: date(2029, 9, 6),  # placeholder – to confirm
    #2030: date(2030, 9, 5),  # placeholder – to confirm
}

REGULAR_SEASON_WEEKS: int = 18  # adjust if you later include preseason/postseason

@dataclass(frozen=True)
class WeekKey:
    season: int
    week: int  # 1-based

def week_range(season: int, week: int) -> tuple[str, str]:
    """
    Returns (from_iso, to_iso) for the NFL week window, Thu..Tue.
    Example: ('2023-09-07','2023-09-12') for Week 1, 2023.
    """
    if week < 1:
        raise ValueError("week must be >= 1")
    if season not in WEEK1_THURSDAY:
        raise KeyError(
            f"Unknown season {season}. Add WEEK1_THURSDAY[{season}] = date(YYYY, M, D)."
        )
    start_thu = WEEK1_THURSDAY[season] + timedelta(days=7 * (week - 1))
    end_tue   = start_thu + timedelta(days=5)  # Thu..Tue
    return (start_thu.isoformat(), end_tue.isoformat())

def next_week(season: int, week: int) -> WeekKey:
    if week < REGULAR_SEASON_WEEKS:
        return WeekKey(season, week + 1)
    if (season + 1) in WEEK1_THURSDAY:
        return WeekKey(season + 1, 1)
    return WeekKey(season, REGULAR_SEASON_WEEKS)

def prev_week(season: int, week: int) -> WeekKey:
    if week > 1:
        return WeekKey(season, week - 1)
    if (season - 1) in WEEK1_THURSDAY:
        return WeekKey(season - 1, REGULAR_SEASON_WEEKS)
    return WeekKey(season, 1)
