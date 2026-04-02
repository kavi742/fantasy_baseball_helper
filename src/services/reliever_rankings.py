"""
Reliever rankings service.

Flow:
  1. Fetch all bullpen pitchers from all MLB teams via mlb client
  2. Fetch season stats for each reliever via pybaseball (FanGraphs)
  3. Rank by SV+H (saves + holds), with secondary sorting by K%, ERA, WHIP
"""

import logging
from datetime import date

from mlb.client import get_all_bullpens
from mlb.stats import get_pitcher_stats

logger = logging.getLogger(__name__)


def get_reliever_rankings(season: int | None = None) -> dict:
    """
    Fetch and rank all active bullpen pitchers.
    Returns dict with list of ranked relievers.
    """
    if season is None:
        season = date.today().year

    bullpens = get_all_bullpens(season)

    player_names = [b["name"] for b in bullpens if b.get("name")]
    pitcher_stats = get_pitcher_stats(player_names) if player_names else {}

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
        b["xfip"] = stats.get("xfip")
        b["siera"] = stats.get("siera")
        b["k_minus_bb"] = (
            round(b["k_pct"] - b["bb_pct"], 4)
            if (b["k_pct"] is not None and b["bb_pct"] is not None)
            else None
        )

    relievers_with_stats = [
        b for b in bullpens if (b.get("svh") or 0) > 0 or b.get("k_pct") is not None
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

    return {"pitchers": relievers_with_stats}
