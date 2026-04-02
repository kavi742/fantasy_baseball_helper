from pydantic import BaseModel


class PitcherSchema(BaseModel):
    name: str
    player_id: int | None


class GameSchema(BaseModel):
    game_id: str
    game_date: str
    game_time: str | None
    status: str | None
    away_team: str
    home_team: str
    away_team_abbrev: str
    home_team_abbrev: str
    away_pitcher: PitcherSchema
    home_pitcher: PitcherSchema
    away_score: int | None
    home_score: int | None
    current_inning: int | None
    inning_state: str | None
    away_qs: bool | None
    home_qs: bool | None

    model_config = {"from_attributes": True}


class WeekResponse(BaseModel):
    start_date: str
    end_date: str
    games: list[GameSchema]
