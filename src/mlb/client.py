"""
Thin wrapper around the mlb-statsapi library.
All MLB API calls go through here — makes swapping the library easy.
"""

import logging
from datetime import date
from functools import lru_cache

import statsapi

logger = logging.getLogger(__name__)

# Maps full MLB team names to standard abbreviations matching the MLB app.
# Minor league / exhibition teams fall back to the first-3-chars truncation.
_TEAM_ABBREV = {
    "Arizona Diamondbacks": "ARI",
    "Atlanta Braves": "ATL",
    "Baltimore Orioles": "BAL",
    "Boston Red Sox": "BOS",
    "Chicago Cubs": "CHC",
    "Chicago White Sox": "CWS",
    "Cincinnati Reds": "CIN",
    "Cleveland Guardians": "CLE",
    "Colorado Rockies": "COL",
    "Detroit Tigers": "DET",
    "Houston Astros": "HOU",
    "Kansas City Royals": "KC",
    "Los Angeles Angels": "LAA",
    "Los Angeles Dodgers": "LAD",
    "Miami Marlins": "MIA",
    "Milwaukee Brewers": "MIL",
    "Minnesota Twins": "MIN",
    "New York Mets": "NYM",
    "New York Yankees": "NYY",
    "Oakland Athletics": "OAK",
    "Athletics": "ATH",
    "Philadelphia Phillies": "PHI",
    "Pittsburgh Pirates": "PIT",
    "San Diego Padres": "SD",
    "San Francisco Giants": "SF",
    "Seattle Mariners": "SEA",
    "St. Louis Cardinals": "STL",
    "Tampa Bay Rays": "TB",
    "Texas Rangers": "TEX",
    "Toronto Blue Jays": "TOR",
    "Washington Nationals": "WSH",
}


def get_weekly_schedule(start_date: date, end_date: date) -> list[dict]:
    """
    Fetch all games in the given date range with probable pitcher data.
    Returns a normalised list of game dicts.
    """
    raw = statsapi.schedule(
        start_date=start_date.strftime("%m/%d/%Y"),
        end_date=end_date.strftime("%m/%d/%Y"),
    )
    return [_normalise(game) for game in raw]


def _normalise(game: dict) -> dict:
    """
    Flatten the raw mlb-statsapi game dict into a clean shape.
    Probable pitcher fields are absent (not just None) when unannounced —
    we normalise that to None so callers don't have to handle KeyError.
    """
    away = game.get("away_name", "")
    home = game.get("home_name", "")
    return {
        "game_id": str(game.get("game_id", "")),
        "game_date": game.get("game_date", ""),
        "game_time": game.get("game_datetime", None),
        "status": game.get("status", None),
        "away_team": away,
        "home_team": home,
        "away_team_abbrev": _abbrev(away),
        "home_team_abbrev": _abbrev(home),
        "away_pitcher_id": game.get("away_probable_pitcher_id", None),
        "away_pitcher_name": game.get("away_probable_pitcher", None),
        "home_pitcher_id": game.get("home_probable_pitcher_id", None),
        "home_pitcher_name": game.get("home_probable_pitcher", None),
    }


def _abbrev(team_name: str) -> str:
    """Return the standard MLB abbreviation, falling back to 3-char truncation."""
    return _TEAM_ABBREV.get(team_name, team_name[:3].upper())


# Team ID to abbreviation mapping (for roster lookups)
_TEAM_ID_TO_ABBREV = {v: k for k, v in _TEAM_ABBREV.items()}
_TEAM_ID_MAP = {
    109: "ARI",
    144: "ATL",
    110: "BAL",
    111: "BOS",
    112: "CHC",
    145: "CWS",
    113: "CIN",
    114: "CLE",
    115: "COL",
    116: "DET",
    117: "HOU",
    118: "KC",
    108: "LAA",
    119: "LAD",
    146: "MIA",
    158: "MIL",
    142: "MIN",
    121: "NYM",
    147: "NYY",
    133: "OAK",
    143: "PHI",
    134: "PIT",
    135: "SD",
    136: "SEA",
    137: "SF",
    138: "STL",
    139: "TB",
    140: "TEX",
    141: "TOR",
    120: "WSH",
}


@lru_cache(maxsize=1)
def get_team_roster(team_id: int, season: int) -> list[dict]:
    """
    Fetch the active roster for a team.
    Returns list of player dicts with id, fullName, position info.
    """
    try:
        result = statsapi.get("team_roster", {"teamId": team_id, "season": season})
        if result is None:
            return []
        return result.get("roster", [])
    except Exception as e:
        logger.warning(f"Failed to fetch roster for team {team_id}: {e}")
        return []


def get_all_bullpens(season: int | None = None) -> list[dict]:
    """
    Fetch all bullpen pitchers from all MLB teams.
    Returns list of dicts with: player_id, name, team_abbrev, position.
    """
    if season is None:
        season = date.today().year

    bullpens = []
    for team_id, abbrev in _TEAM_ID_MAP.items():
        roster = get_team_roster(team_id, season)
        for entry in roster:
            person = entry.get("person", {})
            pos = entry.get("position", {})
            abbr = pos.get("abbreviation", "")
            if abbr == "P":
                status = entry.get("status", {})
                status_desc = status.get("description", "")
                is_active = "Active" in status_desc or status_desc == "14-Day IL"
                if is_active:
                    bullpens.append(
                        {
                            "player_id": person.get("id"),
                            "name": person.get("fullName"),
                            "team_abbrev": abbrev,
                            "team_id": team_id,
                        }
                    )

    return bullpens
