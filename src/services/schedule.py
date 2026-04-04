"""
Schedule service — cache-first pitcher data.

Flow:
  1. Check DB for games in the requested week that were fetched today
  2. If fresh data exists, return it
  3. If stale or missing, fetch from MLB API, persist, return
"""

from datetime import date, datetime, timedelta
import logging

from sqlalchemy.orm import Session

from mlb.client import (
    get_weekly_schedule,
    is_quality_start,
    get_game_boxscore,
    get_pitcher_hand_by_name,
)
from models import Game, Pitcher

logger = logging.getLogger(__name__)


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
            away_score=raw.get("away_score"),
            home_score=raw.get("home_score"),
            current_inning=raw.get("current_inning"),
            inning_state=raw.get("inning_state"),
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

        def to_int(val):
            if val is None or val == "":
                return None
            try:
                return int(val)
            except (ValueError, TypeError):
                return None

        away_score = to_int(game.away_score)
        home_score = to_int(game.home_score)
        current_inning = to_int(game.current_inning)

        away_qs = None
        home_qs = None

        if away_score is not None and home_score is not None:
            boxscore = get_game_boxscore(int(game.game_id))
            if boxscore:
                away_name = (
                    away_pitcher.full_name if away_pitcher and away_pitcher.full_name else ""
                )
                home_name = (
                    home_pitcher.full_name if home_pitcher and home_pitcher.full_name else ""
                )

                def names_match(pitcher_name, boxscore_name):
                    if not pitcher_name or not boxscore_name:
                        return False
                    pitcher_lower = pitcher_name.lower()
                    boxscore_lower = boxscore_name.lower()
                    parts = pitcher_lower.split()
                    return any(part in boxscore_lower for part in parts if len(part) > 3)

                for name, stats in boxscore.items():
                    if names_match(away_name, name):
                        away_qs = is_quality_start(stats.get("ip"), stats.get("er"))
                    if names_match(home_name, name):
                        home_qs = is_quality_start(stats.get("ip"), stats.get("er"))

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
                "away_score": away_score,
                "home_score": home_score,
                "current_inning": current_inning,
                "inning_state": game.inning_state if game.inning_state else None,
                "away_qs": away_qs,
                "home_qs": home_qs,
            }
        )
    return result


def _pitcher_dict(pitcher) -> dict:
    if pitcher is None:
        return {"name": "TBD", "player_id": None, "hand": None}
    name = pitcher.full_name or "TBD"
    hand = get_pitcher_hand_by_name(name) if name and name != "TBD" else None
    return {
        "name": name,
        "player_id": pitcher.player_id,
        "hand": hand,
    }


def _current_week_range() -> tuple[date, date]:
    """Returns Monday–Sunday of the current week."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday
