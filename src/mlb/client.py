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
        "game_time": game.get("game_datetime"),
        "status": game.get("status"),
        "away_team": away,
        "home_team": home,
        "away_team_abbrev": _abbrev(away),
        "home_team_abbrev": _abbrev(home),
        "away_pitcher_id": game.get("away_probable_pitcher_id"),
        "away_pitcher_name": game.get("away_probable_pitcher"),
        "home_pitcher_id": game.get("home_probable_pitcher_id"),
        "home_pitcher_name": game.get("home_probable_pitcher"),
        "away_score": game.get("away_score"),
        "home_score": game.get("home_score"),
        "current_inning": game.get("current_inning"),
        "inning_state": game.get("inning_state"),
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


@lru_cache(maxsize=500)
def get_pitcher_hand(player_id: int) -> str | None:
    """
    Fetch the throwing hand for a pitcher.
    Returns 'L', 'R', or None.
    """
    if not player_id:
        return None
    try:
        result = statsapi.get("people", {"personIds": player_id})
        if not result:
            return None
        people = result.get("people", [])
        if people:
            pitch_hand = people[0].get("pitchHand")
            if pitch_hand:
                return pitch_hand.get("code")
    except Exception as e:
        logger.warning(f"Failed to fetch hand for pitcher {player_id}: {e}")
    return None


@lru_cache(maxsize=1000)
def get_pitcher_hand_by_name(name: str) -> str | None:
    """
    Look up a pitcher by name and return their throwing hand.
    Returns 'L', 'R', or None.
    """
    if not name or name == "TBD":
        return None
    try:
        players = statsapi.lookup_player(name)
        if players:
            player_id = players[0].get("id")
            return get_pitcher_hand(player_id)
    except Exception as e:
        logger.warning(f"Failed to look up hand for pitcher {name}: {e}")
    return None


def is_quality_start(ip: float | str | None, er: int | str | None) -> bool:
    """
    Determine if a pitching performance qualifies as a Quality Start.
    A QS = 6+ innings pitched with less than 3 earned runs.
    """
    if ip is None or er is None:
        return False
    try:
        innings = float(ip)
        earned_runs = int(er)
        return innings >= 6 and earned_runs < 3
    except (ValueError, TypeError):
        return False


@lru_cache(maxsize=100)
def get_game_boxscore(game_id: int) -> dict | None:
    """
    Fetch boxscore data for a completed game.
    Returns dict with pitcher stats keyed by pitcher name.
    """
    try:
        data = statsapi.boxscore_data(game_id)
        if not data:
            return None

        pitcher_stats = {}
        for side in ["away", "home"]:
            pitchers = data.get(f"{side}Pitchers", [])
            for p in pitchers:
                name = p.get("name", "")
                if not name or name == f"{side.title()} Pitchers":
                    continue
                pitcher_stats[name] = {
                    "ip": p.get("ip"),
                    "er": p.get("er"),
                    "k": p.get("k"),
                    "h": p.get("h"),
                    "bb": p.get("bb"),
                }
        return pitcher_stats
    except Exception as e:
        logger.warning(f"Failed to fetch boxscore for game {game_id}: {e}")
        return None
