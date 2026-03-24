"""
Rankings service for Phase 2.5 — Pitcher Rankings Page.

Flow:
  1. Pull probable pitchers for the current week from DB
  2. Fetch season stats for each pitcher from MLB Stats API
  3. Fetch team batting stats for each opposing team
  4. Normalise all stats to 0–1 scale
  5. Apply preset profile weights
  6. Compute opponent difficulty modifier (0.7–1.0 range, penalises tough offences)
  7. Return sorted list of ranked pitchers with all data attached
"""
import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from mlb.stats import get_pitcher_stats, get_team_batting_stats
from models import Game, Pitcher

logger = logging.getLogger(__name__)

# ── Preset profiles ───────────────────────────────────────────────────────────
# Weights must sum to 1.0 across the five categories.
# era_whip are negative stats — lower is better — handled in normalisation.

PROFILES = {
    "balanced": {
        "label": "Balanced",
        "description": "Equal weight across all five categories",
        "weights": {"k": 0.20, "era": 0.20, "whip": 0.20, "qs": 0.20, "svh": 0.20},
    },
    "k_focused": {
        "label": "K-Focused",
        "description": "Heavy strikeouts and WHIP — chase the K category",
        "weights": {"k": 0.40, "era": 0.10, "whip": 0.25, "qs": 0.15, "svh": 0.10},
    },
    "era_whip": {
        "label": "ERA / WHIP",
        "description": "Ratio stats only — protect ERA and WHIP categories",
        "weights": {"k": 0.10, "era": 0.40, "whip": 0.40, "qs": 0.10, "svh": 0.00},
    },
    "closer": {
        "label": "Closer",
        "description": "Heavy SV+H — stream closers and high-leverage relievers",
        "weights": {"k": 0.15, "era": 0.15, "whip": 0.15, "qs": 0.05, "svh": 0.50},
    },
}


def get_rankings(db: Session, profile: str = "balanced") -> dict:
    """
    Return ranked pitcher list for the current week with the given profile.
    """
    if profile not in PROFILES:
        profile = "balanced"

    start, end = _current_week_range()
    pitchers_data = _collect_pitchers(db, start, end)

    if not pitchers_data:
        return {
            "profile": profile,
            "profiles": _profile_list(),
            "pitchers": [],
        }

    # Fetch stats — pybaseball returns by name, team batting by team ID
    player_names = [p["name"] for p in pitchers_data if p["name"] and p["name"] != "Unknown"]
    team_ids = list({p["opp_team_id"] for p in pitchers_data if p["opp_team_id"]})

    pitcher_stats = get_pitcher_stats(player_names) if player_names else {}
    team_stats = get_team_batting_stats(team_ids) if team_ids else {}

    # Attach stats to each pitcher entry
    for p in pitchers_data:
        stats = pitcher_stats.get(p["name"], {})
        p["era"]             = stats.get("era")
        p["whip"]            = stats.get("whip")
        p["strikeouts"]      = stats.get("strikeouts")
        p["innings_pitched"] = stats.get("innings_pitched")
        p["quality_starts"]  = stats.get("quality_starts")
        p["saves"]           = stats.get("saves")
        p["holds"]           = stats.get("holds")
        p["svh"]             = stats.get("svh")
        p["games_started"]   = stats.get("games_started")
        p["k_per_9"]         = stats.get("k_per_9")   # FanGraphs provides this directly
        p["xfip"]            = stats.get("xfip")
        p["siera"]           = stats.get("siera")

        # Opponent batting stats
        opp_id = p["opp_team_id"]
        opp = team_stats.get(opp_id, {})
        p["opp_avg"] = opp.get("avg")
        p["opp_ops"] = opp.get("ops")
        p["opp_k_rate"] = opp.get("strikeout_rate")

    # Normalise, score, rank
    _attach_scores(pitchers_data, profile)

    pitchers_data.sort(key=lambda x: x["score"], reverse=True)
    for i, p in enumerate(pitchers_data):
        p["rank"] = i + 1

    return {
        "profile": profile,
        "profiles": _profile_list(),
        "pitchers": pitchers_data,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _collect_pitchers(db: Session, start: date, end: date) -> list[dict]:
    """
    Pull all probable pitchers for the week from the DB.
    Returns one entry per pitcher (starter or reliever),
    with the opposing team info attached.
    """
    games = (
        db.query(Game)
        .filter(Game.game_date >= start, Game.game_date <= end)
        .order_by(Game.game_date)
        .all()
    )

    entries = []
    for game in games:
        for pitcher in game.pitchers:
            if not pitcher.player_id:
                continue  # skip TBDs
            opp_abbrev = game.home_team_abbrev if pitcher.side == "away" else game.away_team_abbrev
            opp_team = game.home_team if pitcher.side == "away" else game.away_team
            own_team = game.away_team if pitcher.side == "away" else game.home_team
            own_abbrev = game.away_team_abbrev if pitcher.side == "away" else game.home_team_abbrev

            entries.append({
                "player_id": pitcher.player_id,
                "name": pitcher.full_name or "Unknown",
                "team": own_team,
                "team_abbrev": own_abbrev,
                "opp_team": opp_team,
                "opp_team_abbrev": opp_abbrev,
                "opp_team_id": _abbrev_to_team_id(opp_abbrev),
                "game_date": str(game.game_date),
                "game_time": game.game_time,
                "side": pitcher.side,
            })
    return entries


def _attach_scores(pitchers: list[dict], profile: str) -> None:
    """
    Normalise stats across all pitchers, compute difficulty, apply profile
    weights, and attach `score` and `difficulty` to each pitcher dict in place.
    """
    weights = PROFILES[profile]["weights"]

    # Extract per-stat lists for normalisation (skip None)
    def vals(key):
        return [p[key] for p in pitchers if p.get(key) is not None]

    era_vals = vals("era")
    whip_vals = vals("whip")
    k9_vals = vals("k_per_9")
    qs_vals = vals("quality_starts")
    svh_vals = vals("svh")
    opp_avg_vals = vals("opp_avg")
    opp_ops_vals = vals("opp_ops")
    opp_k_vals = vals("opp_k_rate")

    for p in pitchers:
        # Normalise each stat to 0–1
        # ERA/WHIP: lower is better → invert
        era_n = _norm_inverted(p.get("era"), era_vals)
        whip_n = _norm_inverted(p.get("whip"), whip_vals)
        # K/9, QS, SV+H: higher is better
        k_n = _norm(p.get("k_per_9"), k9_vals)
        qs_n = _norm(p.get("quality_starts"), qs_vals)
        svh_n = _norm(p.get("svh"), svh_vals)

        # Weighted pitcher score (0–100)
        raw_score = (
            weights["k"] * k_n
            + weights["era"] * era_n
            + weights["whip"] * whip_n
            + weights["qs"] * qs_n
            + weights["svh"] * svh_n
        ) * 100

        # Opponent difficulty score: 1–10 (higher = tougher)
        difficulty = _compute_difficulty(
            p.get("opp_avg"), p.get("opp_ops"), p.get("opp_k_rate"),
            opp_avg_vals, opp_ops_vals, opp_k_vals,
        )
        p["difficulty"] = difficulty

        # Difficulty modifier: 0.7 (hardest) → 1.0 (easiest)
        # Scale: difficulty 1 → modifier 1.0, difficulty 10 → modifier 0.7
        modifier = 1.0 - ((difficulty - 1) / 9) * 0.30
        p["score"] = round(raw_score * modifier, 1)


def _norm(val, all_vals: list) -> float:
    """Normalise val to 0–1 where higher is better."""
    if val is None or not all_vals:
        return 0.5  # neutral when no data
    mn, mx = min(all_vals), max(all_vals)
    if mx == mn:
        return 0.5
    return (val - mn) / (mx - mn)


def _norm_inverted(val, all_vals: list) -> float:
    """Normalise val to 0–1 where lower is better (ERA, WHIP)."""
    if val is None or not all_vals:
        return 0.5
    mn, mx = min(all_vals), max(all_vals)
    if mx == mn:
        return 0.5
    return (mx - val) / (mx - mn)


def _compute_difficulty(
    avg, ops, k_rate,
    avg_vals, ops_vals, k_vals,
) -> float:
    """
    Compute a 1–10 opponent difficulty score.
    High BA/OPS = harder. High batter K% = easier (good for pitcher).
    """
    avg_n = _norm(avg, avg_vals)          # high avg → high score → harder
    ops_n = _norm(ops, ops_vals)          # high ops → high score → harder
    k_n = _norm(k_rate, k_vals)           # high K% → high score → easier for pitcher
    k_inverted = 1.0 - k_n               # invert: high K% → lower difficulty

    combined = (avg_n * 0.35) + (ops_n * 0.40) + (k_inverted * 0.25)
    return round(combined * 9 + 1, 1)    # scale to 1–10


def _profile_list() -> list[dict]:
    return [
        {"id": pid, "label": p["label"], "description": p["description"]}
        for pid, p in PROFILES.items()
    ]


def _current_week_range() -> tuple[date, date]:
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def _safe_add(a, b) -> int | None:
    if a is None and b is None:
        return None
    return (a or 0) + (b or 0)


# ── Team ID lookup ─────────────────────────────────────────────────────────────
# Maps team abbreviations to MLB team IDs for the Stats API.
_ABBREV_TO_ID = {
    "ARI": 109, "ATL": 144, "BAL": 110, "BOS": 111, "CHC": 112,
    "CWS": 145, "CIN": 113, "CLE": 114, "COL": 115, "DET": 116,
    "HOU": 117, "KC":  118, "LAA": 108, "LAD": 119, "MIA": 146,
    "MIL": 158, "MIN": 142, "NYM": 121, "NYY": 147, "OAK": 133,
    "PHI": 143, "PIT": 134, "SD":  135, "SEA": 136, "SF":  137,
    "STL": 138, "TB":  139, "TEX": 140, "TOR": 141, "WSH": 120,
}


def _abbrev_to_team_id(abbrev: str | None) -> int | None:
    if not abbrev:
        return None
    return _ABBREV_TO_ID.get(abbrev.upper())
