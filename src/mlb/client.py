"""
Thin wrapper around the mlb-statsapi library.
All MLB API calls go through here — makes swapping the library easy.
"""

from datetime import date

import statsapi

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
