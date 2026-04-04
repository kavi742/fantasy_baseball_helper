"""
Reliever rankings service.

Flow:
  1. Fetch all bullpen pitchers from all MLB teams via mlb client
  2. Fetch stats for each reliever via pybaseball (FanGraphs)
     - "season": full season stats
     - "this_week": stats from Monday of current week
     - "last_week": stats from Monday of last week
  3. Batch fetch pitcher hands for all relievers (with DB caching)
  4. Rank by SV+H (saves + holds), with secondary sorting by K%, ERA, WHIP
"""

import logging
from datetime import date

from mlb.client import get_all_bullpens, get_pitcher_hands_batch
from mlb.stats import get_pitcher_stats

logger = logging.getLogger(__name__)


def get_reliever_rankings(
    db_session=None, season: int | None = None, period: str = "season"
) -> dict:
    """
    Fetch and rank all active bullpen pitchers.

    Args:
        db_session: Database session for caching pitcher hands
        season: MLB season year (defaults to current year)
        period: "season", "this_week", or "last_week"
    """
    if season is None:
        season = date.today().year

    bullpens = get_all_bullpens(season)

    player_names = [b["name"] for b in bullpens if b.get("name")]
    pitcher_stats = get_pitcher_stats(player_names, period) if player_names else {}

    name_to_id = {
        b["name"]: b["player_id"] for b in bullpens if b.get("name") and b.get("player_id")
    }
    hands = get_pitcher_hands_batch(player_names, db_session, name_to_id)

    for b in bullpens:
        stats = pitcher_stats.get(b["name"], {})
        b["era"] = stats.get("era")
        b["whip"] = stats.get("whip")
        b["strikeouts"] = stats.get("strikeouts")
        b["innings_pitched"] = stats.get("innings_pitched")
        b["saves"] = stats.get("saves")
        b["holds"] = stats.get("holds")
        b["svh"] = stats.get("svh")
        b["k_pct"] = stats.get("k_pct")
        b["bb_pct"] = stats.get("bb_pct")
        b["k_per_9"] = stats.get("k_per_9")
        b["games_started"] = stats.get("games_started")
        b["hand"] = hands.get(b["name"]) if b.get("name") else None
        b["k_minus_bb"] = (
            round(b["k_pct"] - b["bb_pct"], 4)
            if (b["k_pct"] is not None and b["bb_pct"] is not None)
            else None
        )
        b["period"] = period

    relievers_with_stats = [
        b
        for b in bullpens
        if b.get("games_started", -1) == 0
        and ((b.get("svh") or 0) > 0 or b.get("k_pct") is not None)
    ]

    relievers_with_stats.sort(
        key=lambda x: (
            -(x.get("svh") or 0),
            -(x.get("k_pct") or 0) if x.get("k_pct") else -999,
            x.get("era") if x.get("era") else 999,
            x.get("whip") if x.get("whip") else 999,
        )
    )

    for i, r in enumerate(relievers_with_stats):
        r["rank"] = i + 1

    return {"pitchers": relievers_with_stats, "period": period}
