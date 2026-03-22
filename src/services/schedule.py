"""
Schedule service — cache-first pitcher data.

Flow:
  1. Check DB for games in the requested week that were fetched today
  2. If fresh data exists, return it
  3. If stale or missing, fetch from MLB API, persist, return
"""

from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from mlb.client import get_weekly_schedule
from models import Game, Pitcher


def get_week_games(db: Session, start_date: date, end_date: date) -> list[dict]:
    """
    Return games for the given date range.
    Refreshes from the MLB API if the cache is stale (older than today).
    """
    if _cache_is_fresh(db, start_date):
        return _serialise(db, start_date, end_date)

    raw_games = get_weekly_schedule(start_date, end_date)
    _persist(db, raw_games)
    return _serialise(db, start_date, end_date)


def refresh_current_week(db: Session) -> None:
    """
    Called by the scheduler each morning.
    Forces a fresh fetch for the current fantasy week.
    """
    start, end = _current_week_range()
    raw_games = get_weekly_schedule(start, end)
    _persist(db, raw_games)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _cache_is_fresh(db: Session, start_date: date) -> bool:
    """True if we already fetched data for this week today."""
    today = date.today()
    game = (
        db.query(Game)
        .filter(Game.game_date >= start_date)
        .filter(Game.fetched_at >= datetime.combine(today, datetime.min.time()))
        .first()
    )
    return game is not None


def _persist(db: Session, raw_games: list[dict]) -> None:
    """
    Upsert games and their pitchers.
    Deletes existing records for the same game_id before inserting fresh data
    so pitcher updates (TBD → confirmed) are always reflected.
    """
    for raw in raw_games:
        existing = db.query(Game).filter(Game.game_id == raw["game_id"]).first()
        if existing:
            db.delete(existing)
            db.flush()

        game = Game(
            game_id=raw["game_id"],
            game_date=date.fromisoformat(raw["game_date"]),
            game_time=raw["game_time"],
            status=raw["status"],
            away_team=raw["away_team"],
            home_team=raw["home_team"],
            away_team_abbrev=raw["away_team_abbrev"],
            home_team_abbrev=raw["home_team_abbrev"],
            fetched_at=datetime.utcnow(),
        )
        db.add(game)
        db.flush()  # get game.id before adding pitchers

        db.add(
            Pitcher(
                game_id=game.id,
                side="away",
                player_id=raw["away_pitcher_id"],
                full_name=raw["away_pitcher_name"],
            )
        )
        db.add(
            Pitcher(
                game_id=game.id,
                side="home",
                player_id=raw["home_pitcher_id"],
                full_name=raw["home_pitcher_name"],
            )
        )

    db.commit()


def _serialise(db: Session, start_date: date, end_date: date) -> list[dict]:
    """Query games from DB and return as plain dicts for the API layer."""
    games = (
        db.query(Game)
        .filter(Game.game_date >= start_date, Game.game_date <= end_date)
        .order_by(Game.game_date, Game.game_time)
        .all()
    )

    result = []
    for game in games:
        away_pitcher = next((p for p in game.pitchers if p.side == "away"), None)
        home_pitcher = next((p for p in game.pitchers if p.side == "home"), None)
        result.append(
            {
                "game_id": game.game_id,
                "game_date": str(game.game_date),
                "game_time": game.game_time,
                "status": game.status,
                "away_team": game.away_team,
                "home_team": game.home_team,
                "away_team_abbrev": game.away_team_abbrev,
                "home_team_abbrev": game.home_team_abbrev,
                "away_pitcher": _pitcher_dict(away_pitcher),
                "home_pitcher": _pitcher_dict(home_pitcher),
            }
        )
    return result


def _pitcher_dict(pitcher) -> dict:
    if pitcher is None:
        return {"name": "TBD", "player_id": None}
    return {
        "name": pitcher.full_name or "TBD",
        "player_id": pitcher.player_id,
    }


def _current_week_range() -> tuple[date, date]:
    """Returns Monday–Sunday of the current week."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday
