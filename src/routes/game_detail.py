from fastapi import APIRouter, HTTPException

from services.game_detail import get_game_detail

router = APIRouter(prefix="/api", tags=["game"])


@router.get("/game/{game_id}")
def get_game(game_id: int):
    """
    Get detailed game information including:
    - Game info (teams, pitchers, scores)
    - Lineups for both teams
    - Batter vs handedness splits (vs LHP / vs RHP)
    - Season batting stats for each batter
    - Career stats for each batter
    """
    result = get_game_detail(game_id)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result
