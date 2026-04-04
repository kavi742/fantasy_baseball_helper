"""
Thin wrapper around the mlb-statsapi library.
All MLB API calls go through here — makes swapping the library easy.
"""

import logging
from datetime import date
from functools import lru_cache

import statsapi

logger = logging.getLogger(__name__)

# Maps full MLB team names to standard abbreviations matching the MLB app.
# Minor league / exhibition teams fall back to the first-3-chars truncation.
_TEAM_ABBREV = {
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
    "Athletics": "ATH",
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


def get_weekly_schedule(start_date: date, end_date: date) -> list[dict]:
    """
    Fetch all games in the given date range with probable pitcher data.
    Returns a normalised list of game dicts.
    """
    raw = statsapi.schedule(
        start_date=start_date.strftime("%m/%d/%Y"),
        end_date=end_date.strftime("%m/%d/%Y"),
    )
    return [_normalise(game) for game in raw]


def _normalise(game: dict) -> dict:
    """
    Flatten the raw mlb-statsapi game dict into a clean shape.
    Probable pitcher fields are absent (not just None) when unannounced —
    we normalise that to None so callers don't have to handle KeyError.
    """
    away = game.get("away_name", "")
    home = game.get("home_name", "")
    return {
        "game_id": str(game.get("game_id", "")),
        "game_date": game.get("game_date", ""),
        "game_time": game.get("game_datetime"),
        "status": game.get("status"),
        "away_team": away,
        "home_team": home,
        "away_team_abbrev": _abbrev(away),
        "home_team_abbrev": _abbrev(home),
        "away_pitcher_id": game.get("away_probable_pitcher_id"),
        "away_pitcher_name": game.get("away_probable_pitcher"),
        "home_pitcher_id": game.get("home_probable_pitcher_id"),
        "home_pitcher_name": game.get("home_probable_pitcher"),
        "away_score": game.get("away_score"),
        "home_score": game.get("home_score"),
        "current_inning": game.get("current_inning"),
        "inning_state": game.get("inning_state"),
    }


def _abbrev(team_name: str) -> str:
    """Return the standard MLB abbreviation, falling back to 3-char truncation."""
    return _TEAM_ABBREV.get(team_name, team_name[:3].upper())


# Team ID to abbreviation mapping (for roster lookups)
_TEAM_ID_TO_ABBREV = {v: k for k, v in _TEAM_ABBREV.items()}
_TEAM_ID_MAP = {
    109: "ARI",
    144: "ATL",
    110: "BAL",
    111: "BOS",
    112: "CHC",
    145: "CWS",
    113: "CIN",
    114: "CLE",
    115: "COL",
    116: "DET",
    117: "HOU",
    118: "KC",
    108: "LAA",
    119: "LAD",
    146: "MIA",
    158: "MIL",
    142: "MIN",
    121: "NYM",
    147: "NYY",
    133: "OAK",
    143: "PHI",
    134: "PIT",
    135: "SD",
    136: "SEA",
    137: "SF",
    138: "STL",
    139: "TB",
    140: "TEX",
    141: "TOR",
    120: "WSH",
}


@lru_cache(maxsize=32)
def get_team_roster(team_id: int, season: int) -> list[dict]:
    """
    Fetch the active roster for a team.
    Returns list of player dicts with id, fullName, position info.
    """
    try:
        result = statsapi.get("team_roster", {"teamId": team_id, "season": season})
        if result is None:
            return []
        return result.get("roster", [])
    except Exception as e:
        logger.warning(f"Failed to fetch roster for team {team_id}: {e}")
        return []


@lru_cache(maxsize=4)
def _get_all_bullpens_cached(season: int) -> list[dict]:
    """
    Internal cached bullpen fetcher. Returns list of dicts.
    """
    bullpens = []
    for team_id, abbrev in _TEAM_ID_MAP.items():
        roster = get_team_roster(team_id, season)
        for entry in roster:
            person = entry.get("person", {})
            pos = entry.get("position", {})
            abbr = pos.get("abbreviation", "")
            if abbr == "P":
                status = entry.get("status", {})
                status_desc = status.get("description", "")
                is_active = "Active" in status_desc or status_desc == "14-Day IL"
                if is_active:
                    bullpens.append(
                        {
                            "player_id": person.get("id"),
                            "name": person.get("fullName"),
                            "team_abbrev": abbrev,
                            "team_id": team_id,
                        }
                    )

    return bullpens


def get_all_bullpens(season: int | None = None) -> list[dict]:
    """
    Fetch all bullpen pitchers from all MLB teams.
    Returns list of dicts with: player_id, name, team_abbrev, position.
    """
    if season is None:
        season = date.today().year

    cached = _get_all_bullpens_cached(season)
    return [dict(d) for d in cached]


@lru_cache(maxsize=500)
def get_pitcher_hand(player_id: int) -> str | None:
    """
    Fetch the throwing hand for a pitcher.
    Returns 'L', 'R', or None.
    """
    if not player_id:
        return None
    try:
        result = statsapi.get("people", {"personIds": player_id})
        if not result:
            return None
        people = result.get("people", [])
        if people:
            pitch_hand = people[0].get("pitchHand")
            if pitch_hand:
                return pitch_hand.get("code")
    except Exception as e:
        logger.warning(f"Failed to fetch hand for pitcher {player_id}: {e}")
    return None


@lru_cache(maxsize=1000)
def get_pitcher_hand_by_name(name: str) -> str | None:
    """
    Look up a pitcher by name and return their throwing hand.
    Returns 'L', 'R', or None.
    """
    if not name or name == "TBD":
        return None
    try:
        players = statsapi.lookup_player(name)
        if players:
            player_id = players[0].get("id")
            return get_pitcher_hand(player_id)
    except Exception as e:
        logger.warning(f"Failed to look up hand for pitcher {name}: {e}")
    return None


def _lookup_player_id(name: str) -> int | None:
    """Look up a player's MLB ID by name using pybaseball (faster than statsapi)."""
    try:
        import pybaseball

        pybaseball.cache.enable()
        parts = name.split()
        if len(parts) >= 2:
            last, first = parts[-1], " ".join(parts[:-1])
            lookup = pybaseball.playerid_lookup(last, first)
            if lookup is not None and not lookup.empty:
                return int(lookup.iloc[0]["key_mlbam"])
    except Exception:
        pass
    try:
        players = statsapi.lookup_player(name)
        if players:
            return players[0].get("id")
    except Exception:
        pass
    return None


def get_pitcher_hands_batch(
    names: list[str], db_session=None, name_to_id: dict[str, int] | None = None
) -> dict[str, str | None]:
    """
    Batch fetch pitcher hands for multiple names.
    Returns dict mapping name -> hand ('L', 'R', or None).
    Uses pybaseball for fast ID lookups, then bulk MLB API for hands.
    If name_to_id is provided, skips the pybaseball lookup (use when player IDs are already known).
    If db_session is provided, results are cached to the pitcher_hands table.
    """
    from models import PitcherHand

    result = {}
    names_to_fetch = []
    resolved_ids = name_to_id or {}
    db_hands = {}

    if db_session and resolved_ids:
        try:
            existing = (
                db_session.query(PitcherHand)
                .filter(PitcherHand.player_id.in_(list(resolved_ids.values())))
                .all()
            )
            for ph in existing:
                if ph.hand:
                    db_hands[ph.player_id] = ph.hand
        except Exception as e:
            logger.warning(f"Failed to check DB for pitcher hands: {e}")

    for name in names:
        if not name or name == "TBD":
            result[name] = None
            continue

        pid = resolved_ids.get(name)
        if pid and pid in db_hands:
            result[name] = db_hands[pid]
            continue

        names_to_fetch.append(name)

    if not names_to_fetch:
        return result

    needed_ids = []
    for name in names_to_fetch:
        pid = resolved_ids.get(name)
        if pid:
            needed_ids.append(pid)

    if needed_ids:
        try:
            id_str = ",".join(map(str, needed_ids))
            people_data = statsapi.get("people", {"personIds": id_str})
            people = people_data.get("people", []) if people_data else []

            id_to_hand = {}
            id_to_name = {}
            for person in people:
                pitch_hand = person.get("pitchHand", {})
                hand = pitch_hand.get("code") if pitch_hand else None
                pid = person.get("id")
                id_to_hand[pid] = hand
                id_to_name[pid] = person.get("fullName")

            for name in names_to_fetch:
                pid = resolved_ids.get(name)
                hand = id_to_hand.get(pid) if pid else None
                result[name] = hand
                if hand:
                    get_pitcher_hand_by_name(name)

            if db_session:
                for pid, hand in id_to_hand.items():
                    if hand:
                        try:
                            existing = (
                                db_session.query(PitcherHand)
                                .filter(PitcherHand.player_id == pid)
                                .first()
                            )
                            if not existing:
                                db_session.add(
                                    PitcherHand(
                                        player_id=pid,
                                        full_name=id_to_name.get(pid, ""),
                                        hand=hand,
                                    )
                                )
                            elif not existing.hand:
                                existing.hand = hand
                                existing.full_name = id_to_name.get(pid, existing.full_name)
                            db_session.commit()
                        except Exception as e:
                            logger.warning(f"Failed to save pitcher hand to DB: {e}")
                            db_session.rollback()

        except Exception as e:
            logger.warning(f"Failed to batch fetch pitcher hands: {e}")

    return result

    if not resolved_ids:
        for name in names_to_lookup:
            pid = _lookup_player_id(name)
            if pid:
                resolved_ids[name] = pid

    needed_ids = [resolved_ids[name] for name in names_to_lookup if name in resolved_ids]
    if needed_ids:
        id_to_hand = {}
        id_to_name = {}

        try:
            id_str = ",".join(map(str, needed_ids))
            people_data = statsapi.get("people", {"personIds": id_str})
            people = people_data.get("people", []) if people_data else []

            for person in people:
                pitch_hand = person.get("pitchHand", {})
                hand = pitch_hand.get("code") if pitch_hand else None
                pid = person.get("id")
                id_to_hand[pid] = hand
                id_to_name[pid] = person.get("fullName")

            for name in names_to_lookup:
                pid = resolved_ids.get(name)
                if pid:
                    hand = id_to_hand.get(pid)
                    result[name] = hand
                    if hand:
                        get_pitcher_hand_by_name(name)
                        hands_to_save[pid] = (hand, id_to_name.get(pid, name))

        except Exception as e:
            logger.warning(f"Failed to batch fetch pitcher hands: {e}")

    if db_session and hands_to_save:
        try:
            for pid, (hand, full_name) in hands_to_save.items():
                existing = (
                    db_session.query(PitcherHand).filter(PitcherHand.player_id == pid).first()
                )
                if not existing:
                    db_session.add(
                        PitcherHand(
                            player_id=pid,
                            full_name=full_name,
                            hand=hand,
                        )
                    )
                elif not existing.hand:
                    existing.hand = hand
                    existing.full_name = full_name
            db_session.commit()
        except Exception as e:
            logger.warning(f"Failed to save pitcher hands to DB: {e}")
            db_session.rollback()

    return result

    needed_ids = [name_to_id[name] for name in names_to_lookup if name in name_to_id]
    if needed_ids:
        id_to_hand = {}
        id_to_name = {}

        try:
            id_str = ",".join(map(str, needed_ids))
            people_data = statsapi.get("people", {"personIds": id_str})
            people = people_data.get("people", []) if people_data else []

            for person in people:
                pitch_hand = person.get("pitchHand", {})
                hand = pitch_hand.get("code") if pitch_hand else None
                pid = person.get("id")
                id_to_hand[pid] = hand
                id_to_name[pid] = person.get("fullName")

            for name in names_to_lookup:
                pid = name_to_id.get(name)
                if pid:
                    hand = id_to_hand.get(pid)
                    result[name] = hand
                    if hand:
                        get_pitcher_hand_by_name(name)
                        hands_to_save[pid] = (hand, id_to_name.get(pid, name))

        except Exception as e:
            logger.warning(f"Failed to batch fetch pitcher hands: {e}")

    if db_session and hands_to_save:
        try:
            for pid, (hand, full_name) in hands_to_save.items():
                existing = (
                    db_session.query(PitcherHand).filter(PitcherHand.player_id == pid).first()
                )
                if not existing:
                    db_session.add(
                        PitcherHand(
                            player_id=pid,
                            full_name=full_name,
                            hand=hand,
                        )
                    )
                elif not existing.hand:
                    existing.hand = hand
                    existing.full_name = full_name
            db_session.commit()
        except Exception as e:
            logger.warning(f"Failed to save pitcher hands to DB: {e}")
            db_session.rollback()

    return result


def is_quality_start(ip: float | str | None, er: int | str | None) -> bool:
    """
    Determine if a pitching performance qualifies as a Quality Start.
    A QS = 6+ innings pitched with less than 3 earned runs.
    """
    if ip is None or er is None:
        return False
    try:
        innings = float(ip)
        earned_runs = int(er)
        return innings >= 6 and earned_runs < 3
    except (ValueError, TypeError):
        return False


@lru_cache(maxsize=100)
def get_game_boxscore(game_id: int) -> dict | None:
    """
    Fetch boxscore data for a completed game.
    Returns dict with pitcher stats keyed by pitcher name.
    """
    try:
        data = statsapi.boxscore_data(game_id)
        if not data:
            return None

        pitcher_stats = {}
        for side in ["away", "home"]:
            pitchers = data.get(f"{side}Pitchers", [])
            for p in pitchers:
                name = p.get("name", "")
                if not name or name == f"{side.title()} Pitchers":
                    continue
                pitcher_stats[name] = {
                    "ip": p.get("ip"),
                    "er": p.get("er"),
                    "k": p.get("k"),
                    "h": p.get("h"),
                    "bb": p.get("bb"),
                }
        return pitcher_stats
    except Exception as e:
        logger.warning(f"Failed to fetch boxscore for game {game_id}: {e}")
        return None
