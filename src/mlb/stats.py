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


@lru_cache(maxsize=8)
def _fetch_pitching_leaderboard_range(start_date: str, end_date: str):
    """
    Fetch weekly pitching stats from MLB API boxscores.
    Cached per-process for repeat calls within the same server instance.
    """
    from mlb.client import get_weekly_schedule

    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    games = get_weekly_schedule(start, end)

    pitcher_stats: dict[int, dict] = {}

    for game in games:
        game_id = game.get("game_id")
        if not game_id:
            continue

        try:
            boxscore_data = statsapi.boxscore_data(int(game_id))
            if not boxscore_data:
                continue

            for side in ["away", "home"]:
                pitchers = boxscore_data.get(f"{side}Pitchers", [])
                for p in pitchers:
                    pid = p.get("personId")
                    if not pid or pid == 0:
                        continue

                    name = p.get("name", "")
                    if "Pitchers" in name:  # Skip header row
                        continue

                    if pid not in pitcher_stats:
                        pitcher_stats[pid] = {
                            "name": name,
                            "ip": 0.0,
                            "strikeouts": 0,
                            "walks": 0,
                            "hits": 0,
                            "earned_runs": 0,
                            "wins": 0,
                            "losses": 0,
                            "saves": 0,
                            "holds": 0,
                            "games_pitched": 0,
                        }

                    ip_str = p.get("ip", "0")
                    try:
                        ip_parts = str(ip_str).split(".")
                        full_ip = int(ip_parts[0])
                        outs = int(ip_parts[1]) if len(ip_parts) > 1 else 0
                        ip = full_ip + outs / 3
                    except (ValueError, IndexError):
                        ip = 0

                    pitcher_stats[pid]["ip"] += ip
                    pitcher_stats[pid]["strikeouts"] += _safe_int(p.get("k", 0))
                    pitcher_stats[pid]["walks"] += _safe_int(p.get("bb", 0))
                    pitcher_stats[pid]["hits"] += _safe_int(p.get("h", 0))
                    pitcher_stats[pid]["earned_runs"] += _safe_int(p.get("er", 0))
                    pitcher_stats[pid]["games_pitched"] += 1

                    # Check for win/loss in note
                    note = p.get("note", "")
                    if "(W," in note:
                        pitcher_stats[pid]["wins"] += 1
                    elif "(L," in note:
                        pitcher_stats[pid]["losses"] += 1
                    if "(S," in note or "S, " in note:
                        pitcher_stats[pid]["saves"] += 1
                    if "(H," in note:
                        pitcher_stats[pid]["holds"] += 1

        except Exception as e:
            logger.debug("Failed to fetch boxscore for game %s: %s", game_id, e)

    # Convert to result format
    result = {}
    for pid, stats in pitcher_stats.items():
        ip = stats["ip"]
        batters_faced = stats["hits"] + stats["walks"] + stats["strikeouts"]

        result[pid] = {
            "name": stats["name"],
            "innings_pitched": ip,
            "strikeouts": stats["strikeouts"],
            "walks": stats["walks"],
            "hits": stats["hits"],
            "earned_runs": stats["earned_runs"],
            "wins": stats["wins"],
            "losses": stats["losses"],
            "saves": stats["saves"],
            "holds": stats["holds"],
            "svh": stats["saves"] + stats["holds"],
            "games_pitched": stats["games_pitched"],
            "era": round(stats["earned_runs"] / ip * 9, 2) if ip > 0 else None,
            "whip": round((stats["walks"] + stats["hits"]) / ip, 2) if ip > 0 else None,
            "k_per_9": round(stats["strikeouts"] / ip * 9, 2) if ip > 0 else None,
            "k_pct": round(stats["strikeouts"] / batters_faced, 3) if batters_faced > 0 else None,
            "bb_pct": round(stats["walks"] / batters_faced, 3) if batters_faced > 0 else None,
        }

    return result


def get_pitcher_stats(player_names: list[str], period: str = "season") -> dict[str, dict]:
    """
    Fetch pitching stats for a list of player names from FanGraphs.

    Args:
        player_names: List of pitcher names to fetch stats for
        period: "season" (default), "this_week", or "last_week"

    Returns a dict keyed by player name with stats:
      era, whip, strikeouts, k_per_9, innings_pitched,
      quality_starts, saves, holds, svh, games_started, k_pct, bb_pct
    """
    if not player_names:
        return {}

    if period in ("this_week", "last_week"):
        return _get_pitcher_stats_weekly(player_names, period)
    else:
        return _get_pitcher_stats_season(player_names)


def _get_pitcher_stats_season(player_names: list[str]) -> dict[str, dict]:
    """Fetch season pitching stats from FanGraphs."""
    season = get_current_season()
    df = _fetch_pitching_leaderboard(season)

    if df is None or df.empty:
        logger.warning("No pitching leaderboard data available for %s", season)
        return {}

    return _extract_stats_from_df(df, player_names)


def _get_pitcher_stats_weekly(player_names: list[str], period: str) -> dict[str, dict]:
    """Fetch weekly pitching stats from MLB API boxscores."""
    start_date, end_date = _get_week_date_range(period)

    stats_by_id = _fetch_pitching_leaderboard_range(start_date, end_date)

    if not stats_by_id:
        logger.warning("No weekly pitching data available for %s to %s", start_date, end_date)
        return {}

    # Match by player ID via name lookup
    name_to_id = {}
    for pid, stats in stats_by_id.items():
        name_lower = stats.get("name", "").lower().strip()
        name_to_id[name_lower] = pid

    result = {}
    for name in player_names:
        name_lower = name.lower().strip()
        pid = name_to_id.get(name_lower)

        if not pid:
            # Try last-name match
            parts = name_lower.split()
            if len(parts) >= 2:
                last = parts[-1]
                for nl, p in name_to_id.items():
                    if nl.endswith(" " + last):
                        pid = p
                        break

        if pid and pid in stats_by_id:
            s = stats_by_id[pid]
            result[name] = {
                "era": s.get("era"),
                "whip": s.get("whip"),
                "strikeouts": s.get("strikeouts"),
                "k_per_9": s.get("k_per_9"),
                "innings_pitched": s.get("innings_pitched"),
                "quality_starts": None,  # Not tracked for relievers
                "saves": s.get("saves"),
                "holds": s.get("holds"),
                "svh": s.get("svh"),
                "games_started": 0,
                "k_pct": s.get("k_pct"),
                "bb_pct": s.get("bb_pct"),
            }
        else:
            logger.debug("No weekly stats found for: %s", name)

    return result


def _get_week_date_range(period: str) -> tuple[str, str]:
    """Get start and end dates for this_week or last_week."""
    from datetime import timedelta

    today = date.today()
    monday = today - timedelta(days=today.weekday())

    if period == "this_week":
        start = monday
        end = today
    else:  # last_week
        start = monday - timedelta(days=7)
        end = monday - timedelta(days=1)

    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def _extract_stats_from_df(df, player_names: list[str]) -> dict[str, dict]:
    """Extract stats from a FanGraphs DataFrame for the given player names."""
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
        sv = _safe_int(row.get("SV"))
        hld = _safe_int(row.get("HLD"))

        result[name] = {
            "era": _safe_float(row.get("ERA")),
            "whip": _safe_float(row.get("WHIP")),
            "strikeouts": _safe_int(row.get("SO")),
            "k_per_9": _safe_float(row.get("K/9")),
            "innings_pitched": _safe_float(row.get("IP")),
            "quality_starts": _safe_int(row.get("QS")),
            "saves": sv,
            "holds": hld,
            "svh": _safe_add(sv, hld),
            "games_started": _safe_int(row.get("GS")),
            "k_pct": _safe_float(row.get("K%")),
            "bb_pct": _safe_float(row.get("BB%")),
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
            k = _safe_int(s.get("strikeOuts")) or 0
            result[team_id] = {
                "avg": _safe_float(s.get("avg")),
                "ops": _safe_float(s.get("ops")),
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
