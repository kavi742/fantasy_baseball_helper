"""
Thin wrapper around the mlb-statsapi library.
All MLB API calls go through here — makes swapping the library easy.
"""
from datetime import date

import statsapi


def get_weekly_schedule(start_date: date, end_date: date) -> list[dict]:
    """
    Fetch all games in the given date range with probable pitcher data.
    Returns a normalised list of game dicts.
    """
    raw = statsapi.schedule(
        start_date=start_date.strftime("%m/%d/%Y"),
        end_date=end_date.strftime("%m/%d/%Y"),
    )

    games = []
    for game in raw:
        games.append(_normalise(game))

    return games


def _normalise(game: dict) -> dict:
    """
    Flatten the raw mlb-statsapi game dict into a clean shape.
    Probable pitcher fields are absent (not just None) when unannounced —
    we normalise that to None so callers don't have to handle KeyError.
    """
    return {
        "game_id": str(game.get("game_id", "")),
        "game_date": game.get("game_date", ""),
        "game_time": game.get("game_datetime", None),
        "status": game.get("status", None),
        "away_team": game.get("away_name", ""),
        "home_team": game.get("home_name", ""),
        "away_team_abbrev": game.get("away_name", "")[:3].upper(),
        "home_team_abbrev": game.get("home_name", "")[:3].upper(),
        "away_pitcher_id": game.get("away_probable_pitcher_id", None),
        "away_pitcher_name": game.get("away_probable_pitcher", None),
        "home_pitcher_id": game.get("home_probable_pitcher_id", None),
        "home_pitcher_name": game.get("home_probable_pitcher", None),
    }
