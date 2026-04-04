from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from services.rankings import PROFILES, get_rankings
from services.reliever_rankings import get_reliever_rankings as fetch_reliever_rankings

router = APIRouter()


@router.get("/api/rankings")
def get_pitcher_rankings(
    profile: str = Query(default="balanced"),
    week_start: date = Query(default=None),
    db: Session = Depends(get_db),
):
    return get_rankings(db, profile, week_start)


@router.get("/api/rankings/profiles")
def list_profiles():
    return [
        {"id": pid, "label": p["label"], "description": p["description"]}
        for pid, p in PROFILES.items()
    ]


@router.get("/api/relievers")
def get_reliever_rankings(
    season: int = Query(default=None),
    period: str = Query(default="season", pattern="^(season|this_week|last_week)$"),
    db: Session = Depends(get_db),
):
    return fetch_reliever_rankings(db, season, period)
