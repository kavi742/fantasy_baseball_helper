"""
Game detail service - fetches lineups, splits, and stats for a specific game.
"""

import logging
from datetime import date

import requests
import statsapi

logger = logging.getLogger(__name__)


def get_current_season() -> int:
    today = date.today()
    return today.year if today.month >= 4 else today.year - 1


def _safe_float(val) -> float | None:
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _safe_int(val) -> int | None:
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _safe_float_str(val) -> float | None:
    """Parse float from string value (handles '.259' format)."""
    if not val:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _safe_int_str(val) -> int | None:
    """Parse int from string value."""
    if not val:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _get_favorable_split(splits: dict | None, pitcher_hand: str | None) -> str | None:
    """
    Determine which split is favorable for a batter against a pitcher.

    Returns 'vs_lhp' if the batter performs better vs LHP than RHP,
    Returns 'vs_rhp' if the batter performs better vs RHP than LHP,
    Returns None if there's no clear advantage or insufficient data.

    Requires a meaningful sample size (min 10 PA) in each split to consider it reliable.
    """
    if not splits or not pitcher_hand:
        return None

    vs_lhp = splits.get("vs_lhp")
    vs_rhp = splits.get("vs_rhp")

    lhp_ops = vs_lhp.get("ops") if vs_lhp else None
    rhp_ops = vs_rhp.get("ops") if vs_rhp else None

    lhp_pa = vs_lhp.get("pa") if vs_lhp else 0
    rhp_pa = vs_rhp.get("pa") if vs_rhp else 0

    min_pa = 10
    ops_advantage = 0.05

    if lhp_ops is None or rhp_ops is None:
        return None

    if lhp_pa < min_pa or rhp_pa < min_pa:
        return None

    if pitcher_hand == "L" and lhp_ops > rhp_ops + ops_advantage:
        return "vs_lhp"
    if pitcher_hand == "R" and rhp_ops > lhp_ops + ops_advantage:
        return "vs_rhp"

    return None


def _get_pitcher_hand(player_id: int | None) -> str | None:
    """Get pitcher throwing hand from MLB API."""
    if not player_id:
        return None
    try:
        result = statsapi.get("people", {"personIds": player_id})
        if result and result.get("people"):
            pitch_hand = result["people"][0].get("pitchHand")
            if pitch_hand:
                return pitch_hand.get("code")
    except Exception as e:
        logger.warning(f"Failed to get hand for pitcher {player_id}: {e}")
    return None


def _get_batter_splits_via_mlb(batter_id: int) -> dict | None:
    """Get batting splits for a batter via MLB API (vs LHP / vs RHP)."""
    if not batter_id:
        return None

    try:
        # Use the people/{id}/stats endpoint with sitCodes for handedness splits
        # sitCodes: vl = vs Left, vr = vs Right
        url = f"https://statsapi.mlb.com/api/v1/people/{batter_id}/stats"
        params = {
            "stats": "statSplits",
            "group": "hitting",
            "gameType": "R",
            "sitCodes": "vl,vr",
            "season": get_current_season(),
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        result = response.json()

        if not result or "stats" not in result:
            return None

        stats_list = result.get("stats", [])
        if not stats_list:
            return None

        splits_list = stats_list[0].get("splits", [])

        vs_lhp = None
        vs_rhp = None

        for split in splits_list:
            stat = split.get("stat", {})
            split_code = split.get("split", {}).get("code", "")

            if split_code == "vl":
                vs_lhp = _parse_split_stat(stat)
            elif split_code == "vr":
                vs_rhp = _parse_split_stat(stat)

        return {"vs_lhp": vs_lhp, "vs_rhp": vs_rhp}

    except Exception as e:
        logger.debug(f"Failed to get splits for batter {batter_id}: {e}")
        return None


def _parse_split_stat(stat: dict) -> dict:
    """Parse batting stat from MLB API split."""
    return {
        "pa": _safe_int(stat.get("plateAppearances")),
        "avg": _safe_float(stat.get("avg")),
        "obp": _safe_float(stat.get("obp")),
        "slg": _safe_float(stat.get("slg")),
        "ops": _safe_float(stat.get("ops")),
        "hr": _safe_int(stat.get("homeRuns")),
        "bb": _safe_int(stat.get("walks")),
        "k": _safe_int(stat.get("strikeOuts")),
        "h": _safe_int(stat.get("hits")),
    }


def get_lineups(game_id: int) -> dict:
    """
    Fetch lineups for both teams from the game's boxscore.
    Returns batting orders for away and home teams.
    """
    try:
        data = statsapi.boxscore_data(game_id)
        if not data:
            return {"away": [], "home": []}

        away_lineup = []
        home_lineup = []

        away_batters = data.get("awayBatters", []) or []
        for b in away_batters:
            batter_id = b.get("personId")
            if not batter_id or batter_id == 0:
                continue
            away_lineup.append(
                {
                    "id": batter_id,
                    "name": b.get("name"),
                    "position": b.get("position"),
                    "bat_order": b.get("battingOrder"),
                    "avg": _safe_float_str(b.get("avg")),
                    "hr": _safe_int_str(b.get("hr")),
                    "rbi": _safe_int_str(b.get("rbi")),
                    "ops": _safe_float_str(b.get("ops")),
                }
            )

        home_batters = data.get("homeBatters", []) or []
        for b in home_batters:
            batter_id = b.get("personId")
            if not batter_id or batter_id == 0:
                continue
            home_lineup.append(
                {
                    "id": batter_id,
                    "name": b.get("name"),
                    "position": b.get("position"),
                    "bat_order": b.get("battingOrder"),
                    "avg": _safe_float_str(b.get("avg")),
                    "hr": _safe_int_str(b.get("hr")),
                    "rbi": _safe_int_str(b.get("rbi")),
                    "ops": _safe_float_str(b.get("ops")),
                }
            )

        away_lineup = [b for b in away_lineup if b.get("bat_order")]
        home_lineup = [b for b in home_lineup if b.get("bat_order")]
        away_lineup.sort(key=lambda x: x.get("bat_order") or 999)
        home_lineup.sort(key=lambda x: x.get("bat_order") or 999)

        return {"away": away_lineup, "home": home_lineup}
    except Exception as e:
        logger.warning(f"Failed to get lineups for game {game_id}: {e}")
        return {"away": [], "home": []}


def _get_pitcher_by_name(name: str) -> dict | None:
    """Look up a pitcher by name and return id and hand."""
    if not name or name == "TBD":
        return None
    try:
        players = statsapi.lookup_player(name)
        if players:
            player_id = players[0].get("id")
            if player_id:
                return {
                    "id": player_id,
                    "hand": _get_pitcher_hand(player_id),
                }
    except Exception as e:
        logger.debug(f"Failed to look up pitcher {name}: {e}")
    return None


def get_game_pitchers(game_id: int) -> dict:
    """
    Fetch probable pitchers and their stats for a game.
    Uses ID if available, otherwise falls back to name lookup.
    """
    try:
        data = statsapi.schedule(
            start_date=date.today().strftime("%m/%d/%Y"),
            end_date=date.today().strftime("%m/%d/%Y"),
        )

        game = None
        for g in data:
            if str(g.get("game_id")) == str(game_id):
                game = g
                break

        if not game:
            return {"away": None, "home": None}

        away_id = game.get("away_probable_pitcher_id")
        home_id = game.get("home_probable_pitcher_id")
        away_name = game.get("away_probable_pitcher")
        home_name = game.get("home_probable_pitcher")

        away_pitcher = None
        if away_name and away_name != "TBD":
            if away_id:
                away_pitcher = {
                    "id": away_id,
                    "name": away_name,
                    "hand": _get_pitcher_hand(away_id),
                }
            else:
                lookup = _get_pitcher_by_name(away_name)
                if lookup:
                    away_pitcher = {
                        "id": lookup["id"],
                        "name": away_name,
                        "hand": lookup["hand"],
                    }
                else:
                    away_pitcher = {"id": None, "name": away_name, "hand": None}

        home_pitcher = None
        if home_name and home_name != "TBD":
            if home_id:
                home_pitcher = {
                    "id": home_id,
                    "name": home_name,
                    "hand": _get_pitcher_hand(home_id),
                }
            else:
                lookup = _get_pitcher_by_name(home_name)
                if lookup:
                    home_pitcher = {
                        "id": lookup["id"],
                        "name": home_name,
                        "hand": lookup["hand"],
                    }
                else:
                    home_pitcher = {"id": None, "name": home_name, "hand": None}

        return {"away": away_pitcher, "home": home_pitcher}
    except Exception as e:
        logger.warning(f"Failed to get game pitchers for {game_id}: {e}")
        return {"away": None, "home": None}


def get_batter_info(batter_id: int) -> dict | None:
    """Get batter info with handedness and position."""
    if not batter_id:
        return None
    try:
        result = statsapi.get("people", {"personIds": batter_id})
        if result and result.get("people"):
            person = result["people"][0]
            return {
                "id": batter_id,
                "name": person.get("fullName"),
                "bat_hand": person.get("batSide", {}).get("code"),
                "position": person.get("primaryPosition", {}).get("abbreviation"),
            }
    except Exception as e:
        logger.warning(f"Failed to get batter info for {batter_id}: {e}")
    return None


def get_batter_season_stats(batter_id: int) -> dict | None:
    """Get batter's current season stats from MLB API."""
    if not batter_id:
        return None
    try:
        url = f"https://statsapi.mlb.com/api/v1/people/{batter_id}/stats"
        params = {
            "stats": "season",
            "group": "hitting",
            "season": get_current_season(),
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "stats" not in data:
            return None

        stats_list = data["stats"]
        if not stats_list:
            return None

        splits = stats_list[0].get("splits", [])
        if not splits:
            return None

        stat = splits[0].get("stat", {})
        return {
            "games": _safe_int(stat.get("gamesPlayed")),
            "pa": _safe_int(stat.get("plateAppearances")),
            "avg": _safe_float(stat.get("avg")),
            "obp": _safe_float(stat.get("obp")),
            "slg": _safe_float(stat.get("slg")),
            "ops": _safe_float(stat.get("ops")),
            "hr": _safe_int(stat.get("homeRuns")),
            "rbi": _safe_int(stat.get("rbi")),
            "sb": _safe_int(stat.get("stolenBases")),
            "bb": _safe_int(stat.get("walks")),
            "k": _safe_int(stat.get("strikeOuts")),
            "h": _safe_int(stat.get("hits")),
        }
    except Exception as e:
        logger.warning(f"Failed to get season stats for batter {batter_id}: {e}")
    return None


def get_game_detail(game_id: int) -> dict:
    """
    Get complete game detail including:
    - Game info (teams, pitchers, scores)
    - Lineups for both teams
    - Batter vs handedness splits
    - Season stats for batters
    """
    season = get_current_season()

    game_data = None
    try:
        schedule_data = statsapi.schedule(
            start_date="01/01/" + str(season),
            end_date="12/31/" + str(season),
        )
        for g in schedule_data:
            if str(g.get("game_id")) == str(game_id):
                game_data = g
                break
    except Exception as e:
        logger.warning(f"Failed to find game {game_id}: {e}")

    if not game_data:
        return {"error": "Game not found"}

    pitchers = get_game_pitchers(game_id)
    lineups = get_lineups(game_id)

    away_pitcher_hand = pitchers.get("away", {}).get("hand") if pitchers.get("away") else None
    home_pitcher_hand = pitchers.get("home", {}).get("hand") if pitchers.get("home") else None

    away_batters = []
    for batter in lineups.get("away", []):
        batter_id = batter.get("id")
        if not batter_id:
            continue

        batter_info = get_batter_info(batter_id)
        splits = _get_batter_splits_via_mlb(batter_id)
        season_stats = get_batter_season_stats(batter_id)

        favorable_split = _get_favorable_split(splits, away_pitcher_hand)

        away_batters.append(
            {
                **batter,
                "name": batter_info.get("name") if batter_info else batter.get("name"),
                "bat_hand": batter_info.get("bat_hand") if batter_info else None,
                "splits": splits,
                "season_stats": season_stats,
                "favorable_split": favorable_split,
            }
        )

    home_batters = []
    for batter in lineups.get("home", []):
        batter_id = batter.get("id")
        if not batter_id:
            continue

        batter_info = get_batter_info(batter_id)
        splits = _get_batter_splits_via_mlb(batter_id)
        season_stats = get_batter_season_stats(batter_id)

        favorable_split = _get_favorable_split(splits, home_pitcher_hand)

        home_batters.append(
            {
                **batter,
                "name": batter_info.get("name") if batter_info else batter.get("name"),
                "bat_hand": batter_info.get("bat_hand") if batter_info else None,
                "splits": splits,
                "season_stats": season_stats,
                "favorable_split": favorable_split,
            }
        )

    away_team = game_data.get("away_name", "")
    home_team = game_data.get("home_name", "")

    abbrev_map = {
        "Arizona Diamondbacks": "ARI",
        "Atlanta Braves": "ATL",
        "Baltimore Orioles": "BAL",
        "Boston Red Sox": "BOS",
        "Chicago Cubs": "CHC",
        "Chicago White Sox": "CWS",
        "Cincinnati Reds": "CIN",
        "Cleveland Guardians": "CLE",
        "Colorado Rockies": "COL",
        "Detroit Tigers": "DET",
        "Houston Astros": "HOU",
        "Kansas City Royals": "KC",
        "Los Angeles Angels": "LAA",
        "Los Angeles Dodgers": "LAD",
        "Miami Marlins": "MIA",
        "Milwaukee Brewers": "MIL",
        "Minnesota Twins": "MIN",
        "New York Mets": "NYM",
        "New York Yankees": "NYY",
        "Oakland Athletics": "OAK",
        "Philadelphia Phillies": "PHI",
        "Pittsburgh Pirates": "PIT",
        "San Diego Padres": "SD",
        "San Francisco Giants": "SF",
        "Seattle Mariners": "SEA",
        "St. Louis Cardinals": "STL",
        "Tampa Bay Rays": "TB",
        "Texas Rangers": "TEX",
        "Toronto Blue Jays": "TOR",
        "Washington Nationals": "WSH",
    }

    return {
        "game_id": str(game_id),
        "game_date": game_data.get("game_date"),
        "game_time": game_data.get("game_datetime"),
        "status": game_data.get("status"),
        "away_team": away_team,
        "home_team": home_team,
        "away_abbrev": abbrev_map.get(away_team, away_team[:3].upper()),
        "home_abbrev": abbrev_map.get(home_team, home_team[:3].upper()),
        "away_score": game_data.get("away_score"),
        "home_score": game_data.get("home_score"),
        "away_pitcher": pitchers.get("away"),
        "home_pitcher": pitchers.get("home"),
        "away_batters": away_batters,
        "home_batters": home_batters,
    }
