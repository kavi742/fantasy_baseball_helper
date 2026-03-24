"""
Pitcher season stats via pybaseball (FanGraphs data).

Why pybaseball over mlb-statsapi for this use case:
  - FanGraphs data is richer: xFIP, SIERA, K%, BB%, SwStr% alongside standard ERA/WHIP/K
  - One bulk call fetches the entire league leaderboard — no per-player requests
  - No API key required, pip-installable, no browser dependencies
  - Active maintenance, widely used in the baseball analytics community
  - A pitcher's actual season-to-date numbers are better for weekly ranking
    than pre-season projections

Future enhancement: baseball-scraper can pull Steamer/ZiPS projections but
introduces a Selenium/Chrome dependency that significantly raises the barrier
for OSS contributors. Flag as optional rather than default.

Team batting stats still use mlb-statsapi since pybaseball's team hitting
leaderboard is less granular at the team level.
"""
import logging
from datetime import date
from functools import lru_cache

import pybaseball
import statsapi

logger = logging.getLogger(__name__)

pybaseball.cache.enable()


def get_current_season() -> int:
    today = date.today()
    return today.year if today.month >= 4 else today.year - 1


@lru_cache(maxsize=4)
def _fetch_pitching_leaderboard(season: int):
    """
    Fetch the full FanGraphs pitching leaderboard for the season.
    Cached per-process so repeat calls within the same server instance
    don't re-fetch. qual=1 includes anyone with at least 1 IP.
    """
    try:
        df = pybaseball.pitching_stats(season, season, qual=1)
        return df
    except Exception as e:
        logger.warning("pybaseball pitching_stats fetch failed: %s", e)
        return None


def get_pitcher_stats(player_names: list[str]) -> dict[str, dict]:
    """
    Fetch season pitching stats for a list of player names from FanGraphs.

    Returns a dict keyed by player name with stats:
      era, whip, strikeouts, k_per_9, innings_pitched,
      quality_starts, saves, holds, svh, games_started, xfip, siera, k_pct, bb_pct

    Matching is done by name since FanGraphs uses its own player IDs.
    """
    if not player_names:
        return {}

    season = get_current_season()
    df = _fetch_pitching_leaderboard(season)

    if df is None or df.empty:
        logger.warning("No pitching leaderboard data available for %s", season)
        return {}

    name_col = "Name" if "Name" in df.columns else df.columns[0]
    df = df.copy()
    df["_name_lower"] = df[name_col].str.lower().str.strip()

    result = {}
    for name in player_names:
        name_lower = name.lower().strip()
        match = df[df["_name_lower"] == name_lower]

        if match.empty:
            # Last-name fallback for cases where DB stores shortened names
            parts = name_lower.split()
            if len(parts) >= 2:
                last = parts[-1]
                candidates = df[df["_name_lower"].str.endswith(" " + last)]
                if len(candidates) == 1:
                    match = candidates

        if match.empty:
            logger.debug("No FanGraphs stats found for: %s", name)
            continue

        row = match.iloc[0]
        sv  = _safe_int(row.get("SV"))
        hld = _safe_int(row.get("HLD"))

        result[name] = {
            "era":             _safe_float(row.get("ERA")),
            "whip":            _safe_float(row.get("WHIP")),
            "strikeouts":      _safe_int(row.get("SO")),
            "k_per_9":         _safe_float(row.get("K/9")),
            "innings_pitched": _safe_float(row.get("IP")),
            "quality_starts":  _safe_int(row.get("QS")),
            "saves":           sv,
            "holds":           hld,
            "svh":             _safe_add(sv, hld),
            "games_started":   _safe_int(row.get("GS")),
            "xfip":            _safe_float(row.get("xFIP")),
            "siera":           _safe_float(row.get("SIERA")),
            "k_pct":           _safe_float(row.get("K%")),
            "bb_pct":          _safe_float(row.get("BB%")),
        }

    return result


def get_team_batting_stats(team_ids: list[int]) -> dict[int, dict]:
    """
    Fetch season team batting stats from mlb-statsapi.
    Returns a dict keyed by MLB team ID.
    """
    if not team_ids:
        return {}

    season = get_current_season()
    result = {}

    for team_id in team_ids:
        try:
            data = statsapi.get(
                "stats",
                {
                    "stats": "season",
                    "group": "hitting",
                    "gameType": "R",
                    "season": season,
                    "sportId": 1,
                    "teamId": team_id,
                },
            )
        except Exception as e:
            logger.warning("Failed to fetch batting stats for team %s: %s", team_id, e)
            continue

        for entry in data.get("stats", []):
            splits = entry.get("splits", [])
            if not splits:
                continue
            s = splits[0].get("stat", {})
            pa = _safe_int(s.get("plateAppearances")) or 1
            k  = _safe_int(s.get("strikeOuts")) or 0
            result[team_id] = {
                "avg":            _safe_float(s.get("avg")),
                "ops":            _safe_float(s.get("ops")),
                "strikeout_rate": round(k / pa, 4) if pa else None,
                "plate_appearances": pa,
            }

    return result


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe_float(val) -> float | None:
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _safe_int(val) -> int | None:
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _safe_add(a, b) -> int | None:
    if a is None and b is None:
        return None
    return (a or 0) + (b or 0)
