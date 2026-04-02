**Fantasy Baseball Probable Pitchers App**

Project Planning & Architecture Document

March 2026 \| Version 1.0

**Status:** Pre-implementation planning

**Target:** Open-source release (post-internal validation)

**Language:** Python

1\. Project Overview

This document captures all planning decisions made for a Python-based
web application that surfaces probable starting pitchers for the
upcoming fantasy baseball week. The app is designed to be built
incrementally across three phases, starting with a clean MVP and
expanding toward full fantasy decision support.

The project will be developed privately first, then released as an
open-source project once the core functionality is stable and
well-tested. All technical decisions have been made with this OSS
trajectory in mind --- favouring widely understood tools, clean
abstractions, and a database layer that can scale.

2\. Goals & Scope

2.1 Primary goal

Display the full week\'s probable starting pitchers across all MLB
matchups, pulled from official team announcements via free APIs, with no
manual data entry required.

2.2 Future feature goals

- Platoon advantage analysis --- cross-reference pitcher handedness with
  batter splits to surface favourable matchups

- Add/drop recommendations --- identify streamable pitchers and hot
  waiver wire targets based on upcoming schedules

- Fantasy platform integration --- connect to a user\'s Yahoo or ESPN
  Fantasy league to personalise recommendations against their actual
  roster

2.3 Out of scope (initial release)

- Projections or predictive modelling (this uses real announced starters
  only)

- Mobile app --- web application only

- Multi-sport support

3\. Architecture Overview

The application follows a standard three-layer architecture: external
data sources feed a Python backend, which stores processed data in a
local database and exposes a REST API, consumed by a React frontend.

3.1 Data sources

  -----------------------------------------------------------------------
  **Source**            **Purpose**
  --------------------- -------------------------------------------------
  **MLB Stats API**     Schedule, probable pitchers, player handedness,
                        splits --- free, no API key required

  **mlb-statsapi        Python wrapper for the MLB Stats API, handles
  (Python library)**    date-range schedule queries and team batting
                        stats. Not used for pitcher season stats (see
                        pybaseball below).

  **Yahoo Fantasy       Roster data, league player pool, waiver wire,
  Sports API**          add/drop history --- requires free OAuth app
                        registration

  **ESPN Fantasy API    Alternative to Yahoo --- no key required but
  (unofficial)**        undocumented; lower reliability
  -----------------------------------------------------------------------

3.2 Data freshness

The MLB API returns real pitcher announcements --- not
computer-generated predictions. Teams typically confirm starting
pitchers 24--48 hours before game time, meaning early-week queries will
show many TBD entries that fill in mid-week. The application must
refresh daily to capture new announcements.

  -----------------------------------------------------------------------
  **Note:** The fantasy baseball scoring week typically runs
  Monday--Sunday. The app should align its weekly view to the active
  scoring period rather than a rolling 7-day window.

  -----------------------------------------------------------------------

4\. Recommended Technology Stack

Each layer of the stack was evaluated across multiple options. The
recommendations below optimise for development speed, community support,
OSS-friendliness, and the ability to scale to a hosted multi-user
deployment later.

4.1 Backend framework

  -----------------------------------------------------------------------
  **Option**            **Assessment**
  --------------------- -------------------------------------------------
  **FastAPI ✓           Async-first, automatic Swagger docs at /docs,
  Recommended**         built-in request validation via Pydantic. Ideal
                        for serving a REST API consumed by a React
                        frontend.

  **Flask**             Simpler and more familiar --- perfectly viable,
                        especially for Phase 1. Lacks built-in async and
                        data validation.

  **Django**            Overkill for this project. Brings a full ORM,
                        admin panel, and auth system that this app
                        doesn\'t need.
  -----------------------------------------------------------------------

4.2 Frontend

  -----------------------------------------------------------------------
  **Option**            **Assessment**
  --------------------- -------------------------------------------------
  **React + Vite ✓      Best fit for an interactive weekly calendar view
  Recommended**         with filtering, status badges, and eventual
                        platoon colour-coding. Vite gives fast builds and
                        HMR.

  **Jinja2 + HTMX**     Simpler to start, server-side rendered. Becomes
                        awkward once interactivity requirements grow
                        (filtering, live updates).

  **Streamlit**         Very fast to prototype but not suitable for a
                        polished, shippable UI. Limited layout control.

  **Dash (Plotly)**     Good for data dashboards but opinionated layout
                        system makes custom UI work harder.
  -----------------------------------------------------------------------

4.3 Database

The database choice was made with two requirements in mind:
zero-friction local development, and a clear upgrade path to a hosted
deployment when the project goes OSS.

  -----------------------------------------------------------------------
  **Option**            **Assessment**
  --------------------- -------------------------------------------------
  **SQLite ✓            Zero setup, single file, ships with Python.
  Recommended           Sufficient for a single user\'s league data and
  (dev/MVP)**           daily cached pitcher data. Ideal for local
                        development and initial OSS contributors.

  **PostgreSQL ✓        The natural upgrade path when the app is deployed
  Recommended           for multiple users or leagues. Full SQL
  (production/OSS)**    compatibility with SQLite means minimal code
                        changes.

  **JSON flat files**   Acceptable for Phase 1 only --- no querying
                        capability, will become a maintenance burden as
                        data volume grows.
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------
  **OSS Consideration:** The database layer will be abstracted via
  SQLAlchemy from day one, using SQLite as the default for local
  development. A PostgreSQL connection string can be dropped in via
  environment variable for deployed instances, with no code changes
  required. The README will document both paths clearly for OSS
  contributors.

  -----------------------------------------------------------------------

4.4 ORM / data access

  -----------------------------------------------------------------------
  **Option**            **Assessment**
  --------------------- -------------------------------------------------
  **SQLAlchemy ✓        Industry-standard Python ORM. Abstracts the
  Recommended**         database engine entirely --- switching from
                        SQLite to PostgreSQL is a single config change.
                        Widely known by Python contributors.

  **Peewee**            Lighter and simpler than SQLAlchemy. Good for
                        very small projects but less familiar to the
                        wider Python community.

  **Raw SQL**           Acceptable for a small solo project but creates
                        tight coupling to the database engine, which
                        conflicts with the SQLite → PostgreSQL upgrade
                        path.
  -----------------------------------------------------------------------

4.5 Background scheduling

The app needs to refresh pitcher data daily, ideally without requiring a
separate process or infrastructure.

  -----------------------------------------------------------------------
  **Option**            **Assessment**
  --------------------- -------------------------------------------------
  **APScheduler ✓       Runs inside the FastAPI process. No Redis, no
  Recommended**         separate worker. Define a job function and
                        schedule it to run at a set time each day. Ideal
                        for a single-instance deployment.

  **Celery + Redis**    The right tool for distributed task queues at
                        scale. Significant infrastructure overhead for a
                        daily data refresh task.

  **OS cron**           Simple and reliable. Requires the server OS to
                        manage the schedule, which is less portable for
                        OSS contributors running on different platforms.
  -----------------------------------------------------------------------

4.6 OAuth / authentication (Yahoo API)

Accessing a user\'s Yahoo Fantasy league requires OAuth 2.0. The access
tokens expire and must be refreshed.

  -------------------------------------------------------------------------
  **Option**              **Assessment**
  ----------------------- -------------------------------------------------
  **yahoo-fantasy-api     The yahoo-fantasy-api Python library handles the
  (built-in) ✓            OAuth token flow internally. Try this first
  Recommended**           before adding a separate auth library.

  **Authlib**             Full-featured OAuth library for FastAPI. Use if
                          yahoo-fantasy-api\'s token handling proves
                          insufficient.

  **requests-oauthlib**   Lightweight OAuth wrapper for the requests
                          library. Lower-level than Authlib.
  -------------------------------------------------------------------------

4.7 Full recommended stack summary

  -----------------------------------------------------------------------
  **Layer**             **Choice**
  --------------------- -------------------------------------------------
  **Backend framework** FastAPI

  **Frontend**          React + Vite

  **Database            SQLite
  (local/dev)**         

  **Database            PostgreSQL
  (production/OSS)**    

  **ORM**               SQLAlchemy

  **Scheduler**         APScheduler

  **OAuth**             yahoo-fantasy-api (built-in)

  **MLB data library**  mlb-statsapi

  **Fantasy data        yahoo-fantasy-api
  library**             
  -----------------------------------------------------------------------

5\. Phased Delivery Plan

The project is split into three phases. Each phase delivers a
standalone, usable increment. Phase 1 is the minimum viable product and
the starting point for development.

Phase 1 --- Probable pitchers view (MVP)

  -----------------------------------------------------------------------
  **Goal:** Show all MLB games for the current fantasy week with probable
  starters, updated daily.

  -----------------------------------------------------------------------

**Data flow:**

1.  APScheduler triggers a daily refresh job at a configured time

2.  mlb-statsapi fetches the week\'s schedule with probable pitcher
    fields

3.  Results are written to SQLite via SQLAlchemy

4.  FastAPI exposes a /api/week endpoint returning matchups as JSON

5.  React frontend renders a calendar-style weekly view grouped by date

Key API endpoint:

GET /api/week → { date, away_team, home_team, away_pitcher, home_pitcher
}

Phase 2 --- Platoon advantage analysis (deferred --- lower priority than
Phase 2.5)

  -----------------------------------------------------------------------
  **Goal:** Surface which batters on a user\'s roster have a handedness
  advantage against that day\'s probable pitcher.

  -----------------------------------------------------------------------

- Pull pitcher handedness from the MLB Stats API player endpoint

- Pull batter vs. LHP / vs. RHP split stats from the MLB Stats API stats
  endpoint

- Compute a platoon advantage score and surface favourable matchups in
  the UI

- Add colour-coded indicators to the weekly view (e.g. green highlight =
  strong platoon advantage)

Phase 3 --- Add/drop recommendations & fantasy integration

  -----------------------------------------------------------------------
  **Goal:** Connect to the user's Yahoo Fantasy league to personalise
  recommendations against their actual roster.

  -----------------------------------------------------------------------

- Implement Yahoo Fantasy OAuth flow via the yahoo-fantasy-api library

- Fetch the user's current roster and the full league player pool
  (owned, waivers, free agents)

- Build an add/drop scoring model: combine upcoming schedule, platoon
  advantage, and injury status

- Surface the top add/drop recommendations ranked by projected value for
  the current week

**Weekly Category Gap Analysis & Streaming Recommendations**

A key addition that runs throughout the week to help managers catch up in
categories they're lacking.

- **Category gap detection** --- Compare the user's current standings to
  the league median in each head-to-head category. Identify which
  categories are at risk of losing (below median) or could be gained
  (above median but not locked).

- **Streaming recommendations** --- Based on identified gaps, surface
  available pitchers (waiver wire / free agents) who have upcoming starts
  in the remaining days of the week. Rank by projected category contribution
  (e.g., high K for strikeout-deficient teams, QS for win-deficient teams).

- **Gap severity scoring** --- Rank detected gaps by severity: critical
  (likely to lose), vulnerable (close to median), secure (safe lead). This
  helps managers prioritize which categories to target.

- **In-season adjustment** --- As the week progresses, re-evaluate gaps
  daily. If a gap is already lost, pivot to protecting other categories
  rather than chasing the impossible.

- **Opponent-aware suggestions** --- Factor in not just the pitcher's
  schedule but the quality of opponent they face. A streamer facing a
  weak-hitting team is more valuable than one facing a top offense.

New Backend Components (Weekly Category Gap)

**services/category_gap.py** --- Compares user's roster stats to league
median, computes gap severity, and returns ranked list of weak categories.

**services/streaming.py** --- Finds available pitchers with remaining starts
this week, fetches their upcoming opponent difficulty, and scores them
against the user's category needs. Returns streaming candidates ranked by
category value.

**routes/league.py** --- Extended with GET /api/league/category-gaps and GET
/api/league/streaming-targets. Requires Yahoo OAuth (Phase 3).

New Frontend Components (Weekly Category Gap)

**components/CategoryGaps.jsx** --- Dashboard showing current category
gaps with severity indicators (critical/vulnerable/secure). Updates daily.

**components/StreamingSuggestions.jsx** --- List of recommended streamers
based on identified gaps. Shows pitcher, next start date, opponent
difficulty, and projected category impact.

The Category Gaps and Streaming Suggestions can be displayed on the main
dashboard or within a dedicated "Gap Recovery" section of the app.

Scheduled Transactions

A key addition to the Yahoo Fantasy integration is the ability to plan
and schedule add/drop transactions ahead of time. Rather than executing
moves immediately, the user can queue a transaction for a specific
future date and time --- for example, scheduling a waiver pickup to
execute on Wednesday morning before a pitcher's Thursday start.

Scheduled Transactions --- Feature Scope

- **Queue transactions** --- User selects a player to add and a player
  to drop, picks an execution date and time, and saves the transaction
  to a local queue

- **Scheduled execution** --- APScheduler checks the queue and fires
  pending transactions at the specified time via the Yahoo Fantasy API

- **Transaction queue UI** --- A dedicated panel shows all pending,
  executed, and failed transactions with the ability to cancel or
  reschedule pending ones

- **Integration with rankings** --- The Rankings page surfaces a
  "Schedule Add" button next to each pitcher, pre-filling the
  transaction form with the player and a suggested execution time based
  on their next start

- **Status tracking** --- Each transaction is stored in the DB with a
  status field: pending, executed, failed, or cancelled. Failed
  transactions surface an error reason so the user can retry

New Backend Components (Scheduled Transactions)

**models.py** --- New ScheduledTransaction model with fields: id,
add_player_id, add_player_name, drop_player_id, drop_player_name,
execute_at (datetime), status, error_message, created_at.

**services/transactions.py** --- Business logic for creating,
cancelling, and executing transactions. Calls the Yahoo Fantasy API to
perform the actual add/drop.

**routes/transactions.py** --- REST endpoints: POST /api/transactions,
GET /api/transactions, DELETE /api/transactions/{id}.

**scheduler.py** --- Extended to poll the ScheduledTransaction table
every few minutes and execute any pending transactions whose execute_at
time has passed.

New Frontend Components (Scheduled Transactions)

**pages/Transactions.jsx** --- Transaction queue panel showing pending,
executed, and failed transactions. Supports cancellation of pending
items.

**components/ScheduleTransactionModal.jsx** --- Modal form to schedule a
new add/drop. Fields: player to add (search), player to drop (from
current roster), execution date and time.

A "Schedule Add" button is added to each row in the Rankings table,
opening the modal pre-filled with that pitcher's details and a suggested
execution time one hour before their next start.

**Goal:** Rank all probable pitchers for the current week by projected
fantasy value, factoring in their season stats and the offensive
strength of the team they face. Designed for head-to-head categories
leagues.

Scoring Stats

The ranking model uses five standard head-to-head categories: Strikeouts
(K), Earned Run Average (ERA), WHIP (Walks + Hits per Inning Pitched),
Quality Starts (QS), and Saves + Holds (SV+H).

Opposing Team Difficulty

Each pitcher's projected score is adjusted by the offensive strength of
the team they face. Opponent data is pulled from the MLB Stats API
(season team batting stats) and displayed in three columns:

**BA / OPS** --- Team batting average and on-base plus slugging. Higher
values indicate a tougher lineup.

**Opp K%** --- Opposing team's strikeout rate as batters. A high K%
means the lineup strikes out often, which is favourable for pitcher
strikeout projections.

**Difficulty Score** --- A composite 1--10 score combining BA, OPS, and
batter K% into a single matchup difficulty rating. Higher = tougher
opponent.

Preset Scoring Profiles

Users select a profile at the top of the rankings page to weight stats
according to their roster needs:

**Balanced** --- Equal weight across all five categories. Good default
for most managers.

**K-Focused** --- Heavy weight on strikeouts and WHIP. For managers
targeting the K category.

**ERA / WHIP** --- Ratio stats only. Best for managers whose counting
stats are already strong.

**Closer** --- Heavy SV+H weight. For streaming relievers and
save-hunting strategies.

New Backend Components

**mlb/stats.py** --- Fetches pitcher season stats via pybaseball
(FanGraphs leaderboard data --- ERA, WHIP, K/9, QS, SV+H, xFIP, SIERA,
K%). Team batting stats fetched from mlb-statsapi. One bulk leaderboard
call per session, cached in-process. Future enhancement:
baseball-scraper could pull Steamer/ZiPS projections, but introduces a
Selenium/Chrome dependency that raises the barrier for OSS contributors
--- treat as optional.

**services/rankings.py** --- Scoring and weighting logic. Normalises
stats, applies profile weights, computes opponent difficulty modifier,
and returns a ranked list.

**routes/rankings.py** --- Exposes GET /api/rankings?profile=balanced.
Returns ranked pitcher list with stats and opponent difficulty data.

New Frontend Components

**pages/Rankings.jsx** --- Sortable table with one row per probable
pitcher. Columns: Pitcher, Team, Opp, Date, ERA, WHIP, K/9, BA/OPS, Opp
K%, Difficulty, Score.

**hooks/useRankings.js** --- Fetches rankings data, manages selected
profile state, and handles sorting.

A tab or nav bar is added to the app to switch between the Week View and
the Rankings page.

Phase 4 --- Advanced Analytics & Breakout Detection

**Goal:** Surface breakout candidates for both batters and pitchers
using advanced Statcast metrics, projection models, and machine
learning. Give fantasy managers an edge by identifying players trending
up before the rest of the market catches on.

Data Sources

All data is pulled via pybaseball (already a project dependency). No
additional libraries are required for data acquisition.

**Pitching metrics (FanGraphs)** --- ERA, WHIP, FIP, xFIP, SIERA, K%,
BB%, K−BB%, SwStr%, CSW%, GB%. ERA− and FIP− (park- and league-adjusted)
are particularly useful for identifying pitchers outperforming or
underperforming their peripherals.

**Batting metrics (FanGraphs)** --- wOBA, wRC+, ISO, BABIP, BB%, K%,
Hard Hit%, Barrel%, Sprint Speed. Age and playing time context are
applied to all batter projections.

**Statcast data** --- Exit velocity, launch angle, Barrel%, xBA
(expected batting average), xSLG, xwOBA, HardHit% (balls hit over 95
mph). Statcast metrics are quality-of-contact signals that are more
predictive of future performance than traditional counting stats and are
less subject to BABIP noise.

Projection Model

The projection pipeline runs in two stages: a MARCEL baseline followed
by an optional machine learning layer.

**Stage 1 --- MARCEL baseline** --- MARCEL is the minimum-competency
standard for baseball projections. It is simple, transparent, and
well-understood by the analytics community --- ideal for an OSS project.
The model applies three transformations: (1) a weighted average of the
last three seasons with a 5/4/3 recency weighting so recent performance
counts most; (2) regression to the mean, which tempers extreme
performances by pulling projections toward league average; and (3) an
age adjustment that adds a boost for young players still in their
development arc and a penalty for players past their peak.

**Stage 2 --- Machine learning layer (optional enhancement)** --- Once
the MARCEL baseline is validated, a gradient-boosted model (XGBoost or
LightGBM) can be trained on historical player seasons to improve
projection accuracy. The model ingests the 300+ FanGraphs features and
identifies which metrics are the strongest predictors of year-over-year
improvement. Feature importance scores will be surfaced in the UI so
managers can see why a player is flagged.

Breakout Detection

A player is flagged as a breakout candidate when their projected stats
represent a meaningful improvement over their rolling 3-year average.
The threshold is configurable, defaulting to a 15% improvement in the
primary projection metric (ERA− or FIP− for pitchers; wRC+ or xwOBA for
batters).

**Pitching breakout signals** --- Rising K%, falling BB%, improved
SwStr% or CSW%, FIP or xFIP significantly below ERA (ERA regression
candidate), new pitch added or velocity gain in Statcast data.

**Batting breakout signals** --- Rising Barrel% or HardHit%, xBA or
xwOBA outpacing actual BA (positive regression candidate), improved
launch angle, reduced K%, age 24--27 development window, sprint speed
retention indicating no physical decline.

New Backend Components

**mlb/statcast.py** --- Fetches Statcast batter and pitcher data via
pybaseball.statcast_batter_exitvelo_barrels() and related endpoints.
Cached in-process alongside the FanGraphs leaderboard.

**services/projections.py** --- MARCEL projection engine for both
pitchers and batters. Weighted averages, regression to mean, age
adjustments. Returns projected stat lines per player.

**services/breakouts.py** --- Compares projections to rolling 3-year
averages, applies breakout signal rules, and returns ranked breakout
candidate lists for pitchers and batters separately.

**routes/analytics.py** --- Exposes GET
/api/analytics/breakouts?type=pitching and GET
/api/analytics/breakouts?type=batting. Returns ranked breakout
candidates with projected stats, Statcast signals, and confidence score.

New Frontend Components

**pages/Analytics.jsx** --- Two-tab page (Pitching / Batting) showing
ranked breakout candidates. Each row displays the player's projected
stat line, key Statcast signals, 3-year trend, and a breakout confidence
score. Sortable by any column.

**components/BreakoutBadge.jsx** --- Colour-coded badge (High / Medium /
Low) indicating breakout confidence. Green = strong signal across
multiple metrics, yellow = partial signal, grey = speculative.

**components/StatTrend.jsx** --- Sparkline showing a player's key metric
over the last 3 seasons alongside their projection, giving visual
context for the breakout signal.

Additional Dependencies

**pybaseball** --- Already a project dependency. Statcast endpoints are
included.

**pandas / numpy** --- Required for MARCEL weighted average calculations
and feature engineering. Both are transitive dependencies of pybaseball.

**scikit-learn or XGBoost** --- Optional, for Stage 2 machine learning
layer only. Not required for the MARCEL baseline. Add to pyproject.toml
as an optional dependency group.

Phase 5 --- League Power Rankings & Trade Targets

**Goal:** Analyze every team in the user's Yahoo Fantasy league to determine
their strengths and weaknesses, and use this analysis to identify the best
trade targets. Rank every team by projected rest-of-season performance,
identify which categories each team is strong or weak in, and surface
actionable trade targets so the user can exploit mismatches before the trade
deadline.

Team Analysis & Strengths/Weaknesses Mapping

- **Full league scan** --- Pull all teams in the league and compute their
  current standings across all head-to-head categories (standard 5x5: R, HR,
  RBI, SB, AVG for batting; W, K, ERA, WHIP, SV+H for pitching).

- **Category grades per team** --- Assign each team a grade (1-10) for each
  category based on where they rank relative to the rest of the league.
  This creates a "strengths/weaknesses map" for every team.

- **Visual team profile** --- Each team's profile shows at a glance what
  categories they excel in (strengths) and where they struggle (weaknesses).
  This makes it easy to identify which teams might be looking to trade away
  players in their strong categories to address weaknesses.

- **Trade target identification** --- Cross-reference the user's category
  profile against every other team's profile. Identify teams where the user
  has a surplus in what the other team needs, and the other team has a
  surplus in what the user needs. These are complementary mismatches that
  lead to win-win trades.

Power Rankings

Each team is scored across all head-to-head categories (standard 5x5: R,
HR, RBI, SB, AVG for batting; W, K, ERA, WHIP, SV+H for pitching) using
projected rest-of-season stats from the Phase 4 MARCEL model applied to
every rostered player. The score reflects not just current standings but
where each team is trending --- a team with strong underlying Statcast
metrics may be underperforming now but is projected to finish higher.

**Overall power score** --- A composite rank across all 10 categories,
weighted equally. Displayed as a leaderboard with trend arrows (up/down
vs. last week's projection).

**Category breakdown** --- Each team gets a per-category grade (1--10
relative to the rest of the league) so the user can see at a glance
where they are elite, average, or weak. A heat map view makes cross-team
category comparisons fast.

**Roster health** --- Flags teams carrying injured players with strong
projections (buy-low opportunity) and teams over-relying on players with
poor underlying metrics (sell-high opportunity).

Trade Target Identification

The trade engine compares the user's category profile against every
other team in the league and identifies complementary mismatches ---
categories the user needs that another team has in surplus, and vice
versa. This surfaces genuinely win-win trade structures rather than
generic "good player" suggestions.

**Buy-low targets** --- Players on other rosters whose actual stats are
lagging their projections (e.g. low BABIP, high LOB%, poor strand rate)
and are likely to improve. These players may be available cheaply
because their owner is reacting to results rather than process.

**Sell-high targets** --- Players on the user's own roster whose actual
stats are outpacing their underlying metrics (e.g. unsustainably high
BABIP, low HR/FB rate due for positive regression, ERA well below FIP).
These players have elevated trade value right now that may not last.

**Category swap suggestions** --- Given the user's weakest categories
and each opponent team's weakest categories, the engine proposes
specific trade packages: "Team X is weak in SB and strong in HR. You are
weak in HR and strong in SB. These two players could work."

**Trade value scores** --- Each rostered player across the league is
assigned a rest-of-season trade value score derived from their MARCEL
projection, age curve, and injury status. Values are recalculated
weekly.

New Backend Components

**services/power_rankings.py** --- Pulls all league rosters via the
Yahoo Fantasy API, applies MARCEL projections to each rostered player,
aggregates projected category totals per team, and computes a normalised
power score. Runs weekly and caches results.

**services/trade_engine.py** --- Compares the user's category profile
against all opponents, identifies buy-low and sell-high candidates using
the gap between projected and actual stats, and generates ranked trade
package suggestions.

**routes/league.py** --- Exposes GET /api/league/power-rankings, GET
/api/league/trade-targets, and GET /api/league/trade-value. Requires
Yahoo OAuth (Phase 3).

New Frontend Components

**pages/League.jsx** --- Three-tab page: Power Rankings, Trade Targets,
and Trade Values. Power Rankings tab shows the leaderboard with trend
arrows and per-category heat map. Trade Targets tab shows buy-low and
sell-high candidates with suggested trade packages. Trade Values tab
shows every rostered player in the league sorted by projected
rest-of-season value.

**components/CategoryHeatMap.jsx** --- Grid of all teams vs. all
categories with colour intensity showing relative strength. Makes
cross-team trade opportunities immediately visible.

**components/TradeCard.jsx** --- Displays a suggested trade package with
the player going out, the player coming in, the category impact for both
sides, and a fairness score. Includes a "Propose Trade" button that
opens the scheduled transaction modal pre-filled with the suggested
move.

Dependencies

Phase 5 depends on Phase 3 (Yahoo Fantasy OAuth for roster and league
data) and Phase 4 (MARCEL projections). No new Python dependencies are
required beyond those already introduced in earlier phases.

Phase 6 --- Favourites & Player Comparison

**Goal:** Allow users to star pitchers they are tracking or rostering,
surface a dedicated Favourites page showing their starred pitchers' full
stat lines and rankings, and provide a side-by-side player comparison
tool with season stats, career trends, and platoon splits from FanGraphs
for both batters and pitchers.

Favourites

A star icon is added to each pitcher row in the Rankings table and each
game card in the Week View. Clicking it toggles the pitcher as a
favourite. Favourites are stored locally in SQLite (tied to the user's
session) so they persist across page reloads and daily data refreshes.

The Favourites page shows all starred pitchers in a ranked table
identical to the Rankings page --- same columns, same profile selector,
same day filter --- but scoped to only the pitchers the user has
starred. This lets a manager quickly assess how their watchlist is
performing this week without scrolling through the full pool.

Player Comparison Tool

A dedicated Compare page lets the user search for any two players
(batters or pitchers) and view their stats side by side. The comparison
is divided into three sections:

**Season stats** --- Current season FanGraphs leaderboard stats for both
players shown in parallel columns. Pitchers: ERA, WHIP, K/9, K%-BB%,
FIP, xFIP, SIERA, QS, SV+H. Batters: AVG, OBP, SLG, wOBA, wRC+, ISO,
Barrel%, HardHit%, K%, BB%.

**Career trends** --- A multi-season sparkline chart showing each
player's primary metric (ERA− or FIP− for pitchers; wRC+ or xwOBA for
batters) over the last 5 seasons. Makes aging curves, development arcs,
and recent decline immediately visible.

**Platoon splits** --- FanGraphs platoon split data pulled via
pybaseball for both players. For pitchers: ERA, WHIP, K%, and wOBA split
by batter handedness (vs. LHB / vs. RHB). For batters: AVG, OBP, SLG,
and wOBA split by pitcher handedness (vs. LHP / vs. RHP). This directly
informs streaming decisions and start/sit calls.

New Backend Components

**models.py** --- New FavouritePitcher model with fields: id, player_id,
player_name, created_at.

**routes/favourites.py** --- GET /api/favourites, POST /api/favourites,
DELETE /api/favourites/{player_id}.

**mlb/splits.py** --- Fetches platoon split data from FanGraphs via
pybaseball. Returns vs. LHB / vs. RHB for pitchers and vs. LHP / vs. RHP
for batters. Cached in-process.

**routes/compare.py** --- GET
/api/compare?p1=NAME&p2=NAME&type=pitcher\|batter. Returns season stats,
multi-season career data, and platoon splits for both players in a
single response.

New Frontend Components

**pages/Favourites.jsx** --- Ranked table of starred pitchers, identical
in structure to the Rankings page but filtered to favourites only.
Includes the same profile selector and day filter. Each row has a filled
star icon to unfavourite.

**pages/Compare.jsx** --- Two search inputs at the top to select
players. Below: three-section layout showing season stats side-by-side,
career trend sparklines, and a platoon splits table. Supports both
pitcher vs. pitcher and batter vs. batter comparisons. Player type
(pitcher/batter) is auto-detected from the FanGraphs data.

**components/StarButton.jsx** --- Reusable star toggle button. Outline
star = not favourited, filled star = favourited. Added to each row in
Rankings, Favourites, and game cards in the Week View. Calls the
favourites API on toggle.

**components/PlatoonSplitsTable.jsx** --- Renders a two-row table (vs.
LH / vs. RH) with colour coding to highlight significant platoon
advantages or vulnerabilities. Used inside the Compare page for both
players.

**hooks/useFavourites.js** --- Manages the favourites list in React
state, synced to the backend. Exposes isFavourite(player_id),
toggleFavourite(player), and the full favourites list.

Dependencies

No new Python dependencies. Platoon split data is available via
pybaseball (already a project dependency) using the FanGraphs splits
endpoints. Career multi-season data uses the same pitching_stats and
batting_stats calls with a wider season range. On the frontend, career
trend sparklines use Recharts (already available in the React dependency
tree).

6\. Language Choice Rationale

Python was selected over other viable languages (primarily
TypeScript/Node.js) for the following reasons:

- Library ecosystem: mlb-statsapi and yahoo-fantasy-api are both
  Python-native and well-maintained. The equivalent Node.js landscape
  requires raw HTTP calls and manual OAuth handling.

- Data manipulation: Pandas is the natural choice for computing platoon
  splits and scoring models --- far more ergonomic than equivalent JS
  libraries.

- Community: The fantasy sports tooling and sports analytics communities
  are heavily Python-centric, which benefits OSS adoption.

- FastAPI quality: FastAPI is a genuinely excellent framework ---
  competitive with or superior to Express/Fastify for this use case.

TypeScript + Next.js was the runner-up and would be appropriate for a
developer with strong TypeScript experience who prefers a
single-language full-stack.

7\. Database Scalability & OSS Path

One of the explicit goals of this project is to ship it as an
open-source project once the core functionality is stable. This has
direct implications for the database strategy.

7.1 SQLite for local development

SQLite is the default and requires no setup from a contributor. Clone
the repo, install dependencies, and run --- the database is a file in
the project directory. This minimises the barrier to contribution and
keeps the local dev experience simple.

7.2 PostgreSQL for deployment

When the app is deployed --- either self-hosted or on a platform like
Railway, Render, or Fly.io --- PostgreSQL should be used. It handles
concurrent connections, supports proper user isolation (important if
multiple people run their own league instances), and is the standard for
production Python web apps.

7.3 How the abstraction works

SQLAlchemy\'s engine is configured from a DATABASE_URL environment
variable:

DATABASE_URL=sqlite:///./app.db \# local default

DATABASE_URL=postgresql://user:pass@host/db \# production

No application code changes are required when switching. SQLAlchemy\'s
ORM layer handles dialect differences. The only deployment consideration
is running Alembic migrations against the PostgreSQL instance on first
deploy.

  -----------------------------------------------------------------------
  **OSS Note:** The project README will document both database paths with
  setup instructions. Contributors running locally use SQLite
  automatically. Deployers following the deployment guide will configure
  the PostgreSQL URL. Docker Compose files will be provided for both
  single-container (SQLite) and multi-container (app + Postgres)
  configurations.

  -----------------------------------------------------------------------

7.4 Migration strategy

Database schema migrations will be managed with Alembic, SQLAlchemy\'s
migration tool. Migration files are committed to the repository so any
contributor or deployer can bring their database schema up to date with
a single command.

8\. Open Source Considerations

The project is being developed with an OSS release in mind from day one.
The following decisions reflect that goal:

  -----------------------------------------------------------------------
  **Area**         **Decision**            **Rationale**
  ---------------- ----------------------- ------------------------------
  License          MIT (planned)           Permissive, widely understood,
                                           encourages adoption

  Database         SQLite default,         Zero-friction local dev;
                   Postgres supported      production-ready deployment
                                           path

  Config           Environment variables   Standard 12-factor app
                   (.env file)             pattern, no secrets in source

  Auth tokens      Stored in .env, never   Prevents accidental token
                   in DB                   commits to public repos

  Dependencies     Pinned in               Reproducible installs for all
                   requirements.txt        contributors

  API keys         None required for Phase MLB Stats API is fully free
                   1                       with no registration
  -----------------------------------------------------------------------

9\. Proposed Project Structure

fantasy-pitchers/ ├── backend/ │ ├── main.py \# FastAPI app entry point
│ ├── scheduler.py \# APScheduler daily refresh jobs │ ├── models.py \#
SQLAlchemy models │ ├── database.py \# Engine + session (reads
DATABASE_URL) │ ├── mlb/ │ │ ├── client.py \# mlb-statsapi wrapper │ │
└── schedule.py \# Weekly schedule fetcher │ └── yahoo/ │ ├── auth.py \#
OAuth flow │ └── roster.py \# Roster + player pool fetcher ├── frontend/
│ ├── src/ │ │ ├── App.jsx │ │ ├── components/ │ │ │ ├── WeekView.jsx │
│ │ ├── PitcherCard.jsx │ │ │ └── PlatoonBadge.jsx │ │ └── api/ │ │ └──
client.js │ └── vite.config.js ├── alembic/ \# Database migrations ├──
.env.example \# Template --- never commit .env ├── requirements.txt ├──
docker-compose.yml \# SQLite (single container) ├──
docker-compose.postgres.yml \# PostgreSQL variant └── README.md

10\. Next Steps

The following tasks represent the immediate path to a working Phase 1
prototype:

6.  **Environment setup** --- Create virtual environment, install
    FastAPI, Uvicorn, SQLAlchemy, mlb-statsapi, APScheduler

7.  **Database models** --- Define Game and Pitcher SQLAlchemy models;
    initialise Alembic

8.  **MLB data fetch** --- Implement the weekly schedule fetcher using
    mlb-statsapi; validate data shape

9.  **Scheduler** --- Wire APScheduler to trigger the fetch job daily at
    a configurable time

10. **API endpoint** --- Expose GET /api/week in FastAPI; verify
    response shape matches frontend expectations

11. **React scaffold** --- Initialise Vite + React project; build
    WeekView component consuming the API

12. **Local validation** --- Test full flow end-to-end; verify TBD
    handling when pitchers are unannounced

  -----------------------------------------------------------------------
  **When Phase 1 is stable:** Begin Phase 2.5 (Pitcher Rankings) next ---
  this delivers immediate fantasy value without requiring Yahoo OAuth.
  Phase 2 (platoon advantage analysis) follows, then Phase 3 (add/drop
  recommendations + Yahoo integration).

  -----------------------------------------------------------------------
