# Fantasy Baseball Pitchers App

A Python web application that surfaces probable starting pitchers for the upcoming fantasy baseball week, with rankings and analytics to help fantasy managers make better start/sit decisions.

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI |
| **Frontend** | React + Vite |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **ORM** | SQLAlchemy |
| **Scheduler** | APScheduler |
| **MLB Data** | mlb-statsapi, pybaseball |

## Project Phases

### Phase 1 — MVP (Complete)
- Weekly probable pitchers view
- Daily auto-refresh via APScheduler
- SQLite local storage

### Phase 2 — Platoon Advantage (Deferred)
- Cross-reference pitcher handedness with batter splits
- Color-coded matchup indicators

### Phase 2.5 — Pitcher Rankings (Complete)
- Rank probable pitchers by projected fantasy value
- 4 scoring profiles: Balanced, K-Focused, ERA/WHIP, Closer
- Opponent difficulty scoring
- Day filtering

### Phase 3 — Yahoo Fantasy Integration (Planned)
- OAuth connection to Yahoo Fantasy league
- Add/drop recommendations
- Scheduled transactions

### Phase 4 — Advanced Analytics (Planned)
- MARCEL projection model
- Breakout detection using Statcast metrics

### Phase 5 — League Power Rankings (Planned)
- Team rankings across all categories
- Trade target identification

### Phase 6 — Favourites & Player Comparison (Planned)
- Star pitchers for tracking
- Side-by-side player comparison with career trends and platoon splits

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- [UV](https://github.com/astral-sh/uv) (Python package manager)

### Backend Setup (with UV)

The backend uses `pyproject.toml` for dependencies. UV reads this automatically.

```bash
cd src
uv sync
cp .env.example .env
uv run uvicorn main:app --reload
```

The API runs at `http://localhost:8000` with docs at `http://localhost:8000/docs`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The app runs at `http://localhost:5173`

## Environment Variables

Create a `.env` file in `src/`:

```
DATABASE_URL=sqlite:///./app.db
MLB_API_KEY=  # Not required for Phase 1
```

## License

GPLv3