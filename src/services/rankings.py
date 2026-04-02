"""
Rankings service for Phase 2.5 — Pitcher Rankings Page.

Flow:
  1. Pull probable pitchers for the current week from DB
  2. Fetch season stats for each pitcher via pybaseball (FanGraphs)
  3. Fetch team batting stats for each opposing team via mlb-statsapi
  4. Normalise stats using z-scores (more robust to outliers than min-max)
  5. Apply preset profile weights — K weight uses K%-BB% for cleaner signal
  6. Compute opponent difficulty modifier (0.7–1.0 range)
  7. Return sorted ranked list
"""

import logging
import math
from datetime import date, timedelta

from sqlalchemy.orm import Session

from mlb.stats import get_pitcher_stats, get_team_batting_stats
from models import Game, Pitcher

logger = logging.getLogger(__name__)

# ── Preset profiles ───────────────────────────────────────────────────────────
# Weights must sum to 1.0. K weight scores on K%-BB%, not K/9.
# ERA/WHIP are inverted stats (lower is better) — handled in normalisation.

PROFILES = {
    "balanced": {
        "label": "Balanced",
        "description": "Equal weight across all five categories",
        "weights": {"k": 0.20, "era": 0.20, "whip": 0.20, "qs": 0.20, "svh": 0.20},
    },
    "k_focused": {
        "label": "K-Focused",
        "description": "Heavy K%-BB% and WHIP — chase the strikeout category",
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


def get_rankings(
    db: Session, profile: str = "balanced", week_start: date = None
) -> dict:
    if profile not in PROFILES:
        profile = "balanced"

    if week_start:
        start = week_start
        end = week_start + timedelta(days=6)
    else:
        start, end = _current_week_range()

    pitchers_data = _collect_pitchers(db, start, end)

    # if not pitchers_data:
    #     return {"profile": profile, "profiles": _profile_list(), "pitchers": []}

    # Fetch stats — pybaseball by name, team batting by team ID
    player_names = [
        p["name"] for p in pitchers_data if p["name"] and p["name"] != "Unknown"
    ]
    team_ids = list({p["opp_team_id"] for p in pitchers_data if p["opp_team_id"]})

    pitcher_stats = get_pitcher_stats(player_names) if player_names else {}
    team_stats = get_team_batting_stats(team_ids) if team_ids else {}

    for p in pitchers_data:
        stats = pitcher_stats.get(p["name"], {})
        k_pct = stats.get("k_pct")
        bb_pct = stats.get("bb_pct")

        p["era"] = stats.get("era")
        p["whip"] = stats.get("whip")
        p["strikeouts"] = stats.get("strikeouts")
        p["innings_pitched"] = stats.get("innings_pitched")
        p["quality_starts"] = stats.get("quality_starts")
        p["saves"] = stats.get("saves")
        p["holds"] = stats.get("holds")
        p["svh"] = stats.get("svh")
        p["games_started"] = stats.get("games_started")
        p["k_per_9"] = stats.get("k_per_9")  # display only
        p["k_pct"] = k_pct  # display only
        p["bb_pct"] = bb_pct  # display only
        p["xfip"] = stats.get("xfip")
        p["siera"] = stats.get("siera")
        # K%-BB%: the scoring stat for the K category
        p["k_minus_bb"] = (
            round(k_pct - bb_pct, 4)
            if (k_pct is not None and bb_pct is not None)
            else None
        )

        opp = team_stats.get(p["opp_team_id"], {})
        p["opp_avg"] = opp.get("avg")
        p["opp_ops"] = opp.get("ops")
        p["opp_k_rate"] = opp.get("strikeout_rate")

    _attach_scores(pitchers_data, profile)

    pitchers_data.sort(key=lambda x: x["score"], reverse=True)
    for i, p in enumerate(pitchers_data):
        p["rank"] = i + 1

    return {"profile": profile, "profiles": _profile_list(), "pitchers": pitchers_data}


# ── Helpers ───────────────────────────────────────────────────────────────────


def _collect_pitchers(db: Session, start: date, end: date) -> list[dict]:
    games = (
        db.query(Game)
        .filter(Game.game_date >= start, Game.game_date <= end)
        .order_by(Game.game_date)
        .all()
    )

    entries = []
    for game in games:
        for pitcher in game.pitchers:
            if not pitcher.full_name:
                continue  # skip TBDs — match on name, not player_id
            opp_abbrev = (
                game.home_team_abbrev
                if pitcher.side == "away"
                else game.away_team_abbrev
            )
            opp_team = game.home_team if pitcher.side == "away" else game.away_team
            own_team = game.away_team if pitcher.side == "away" else game.home_team
            own_abbrev = (
                game.away_team_abbrev
                if pitcher.side == "away"
                else game.home_team_abbrev
            )

            entries.append(
                {
                    "player_id": pitcher.player_id,
                    "name": pitcher.full_name,
                    "team": own_team,
                    "team_abbrev": own_abbrev,
                    "opp_team": opp_team,
                    "opp_team_abbrev": opp_abbrev,
                    "opp_team_id": _abbrev_to_team_id(opp_abbrev),
                    "game_date": str(game.game_date),
                    "game_time": game.game_time,
                    "side": pitcher.side,
                }
            )
    return entries


def _attach_scores(pitchers: list[dict], profile: str) -> None:
    weights = PROFILES[profile]["weights"]

    def vals(key):
        return [p[key] for p in pitchers if p.get(key) is not None]

    # Build z-score normalised values for each scoring stat
    # K weight uses k_minus_bb (K%-BB%), not k_per_9
    for p in pitchers:
        era_z = _zscore_inv(p.get("era"), vals("era"))
        whip_z = _zscore_inv(p.get("whip"), vals("whip"))
        k_z = _zscore(p.get("k_minus_bb"), vals("k_minus_bb"))
        qs_z = _zscore(p.get("quality_starts"), vals("quality_starts"))
        svh_z = _zscore(p.get("svh"), vals("svh"))

        raw_score = (
            weights["k"] * k_z
            + weights["era"] * era_z
            + weights["whip"] * whip_z
            + weights["qs"] * qs_z
            + weights["svh"] * svh_z
        ) * 100

        difficulty = _compute_difficulty(
            p.get("opp_avg"),
            p.get("opp_ops"),
            p.get("opp_k_rate"),
            vals("opp_avg"),
            vals("opp_ops"),
            vals("opp_k_rate"),
        )
        p["difficulty"] = difficulty

        modifier = 1.0 - ((difficulty - 1) / 9) * 0.30
        p["score"] = round(raw_score * modifier, 1)


def _zscore(val, all_vals: list) -> float:
    """
    Z-score normalised to 0–1. Higher is better.
    Clips to [-3, 3] standard deviations before scaling.
    Falls back to 0.5 (neutral) when data is missing or flat.
    """
    if val is None or len(all_vals) < 2:
        return 0.5
    mean = sum(all_vals) / len(all_vals)
    variance = sum((x - mean) ** 2 for x in all_vals) / len(all_vals)
    std = math.sqrt(variance)
    if std == 0:
        return 0.5
    z = (val - mean) / std
    z = max(-3.0, min(3.0, z))  # clip outliers
    return (z + 3.0) / 6.0  # scale [-3,3] → [0,1]


def _zscore_inv(val, all_vals: list) -> float:
    """Z-score normalised to 0–1. Lower is better (ERA, WHIP)."""
    return 1.0 - _zscore(val, all_vals)


def _compute_difficulty(avg, ops, k_rate, avg_vals, ops_vals, k_vals) -> float:
    """
    Opponent difficulty score 1–10. High BA/OPS = harder. High batter K% = easier.
    Uses min-max here intentionally — difficulty is a display metric not a scoring
    input, and min-max gives an intuitive spread across the 1–10 range.
    """
    avg_n = _minmax(avg, avg_vals)
    ops_n = _minmax(ops, ops_vals)
    k_inverted = 1.0 - _minmax(k_rate, k_vals)
    combined = (avg_n * 0.35) + (ops_n * 0.40) + (k_inverted * 0.25)
    return round(combined * 9 + 1, 1)


def _minmax(val, all_vals: list) -> float:
    if val is None or not all_vals:
        return 0.5
    mn, mx = min(all_vals), max(all_vals)
    if mx == mn:
        return 0.5
    return (val - mn) / (mx - mn)


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


# ── Team ID lookup ────────────────────────────────────────────────────────────
_ABBREV_TO_ID = {
    "ARI": 109,
    "ATL": 144,
    "BAL": 110,
    "BOS": 111,
    "CHC": 112,
    "CWS": 145,
    "CIN": 113,
    "CLE": 114,
    "COL": 115,
    "DET": 116,
    "HOU": 117,
    "KC": 118,
    "LAA": 108,
    "LAD": 119,
    "MIA": 146,
    "MIL": 158,
    "MIN": 142,
    "NYM": 121,
    "NYY": 147,
    "OAK": 133,
    "PHI": 143,
    "PIT": 134,
    "SD": 135,
    "SEA": 136,
    "SF": 137,
    "STL": 138,
    "TB": 139,
    "TEX": 140,
    "TOR": 141,
    "WSH": 120,
}


def _abbrev_to_team_id(abbrev: str | None) -> int | None:
    if not abbrev:
        return None
    return _ABBREV_TO_ID.get(abbrev.upper())
