from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from schemas import GameSchema, WeekResponse
from services.schedule import get_week_games

router = APIRouter(prefix="/api", tags=["schedule"])


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


@router.get("/health")
def health():
    """Simple health check endpoint."""
    return {"status": "ok", "service": "fantasy-pitchers"}
