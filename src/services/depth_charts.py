"""
Hitting depth chart service.

Fetches batting order from recent games to build a team's typical lineup.
"""

import logging
from collections import defaultdict
from datetime import date, timedelta

import statsapi

logger = logging.getLogger(__name__)

TEAM_ABBREV_TO_ID: dict[str, int] = {
    "ARI": 109,
    "ATL": 144,
    "BAL": 110,
    "BOS": 111,
    "CHC": 112,
    "CWS": 145,
    "CIN": 113,
    "CLE": 114,
    "COL": 115,
    "DET": 116,
    "HOU": 117,
    "KC": 118,
    "LAA": 108,
    "LAD": 119,
    "MIA": 146,
    "MIL": 158,
    "MIN": 142,
    "NYM": 121,
    "NYY": 147,
    "OAK": 133,
    "PHI": 143,
    "PIT": 134,
    "SD": 135,
    "SEA": 136,
    "SF": 137,
    "STL": 138,
    "TB": 139,
    "TEX": 140,
    "TOR": 141,
    "WSH": 120,
}

TEAM_ID_TO_ABBREV: dict[int, str] = {v: k for k, v in TEAM_ABBREV_TO_ID.items()}

DEPTH_CHART_CACHE: dict[str, tuple[list[dict], float]] = {}
CACHE_TTL_SECONDS = 3600


def _get_team_abbrev_from_name(team_name: str) -> str | None:
    """Map team full name to abbreviation."""
    team_upper = team_name.upper()

    if "DIAMONDBACKS" in team_upper:
        return "ARI"
    elif "REDS" in team_upper:
        return "CIN"
    elif "ROYALS" in team_upper:
        return "KC"
    elif "WHITE SOX" in team_upper:
        return "CWS"
    elif "GUARDIANS" in team_upper:
        return "CLE"
    elif "TIGERS" in team_upper:
        return "DET"
    elif "ASTROS" in team_upper:
        return "HOU"
    elif "ANGELS" in team_upper:
        return "LAA"
    elif "DODGERS" in team_upper:
        return "LAD"
    elif "MARLINS" in team_upper:
        return "MIA"
    elif "BREWERS" in team_upper:
        return "MIL"
    elif "TWINS" in team_upper:
        return "MIN"
    elif "YANKEES" in team_upper:
        return "NYY"
    elif "METS" in team_upper:
        return "NYM"
    elif "ATHLETICS" in team_upper:
        return "OAK"
    elif "PHILLIES" in team_upper:
        return "PHI"
    elif "PIRATES" in team_upper:
        return "PIT"
    elif "PADRES" in team_upper:
        return "SD"
    elif "MARINERS" in team_upper:
        return "SEA"
    elif "GIANTS" in team_upper:
        return "SF"
    elif "CARDINALS" in team_upper:
        return "STL"
    elif "RAYS" in team_upper:
        return "TB"
    elif "RANGERS" in team_upper:
        return "TEX"
    elif "BLUE JAYS" in team_upper:
        return "TOR"
    elif "NATIONALS" in team_upper:
        return "WSH"
    elif "BRAVES" in team_upper:
        return "ATL"
    elif "CUBS" in team_upper:
        return "CHC"
    elif "ROCKIES" in team_upper:
        return "COL"
    elif "RED SOX" in team_upper:
        return "BOS"
    elif "ORIOLES" in team_upper:
        return "BAL"

    return None


def _fetch_team_depth_chart(team_abbrev: str, lookback_days: int = 7) -> list[dict]:
    """
    Fetch the hitting depth chart for a team based on recent games.
    Returns a list of batters ordered by batting order position.
    """
    team_id = TEAM_ABBREV_TO_ID.get(team_abbrev.upper())
    if not team_id:
        return []

    today = date.today()
    start = today - timedelta(days=lookback_days)

    batter_positions: dict[int, dict] = {}
    batter_games: dict[int, int] = defaultdict(int)

    for day_offset in range(lookback_days):
        day = start + timedelta(days=day_offset)
        day_str = day.strftime("%m/%d/%Y")

        try:
            games = statsapi.schedule(start_date=day_str, end_date=day_str)
        except Exception:
            continue

        for game in games:
            game_id = game.get("game_id")
            if not game_id:
                continue

            game_away_id = game.get("away_id")
            game_home_id = game.get("home_id")

            is_home = game_home_id == team_id
            is_away = game_away_id == team_id

            if not (is_home or is_away):
                continue

            side = "home" if is_home else "away"

            try:
                data = statsapi.get("game", {"gamePk": game_id})
                boxscore = data.get("liveData", {}).get("boxscore", {})
                team_data = boxscore.get("teams", {}).get(side, {})
                batters = team_data.get("batters", [])
                players = team_data.get("players", {})

                for position, pid in enumerate(batters[:15], 1):
                    player_key = f"ID{pid}"

                    if player_key not in players:
                        continue

                    person = players[player_key].get("person", {})
                    name = person.get("fullName", "")
                    pos = person.get("primaryPosition", {}).get("abbreviation", "")

                    if pid not in batter_positions or position < batter_positions[pid]["position"]:
                        batter_positions[pid] = {
                            "player_id": pid,
                            "name": name,
                            "primary_position": pos,
                            "batting_position": position,
                        }

                    batter_games[pid] += 1

            except Exception as e:
                logger.debug("Failed to get boxscore for game %s: %s", game_id, e)

    depth_chart = []
    for pid, data in batter_positions.items():
        data["games"] = batter_games[pid]
        depth_chart.append(data)

    depth_chart.sort(key=lambda x: (x["batting_position"], -x["games"]))

    return depth_chart


def get_depth_chart(team_abbrev: str, use_cache: bool = True) -> list[dict]:
    """Get the hitting depth chart for a team."""
    import time

    if use_cache:
        cache_key = team_abbrev.upper()
        if cache_key in DEPTH_CHART_CACHE:
            chart, timestamp = DEPTH_CHART_CACHE[cache_key]
            if time.time() - timestamp < CACHE_TTL_SECONDS:
                return chart

    chart = _fetch_team_depth_chart(team_abbrev, lookback_days=7)

    if use_cache:
        DEPTH_CHART_CACHE[team_abbrev.upper()] = (chart, time.time())

    return chart


def get_depth_charts_for_game(away_team: str, home_team: str) -> tuple[list[dict], list[dict]]:
    """Get depth charts for both teams in a game."""
    away_abbrev = _get_team_abbrev_from_name(away_team) if away_team else None
    home_abbrev = _get_team_abbrev_from_name(home_team) if home_team else None

    away_chart = get_depth_chart(away_abbrev) if away_abbrev else []
    home_chart = get_depth_chart(home_abbrev) if home_abbrev else []

    return away_chart, home_chart
