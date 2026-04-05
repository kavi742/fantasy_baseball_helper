# Fantasy Baseball Probable Pitchers App

**Project Planning & Architecture Document**

March 2026 | Version 1.0

**Status:** Pre-implementation planning

**Target:** Open-source release (post-internal validation)

**Language:** Python

---

## 1. Project Overview

This document captures all planning decisions made for a Python-based web application that surfaces probable starting pitchers for the upcoming fantasy baseball week. The app is designed to be built incrementally across six phases, starting with a clean MVP and expanding toward full fantasy decision support.

The project will be developed privately first, then released as an open-source project once the core functionality is stable and well-tested. All technical decisions have been made with this OSS trajectory in mind — favouring widely understood tools, clean abstractions, and a database layer that can scale.

---

## 2. Goals & Scope

### 2.1 Primary Goal

Display the full week's probable starting pitchers across all MLB matchups, pulled from official team announcements via free APIs, with no manual data entry required.

### 2.2 Future Feature Goals

- **Platoon advantage analysis** — Cross-reference pitcher handedness with batter splits to surface favourable matchups
- **Add/drop recommendations** — Identify streamable pitchers and hot waiver wire targets based on upcoming schedules
- **Fantasy platform integration** — Connect to a user's Yahoo or ESPN Fantasy league to personalise recommendations against their actual roster
- **Category gap analysis** — Throughout the week, detect which categories the user is lacking and suggest streamers to catch up
- **Team analysis** — Analyze every team in the league to determine strengths/weaknesses for trade target identification

### 2.3 Out of Scope (Initial Release)

- Projections or predictive modelling (this uses real announced starters only)
- Mobile app — web application only
- Multi-sport support

---

## 3. Architecture Overview

The application follows a standard three-layer architecture: external data sources feed a Python backend, which stores processed data in a local database and exposes a REST API, consumed by a React frontend.

### 3.1 Data Sources

| **Source** | **Purpose** |
|------------|-------------|
| **MLB Stats API** | Schedule, probable pitchers, player handedness, splits — free, no API key required |
| **mlb-statsapi (Python library)** | Python wrapper for the MLB Stats API, handles date-range schedule queries and team batting stats. Not used for pitcher season stats (see pybaseball below). |
| **Yahoo Fantasy Sports API** | Roster data, league player pool, waiver wire, add/drop history — requires free OAuth app registration |
| **ESPN Fantasy API (unofficial)** | Alternative to Yahoo — no key required but undocumented; lower reliability |

### 3.2 Data Freshness

The MLB API returns real pitcher announcements — not computer-generated predictions. Teams typically confirm starting pitchers 24–48 hours before game time, meaning early-week queries will show many TBD entries that fill in mid-week. The application must refresh daily to capture new announcements.

> **Note:** The fantasy baseball scoring week typically runs Monday–Sunday. The app should align its weekly view to the active scoring period rather than a rolling 7-day window.

---

## 4. Recommended Technology Stack

Each layer of the stack was evaluated across multiple options. The recommendations below optimise for development speed, community support, OSS-friendliness, and the ability to scale to a hosted multi-user deployment later.

### 4.1 Backend Framework

| **Option** | **Assessment** |
|-----------|----------------|
| **FastAPI ✓ Recommended** | Async-first, automatic Swagger docs at /docs, built-in request validation via Pydantic. Ideal for serving a REST API consumed by a React frontend. |
| **Flask** | Simpler and more familiar — perfectly viable, especially for Phase 1. Lacks built-in async and data validation. |
| **Django** | Overkill for this project. Brings a full ORM, admin panel, and auth system that this app doesn't need. |

### 4.2 Frontend

| **Option** | **Assessment** |
|-----------|----------------|
| **React + Vite ✓ Recommended** | Best fit for an interactive weekly calendar view with filtering, status badges, and eventual platoon colour-coding. Vite gives fast builds and HMR. |
| **Jinja2 + HTMX** | Simpler to start, server-side rendered. Becomes awkward once interactivity requirements grow (filtering, live updates). |
| **Streamlit** | Very fast to prototype but not suitable for a polished, shippable UI. Limited layout control. |
| **Dash (Plotly)** | Good for data dashboards but opinionated layout system makes custom UI work harder. |

### 4.3 Database

The database choice was made with two requirements in mind: zero-friction local development, and a clear upgrade path to a hosted deployment when the project goes OSS.

| **Option** | **Assessment** |
|-----------|----------------|
| **SQLite ✓ Recommended (dev/MVP)** | Zero setup, single file, ships with Python. Sufficient for a single user's league data and daily cached pitcher data. Ideal for local development and initial OSS contributors. |
| **PostgreSQL ✓ Recommended (production/OSS)** | The natural upgrade path when the app is deployed for multiple users or leagues. Full SQL compatibility with SQLite means minimal code changes. |
| **JSON flat files** | Acceptable for Phase 1 only — no querying capability, will become a maintenance burden as data volume grows. |

> **OSS Consideration:** The database layer will be abstracted via SQLAlchemy from day one, using SQLite as the default for local development. A PostgreSQL connection string can be dropped in via environment variable for deployed instances, with no code changes required. The README will document both paths clearly for OSS contributors.

### 4.4 ORM / Data Access

| **Option** | **Assessment** |
|-----------|----------------|
| **SQLAlchemy ✓ Recommended** | Industry-standard Python ORM. Abstracts the database engine entirely — switching from SQLite to PostgreSQL is a single config change. Widely known by Python contributors. |
| **Peewee** | Lighter and simpler than SQLAlchemy. Good for very small projects but less familiar to the wider Python community. |
| **Raw SQL** | Acceptable for a small solo project but creates tight coupling to the database engine, which conflicts with the SQLite → PostgreSQL upgrade path. |

### 4.5 Background Scheduling

The app needs to refresh pitcher data daily, ideally without requiring a separate process or infrastructure.

| **Option** | **Assessment** |
|-----------|----------------|
| **APScheduler ✓ Recommended** | Runs inside the FastAPI process. No Redis, no separate worker. Define a job function and schedule it to run at a set time each day. Ideal for a single-instance deployment. |
| **Celery + Redis** | The right tool for distributed task queues at scale. Significant infrastructure overhead for a daily data refresh task. |
| **OS cron** | Simple and reliable. Requires the server OS to manage the schedule, which is less portable for OSS contributors running on different platforms. |

### 4.6 OAuth / Authentication (Yahoo API)

Accessing a user's Yahoo Fantasy league requires OAuth 2.0. The access tokens expire and must be refreshed.

| **Option** | **Assessment** |
|-----------|----------------|
| **yahoo-fantasy-api (built-in) ✓ Recommended** | The yahoo-fantasy-api Python library handles the OAuth token flow internally. Try this first before adding a separate auth library. |
| **Authlib** | Full-featured OAuth library for FastAPI. Use if yahoo-fantasy-api's token handling proves insufficient. |
| **requests-oauthlib** | Lightweight OAuth wrapper for the requests library. Lower-level than Authlib. |

### 4.7 Full Recommended Stack Summary

| **Layer** | **Choice** |
|-----------|------------|
| Backend framework | FastAPI |
| Frontend | React + Vite |
| Database (local/dev) | SQLite |
| Database (production/OSS) | PostgreSQL |
| ORM | SQLAlchemy |
| Scheduler | APScheduler |
| OAuth | yahoo-fantasy-api (built-in) |
| MLB data library | mlb-statsapi |
| Fantasy data library | yahoo-fantasy-api |

---

## 5. Phased Delivery Plan

The project is split into six phases. Each phase delivers a standalone, usable increment. Phase 1 is the minimum viable product and the starting point for development.

---

### Phase 1 — MVP: Probable Pitchers View

**Fantasy Roster Integration (Future Enhancement)**

Once Yahoo Fantasy integration is implemented (Phase 3), the Week View gains a powerful personalization layer:

- **Roster awareness** — After authenticating with Yahoo Fantasy, the app fetches the user's current roster
- **Game highlighting** — Any game featuring a player from the user's roster is highlighted with a distinct border or background color
- **Ownership indicator** — A small badge or icon on the game card indicates which players from the roster are in that game (e.g., "Your P: Shohei Ohtani")
- **Start/Sit helper** — Games where the user has a pitcher starting are flagged as "Your SP" to make it easy to scan for decisions
- **Multi-league support** — For users in multiple leagues, allow league selection to switch which roster is highlighted

This transforms the Week View from a generic schedule into a personalized decision dashboard.

**Goal:** Show all MLB games for the current fantasy week with probable starters, updated daily.

**Data flow:**

1. APScheduler triggers a daily refresh job at a configured time
2. mlb-statsapi fetches the week's schedule with probable pitcher fields
3. Results are written to SQLite via SQLAlchemy
4. FastAPI exposes a `/api/week` endpoint returning matchups as JSON
5. React frontend renders a calendar-style weekly view grouped by date

**Key API endpoint:**

```
GET /api/week → { date, away_team, home_team, away_pitcher, home_pitcher }
```

---

### Phase 2 — Platoon Advantage Analysis

**Reliever Workload Tracking (Reliever Rankings Enhancement)**

When viewing relievers in the rankings, each reliever's recent workload should be tracked to estimate availability:

- **Recent appearance tracking** — Query the MLB API boxscore for the past 2-3 days to find which relievers pitched and when
- **Appearance marker** — Display an indicator (e.g., colored dot or "Pitched Yesterday" badge) showing recent usage:
  - Green dot = pitched 3+ days ago (fresh)
  - Yellow dot = pitched 1-2 days ago (likely available but monitor)
  - Red dot = pitched today/yesterday (likely unavailable)
- **Inherited runners** — Boxscore data also shows if a reliever left with runners on, indicating potential for hold/win credit
- **Rest days indicator** — Help fantasy managers identify relievers who are "on rest" and unlikely to pitch tonight

This data helps managers avoid starting a reliever whose team played yesterday and may have burned through their best arms.

**Goal:** Surface which batters on a user's roster have a handedness advantage against that day's probable pitcher.

- Pull pitcher handedness from the MLB Stats API player endpoint
- Pull batter vs. LHP / vs. RHP split stats from the MLB Stats API stats endpoint
- Compute a platoon advantage score and surface favourable matchups in the UI
- Add colour-coded indicators to the weekly view (e.g., green highlight = strong platoon advantage)

---

### Phase 2.5 — Pitcher Rankings

**Goal:** Rank all probable pitchers for the current week by projected fantasy value, factoring in their season stats and the offensive strength of the team they face. Designed for head-to-head categories leagues.

**Scoring Stats**

The ranking model uses five standard head-to-head categories: Strikeouts (K), Earned Run Average (ERA), WHIP (Walks + Hits per Inning Pitched), Quality Starts (QS), and Saves + Holds (SV+H).

**Opposing Team Difficulty**

Each pitcher's projected score is adjusted by the offensive strength of the team they face. Opponent data is pulled from the MLB Stats API (season team batting stats) and displayed in three columns:

- **BA / OPS** — Team batting average and on-base plus slugging. Higher values indicate a tougher lineup.
- **Opp K%** — Opposing team's strikeout rate as batters. A high K% means the lineup strikes out often, which is favourable for pitcher strikeout projections.
- **Difficulty Score** — A composite 1–10 score combining BA, OPS, and batter K% into a single matchup difficulty rating. Higher = tougher opponent.

**Preset Scoring Profiles**

Users select a profile at the top of the rankings page to weight stats according to their roster needs:

- **Balanced** — Equal weight across all five categories. Good default for most managers.
- **K-Focused** — Heavy weight on strikeouts and WHIP. For managers targeting the K category.
- **ERA / WHIP** — Ratio stats only. Best for managers whose counting stats are already strong.
- **Closer** — Heavy SV+H weight. For streaming relievers and save-hunting strategies.

**New Backend Components:**

- `mlb/stats.py` — Fetches pitcher season stats via pybaseball (FanGraphs leaderboard data — ERA, WHIP, K/9, QS, SV+H, xFIP, SIERA, K%). Team batting stats fetched from mlb-statsapi.
- `services/rankings.py` — Scoring and weighting logic. Normalises stats, applies profile weights, computes opponent difficulty modifier, and returns a ranked list.
- `routes/rankings.py` — Exposes `GET /api/rankings?profile=balanced`. Returns ranked pitcher list with stats and opponent difficulty data.

**New Frontend Components:**

- `pages/Rankings.jsx` — Sortable table with one row per probable pitcher.
- `hooks/useRankings.js` — Fetches rankings data, manages selected profile state, and handles sorting.
- Nav bar to switch between the Week View and the Rankings page.

---

### Phase 3 — Fantasy Integration, Add/Drop & Category Gap Analysis

**Goal:** Connect to the user's Yahoo Fantasy league to personalise recommendations against their actual roster, plus provide weekly category gap analysis to help catch up in lagging categories.

**Yahoo Fantasy Integration**

- Implement Yahoo Fantasy OAuth flow via the yahoo-fantasy-api library
- Fetch the user's current roster and the full league player pool (owned, waivers, free agents)
- Build an add/drop scoring model: combine upcoming schedule, platoon advantage, and injury status
- Surface the top add/drop recommendations ranked by projected value for the current week

**Scheduled Transactions**

A key addition to the Yahoo Fantasy integration is the ability to plan and schedule add/drop transactions ahead of time.

- **Queue transactions** — User selects a player to add and a player to drop, picks an execution date and time
- **Scheduled execution** — APScheduler checks the queue and fires pending transactions at the specified time
- **Transaction queue UI** — Dedicated panel showing all pending, executed, and failed transactions
- **Status tracking** — Each transaction stored in DB with status: pending, executed, failed, or cancelled

**Weekly Category Gap Analysis & Streaming Recommendations**

A key feature that runs throughout the week to help managers catch up in categories they're lacking.

- **Category gap detection** — Compare the user's current standings to the league median in each head-to-head category
- **Streaming recommendations** — Surface available pitchers (waiver wire / free agents) with upcoming starts, ranked by projected category contribution
- **Gap severity scoring** — Rank detected gaps by severity: critical (likely to lose), vulnerable (close to median), secure (safe lead)
- **In-season adjustment** — Re-evaluate gaps daily as the week progresses
- **Opponent-aware suggestions** — Factor in opponent quality when suggesting streamers

**New Backend Components:**

- `models.py` — New ScheduledTransaction model
- `services/transactions.py` — Business logic for creating, cancelling, and executing transactions
- `routes/transactions.py` — REST endpoints: POST/GET/DELETE /api/transactions
- `services/category_gap.py` — Compares user's roster stats to league median, computes gap severity
- `services/streaming.py` — Finds available pitchers with remaining starts, scores against category needs
- `scheduler.py` — Extended to poll the ScheduledTransaction table

**New Frontend Components:**

- `pages/Transactions.jsx` — Transaction queue panel
- `components/ScheduleTransactionModal.jsx` — Modal form to schedule a new add/drop
- `components/CategoryGaps.jsx` — Dashboard showing current category gaps with severity indicators
- `components/StreamingSuggestions.jsx` — List of recommended streamers based on identified gaps

---

### Phase 4 — Advanced Analytics & Breakout Detection

**Goal:** Surface breakout candidates for both batters and pitchers using advanced Statcast metrics and projection models.

**Data Sources**

All data is pulled via pybaseball (already a project dependency).

- **Pitching metrics (FanGraphs)** — ERA, WHIP, FIP, xFIP, SIERA, K%, BB%, K−BB%, SwStr%, CSW%, GB%
- **Batting metrics (FanGraphs)** — wOBA, wRC+, ISO, BABIP, BB%, K%, Hard Hit%, Barrel%, Sprint Speed
- **Statcast data** — Exit velocity, launch angle, Barrel%, xBA, xSLG, xwOBA, HardHit%

**Projection Model**

The projection pipeline runs in two stages:

1. **MARCEL baseline** — The minimum-competency standard for baseball projections. Applies three transformations:
   - Weighted average of the last three seasons (5/4/3 recency weighting)
   - Regression to the mean (pulls projections toward league average)
   - Age adjustment (boost for young players, penalty for players past peak)

2. **Machine learning layer (optional)** — Gradient-boosted model (XGBoost or LightGBM) trained on historical player seasons to improve projection accuracy.

**Breakout Detection**

A player is flagged as a breakout candidate when their projected stats represent a meaningful improvement (configurable threshold, default 15%) over their rolling 3-year average.

- **Pitching breakout signals** — Rising K%, falling BB%, improved SwStr% or CSW%, FIP or xFIP significantly below ERA
- **Batting breakout signals** — Rising Barrel% or HardHit%, xBA or xwOBA outpacing actual BA, improved launch angle, reduced K%

**New Backend Components:**

- `mlb/statcast.py` — Fetches Statcast data via pybaseball
- `services/projections.py` — MARCEL projection engine for pitchers and batters
- `services/breakouts.py` — Compares projections to rolling 3-year averages, applies breakout signal rules
- `routes/analytics.py` — Exposes GET /api/analytics/breakouts?type=pitching|batting

**New Frontend Components:**

- `pages/Analytics.jsx` — Two-tab page (Pitching / Batting) showing ranked breakout candidates
- `components/BreakoutBadge.jsx` — Colour-coded badge (High / Medium / Low) indicating breakout confidence
- `components/StatTrend.jsx` — Sparkline showing a player's key metric over the last 3 seasons

**Additional Dependencies:**

- pandas / numpy — Required for MARCEL calculations
- scikit-learn or XGBoost — Optional, for Stage 2 ML layer only

---

### Phase 5 — League Power Rankings & Trade Targets

**Goal:** Analyze every team in the user's Yahoo Fantasy league to determine their strengths and weaknesses, and use this analysis to identify the best trade targets.

**Team Analysis & Strengths/Weaknesses Mapping**

- **Full league scan** — Pull all teams and compute current standings across all head-to-head categories (5x5: R, HR, RBI, SB, AVG for batting; W, K, ERA, WHIP, SV+H for pitching)
- **Category grades per team** — Assign each team a grade (1-10) for each category based on relative league ranking
- **Visual team profile** — Each team's profile shows at a glance what categories they excel in (strengths) and where they struggle (weaknesses)
- **Trade target identification** — Cross-reference user's category profile against every other team to identify complementary mismatches (win-win trades)

**Power Rankings**

- **Overall power score** — Composite rank across all 10 categories, weighted equally, displayed as leaderboard with trend arrows
- **Category breakdown** — Per-category grade (1-10) with heat map view for cross-team comparisons
- **Roster health** — Flags teams carrying injured players with strong projections (buy-low) and teams over-relying on players with poor metrics (sell-high)

**Trade Target Identification**

- **Buy-low targets** — Players on other rosters whose actual stats lag projections (likely to improve)
- **Sell-high targets** — Players on user's roster whose actual stats outpace underlying metrics (elevated trade value)
- **Category swap suggestions** — "Team X is weak in SB and strong in HR. You are weak in HR and strong in SB. These two players could work."
- **Trade value scores** — Rest-of-season trade value score derived from MARCEL projection, age curve, and injury status

**New Backend Components:**

- `services/power_rankings.py` — Pulls all league rosters, applies MARCEL projections, computes normalised power score
- `services/trade_engine.py` — Compares category profiles, identifies buy-low/sell-high candidates, generates trade package suggestions
- `routes/league.py` — Exposes GET /api/league/power-rankings, /api/league/trade-targets, /api/league/trade-value

**New Frontend Components:**

- `pages/League.jsx` — Three-tab page: Power Rankings, Trade Targets, Trade Values
- `components/CategoryHeatMap.jsx` — Grid of all teams vs. all categories with colour intensity
- `components/TradeCard.jsx` — Displays suggested trade package with category impact and fairness score

---

### Phase 6 — Favourites & Player Comparison

**Goal:** Allow users to star pitchers they are tracking and provide a side-by-side player comparison tool.

**Favourites**

- Star icon on each pitcher row in Rankings table and game cards
- Stored in SQLite (tied to user's session)
- Dedicated Favourites page showing all starred pitchers in a ranked table

**Player Comparison Tool**

A dedicated Compare page lets the user search for any two players and view their stats side by side:

- **Season stats** — Current season FanGraphs leaderboard stats in parallel columns
- **Career trends** — Multi-season sparkline chart showing key metric over the last 5 seasons
- **Platoon splits** — FanGraphs platoon split data (vs. LHB / vs. RHB for pitchers; vs. LHP / vs. RHP for batters)

**New Backend Components:**

- `models.py` — New FavouritePitcher model
- `routes/favourites.py` — GET/POST/DELETE /api/favourites
- `mlb/splits.py` — Fetches platoon split data via pybaseball
- `routes/compare.py` — GET /api/compare?p1=NAME&p2=NAME&type=pitcher|batter

**New Frontend Components:**

- `pages/Favourites.jsx` — Ranked table of starred pitchers
- `pages/Compare.jsx` — Two search inputs with three-section layout (season stats, career trends, platoon splits)
- `components/StarButton.jsx` — Reusable star toggle button
- `components/PlatoonSplitsTable.jsx` — Renders two-row table (vs. LH / vs. RH) with colour coding
- `hooks/useFavourites.js` — Manages favourites list in React state

---

## 6. Language Choice Rationale

Python was selected over other viable languages (primarily TypeScript/Node.js) for the following reasons:

- **Library ecosystem** — mlb-statsapi and yahoo-fantasy-api are both Python-native and well-maintained
- **Data manipulation** — Pandas is the natural choice for computing platoon splits and scoring models
- **Community** — Fantasy sports tooling and sports analytics communities are heavily Python-centric
- **FastAPI quality** — Genuinely excellent framework — competitive with or superior to Express/Fastify

TypeScript + Next.js was the runner-up and would be appropriate for a developer with strong TypeScript experience.

---

## 7. Database Scalability & OSS Path

One of the explicit goals of this project is to ship it as an open-source project once the core functionality is stable. This has direct implications for the database strategy.

### 7.1 SQLite for Local Development

SQLite is the default and requires no setup from a contributor. Clone the repo, install dependencies, and run — the database is a file in the project directory.

### 7.2 PostgreSQL for Deployment

When the app is deployed (self-hosted or on platforms like Railway, Render, Fly.io), PostgreSQL should be used. It handles concurrent connections, supports proper user isolation, and is the standard for production Python web apps.

### 7.3 How the Abstraction Works

SQLAlchemy's engine is configured from a DATABASE_URL environment variable:

```
DATABASE_URL=sqlite:///./app.db  # local default
DATABASE_URL=postgresql://user:pass@host/db  # production
```

No application code changes are required when switching. The only deployment consideration is running Alembic migrations against the PostgreSQL instance on first deploy.

> **OSS Note:** The README will document both database paths. Docker Compose files will be provided for both single-container (SQLite) and multi-container (app + Postgres) configurations.

### 7.4 Migration Strategy

Database schema migrations will be managed with Alembic. Migration files are committed to the repository.

---

## 8. Open Source Considerations

The project is being developed with an OSS release in mind from day one:

| **Area** | **Decision** | **Rationale** |
|----------|--------------|----------------|
| License | GPLv3 | Strong copyleft, ensures derivative works remain open |
| Database | SQLite default, Postgres supported | Zero-friction local dev; production-ready path |
| Config | Environment variables (.env file) | Standard 12-factor app pattern, no secrets in source |
| Auth tokens | Stored in .env, never in DB | Prevents accidental token commits |
| Dependencies | Pinned in requirements.txt | Reproducible installs |
| API keys | None required for Phase 1 | MLB Stats API is free |

---

## 9. Proposed Project Structure

```
fantasy-pitchers/
├── src/
│   ├── main.py              # FastAPI app entry point
│   ├── scheduler.py         # APScheduler daily refresh jobs
│   ├── models.py            # SQLAlchemy models
│   ├── database.py          # Engine + session (reads DATABASE_URL)
│   ├── config.py            # Settings
│   ├── pyproject.toml       # UV dependencies
│   ├── routes/
│   │   ├── schedule.py      # /api/week endpoint
│   │   └── rankings.py     # /api/rankings endpoint
│   ├── services/
│   │   ├── schedule.py     # Schedule fetching
│   │   └── rankings.py     # Rankings logic
│   └── mlb/
│       ├── client.py       # mlb-statsapi wrapper
│       └── stats.py        # MLB stats fetching
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── index.css
│   │   ├── pages/
│   │   │   ├── WeekView.jsx
│   │   │   └── Rankings.jsx
│   │   ├── components/
│   │   │   ├── Header.jsx
│   │   │   ├── GameCard.jsx
│   │   │   ├── Filters.jsx
│   │   │   └── ThemePicker.jsx
│   │   ├── hooks/
│   │   │   ├── useWeek.js
│   │   │   ├── useRankings.js
│   │   │   ├── useFilters.js
│   │   │   └── useTheme.js
│   │   ├── api/
│   │   │   └── client.js
│   │   └── themes.js
│   ├── package.json
│   └── vite.config.js
├── alembic/                  # Database migrations
├── .env.example              # Template — never commit .env
├── README.md
├── fantasy_baseball_planning.md
└── docker-compose.yml
```

---

## 10. Next Steps

The following tasks represent the immediate path to a working Phase 1 prototype:

1. **Environment setup** — Install FastAPI, Uvicorn, SQLAlchemy, mlb-statsapi, APScheduler
2. **Database models** — Define Game and Pitcher SQLAlchemy models; initialise Alembic
3. **MLB data fetch** — Implement the weekly schedule fetcher using mlb-statsapi
4. **Scheduler** — Wire APScheduler to trigger the fetch job daily at a configurable time
5. **API endpoint** — Expose GET /api/week in FastAPI
6. **React scaffold** — Build WeekView component consuming the API
7. **Local validation** — Test full flow end-to-end; verify TBD handling

---

> **When Phase 1 is stable:** Begin Phase 2.5 (Pitcher Rankings) next — this delivers immediate fantasy value without requiring Yahoo OAuth. Phase 2 (platoon advantage analysis) follows, then Phase 3 (add/drop recommendations + Yahoo integration).

---

## 11. Technical Notes & Performance Considerations

This section captures important technical decisions and performance optimizations that should not be forgotten.

### 11.1 MLB API Performance Bottlenecks

The MLB Stats API has several performance considerations that must be addressed:

**Pitcher Handedness Lookups**
- The MLB schedule API returns pitcher names but NOT pitcher IDs
- Looking up hands requires two API calls per pitcher: `lookup_player()` → `get("people", {"personIds": id})`
- Each lookup takes ~400ms, and a week can have 149+ unique pitchers
- **Solution:** Store pitcher hands in the database during the persist phase. The `Pitcher` model has a `hand` field specifically for this. `_pitcher_dict()` reads from DB, not API.

**Batch Hand Lookups for Relievers**
- The reliever rankings page needs hands for ~573 active relievers
- Original implementation took ~228 seconds (3+ minutes) due to slow pybaseball lookups
- **Solution:** 
  1. `get_pitcher_hands_batch()` now accepts pre-resolved `player_id` mapping to skip pybaseball lookups
  2. Check DB first before calling individual API lookups
  3. `get_all_bullpens()` is now cached with `@lru_cache`
  4. Team roster lookups cached with larger `maxsize=32`
- First load: ~5s (30 team rosters + FanGraphs stats + batch hand API)
- Subsequent loads: ~235ms (all caches warm)
- The `PitcherHand` model stores `player_id`, `full_name`, `hand`, and `fetched_at`

**Boxscore Lookups for Quality Starts**
- Calculating QS requires boxscore data for completed games
- 92 games × ~130ms each = ~12s if done naively
- **Solution:** Added `@lru_cache(maxsize=100)` to `get_game_boxscore()` in `mlb/client.py`. Caches results for repeated requests.

**Season Stats for Game Detail Page**
- The `/stats` endpoint with `playerIds` parameter returns **team-level** stats, not individual player stats
- **Solution:** Use the `/people/{id}/stats` endpoint which correctly returns each player's individual stats.

**Batter Splits**
- The MLB API `statSplits` endpoint is unreliable (500 errors)
- **Solution:** Use `/people/{id}/stats` with `sitCodes=vl,vr` parameters for handedness splits (vs LHP / vs RHP)

### 11.2 Database Schema for Performance

The `Pitcher` model stores:
```python
hand: Mapped[str | None]  # L / R — pre-fetched during persist
```

This prevents repeated API calls for every request. The `hand` field is populated in `_persist()` in `services/schedule.py`.

### 11.3 Caching Strategy

| Cache | Location | TTL | Purpose |
|-------|----------|-----|---------|
| In-memory | Python `lru_cache` | Process lifetime | `get_pitcher_hand()`, `get_game_boxscore()` |
| Database | SQLite/Postgres | Until next daily refresh | Pitcher data, game schedule |
| Frontend | React state + localStorage | 5 minutes | API responses |

### 11.4 First Load Performance

After a backend restart, the first load is slow (~15s) because:
1. All pitcher hands must be fetched from MLB API
2. Boxscores for completed games must be cached

This is unavoidable. Subsequent loads are ~20ms from database cache.

**Reliever Rankings Optimization:**
- The `/api/relievers` endpoint now passes a DB session to `get_pitcher_hands_batch()`
- Results are persisted to the `pitcher_hands` table
- After first load, reliever rankings load in ~5ms (vs ~167s without caching)

### 11.5 Reliever Rankings Performance Optimization

**Problem:** Reliever rankings page was taking 3+ minutes to load due to slow pitcher hand lookups.

**Root Causes:**
- `get_pitcher_hand_by_name()` takes 326ms per cache miss
- 573 relievers × 326ms = 187 seconds just for hand lookups
- `get_all_bullpens()` was not cached, requiring 30 team roster API calls each time
- Original `get_pitcher_hands_batch()` checked LRU cache before DB, causing unnecessary API calls

**Solution - Changes Made:**

1. **`get_pitcher_hands_batch()`** - Refactored to:
   - Accept pre-resolved player IDs to skip pybaseball lookups
   - Check DB first before LRU cache (avoids 326ms API calls for cached data)
   - Only batch-fetch hands not in DB

2. **`get_all_bullpens()`** - Added `@lru_cache` wrapper to cache bullpen results

3. **`get_team_roster()`** - Increased cache size from 1 to 32 (covers all MLB teams)

4. **`reliever_rankings.py`** - Updated to pass `name_to_id` mapping to batch function

**Performance Results:**
- First load: ~5 seconds (30 team rosters + FanGraphs stats + batch hand API)
- Subsequent loads: ~235ms (all caches warm)
- Before optimization: ~228 seconds (3+ minutes)

### 11.6 SQLite Concurrency Fix

**Problem:** When multiple API requests hit simultaneously (e.g., prefetch on page load), SQLite database locks caused "database is locked" errors.

**Solution:** Enabled WAL (Write-Ahead Logging) mode and optimized SQLite pragmas in `database.py`:

```python
def _set_sqlite_pragma(dbapi_conn, connection_record):
    if settings.database_url.startswith("sqlite"):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")      # Allows concurrent reads during writes
        cursor.execute("PRAGMA synchronous=NORMAL")    # Better performance with WAL
        cursor.execute("PRAGMA busy_timeout=5000")    # Wait up to 5 seconds for locks
        cursor.execute("PRAGMA cache_size=-64000")    # 64MB cache
        cursor.close()

event.listen(engine, "connect", _set_sqlite_pragma)
```

**Key Settings:**
- `journal_mode=WAL` - Enables concurrent access (reads don't block writes)
- `busy_timeout=5000` - 5 second wait before failing on lock
- `synchronous=NORMAL` - Safe with WAL, faster than FULL
- `cache_size=-64000` - 64MB in-memory cache

### 11.7 Frontend Caching

The React API client (`frontend/src/api/client.js`) uses a Map-based cache with 5-minute TTL:
- `fetchWeek()`, `fetchRankings()`, `fetchRelievers()`, `fetchGame()` all use caching
- `clearCache()` function available for force refresh

### 11.8 Color Scheme

CSS variables are used for theme support (light/dark mode):
```css
--highlight-bg:       /* Cell background for highlighted columns */
--highlight-header-bg: /* Header background for active splits */
--highlight-row-bg:   /* Row background for favorable matchups */
--highlight-text:     /* Text color for highlighted elements */
```

All components (Game Detail, Rankings) use these variables for consistent theming.