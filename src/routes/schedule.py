from datetime import date, timedelta
from functools import lru_cache

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from schemas import GameSchema, WeekResponse
from services.schedule import get_week_games, get_live_scores

router = APIRouter(prefix="/api", tags=["schedule"])

SCORES_CACHE_SECONDS = 30


@router.get("/week", response_model=WeekResponse)
def get_week(
    start: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Return all games and probable pitchers for the requested week.
    Defaults to the current Monday–Sunday scoring period.
    If start is provided, returns the 7-day window from that date.
    """
    if start is None:
        today = date.today()
        start = today - timedelta(days=today.weekday())  # this Monday
    end = start + timedelta(days=6)

    games_data = get_week_games(db, start, end)

    return WeekResponse(
        start_date=str(start),
        end_date=str(end),
        games=[GameSchema(**g) for g in games_data],
    )


@lru_cache(maxsize=1)
def _get_cached_scores(game_ids_tuple: tuple[str, ...]) -> list[dict]:
    """Cached score fetcher - 30 second TTL."""
    return get_live_scores(list(game_ids_tuple))


@router.get("/scores")
def get_scores(
    game_ids: str = Query(..., description="Comma-separated game IDs"),
):
    """
    Return live scores for specified games.
    Results cached for 30 seconds to avoid hammering MLB API.
    """
    game_id_list = [g.strip() for g in game_ids.split(",") if g.strip()]
    if not game_id_list:
        return {"scores": []}

    cached = _get_cached_scores(tuple(game_id_list))
    return {"scores": cached}


@router.get("/health")
def health():
    """Simple health check endpoint."""
    return {"status": "ok", "service": "fantasy-pitchers"}
