import { useState, useMemo } from 'react'
import { useRankings } from '../hooks/useRankings'
import { useColumnResize } from '../hooks/useColumnResize'
import { RefreshCw, ArrowUp, ArrowDown, ArrowUpDown } from 'lucide-react'

const COLUMNS = [
  { key: 'rank',            label: '#',       title: 'Rank',         defaultWidth: 40 },
  { key: 'team_abbrev',     label: 'Team',    title: 'Team',         defaultWidth: 60 },
  { key: 'name',            label: 'Pitcher', title: 'Pitcher name',  defaultWidth: 150 },
  { key: 'hand',            label: 'Thows',   title: 'Throwing hand', defaultWidth: 50 },
  { key: 'opp_team_abbrev', label: 'Opp',     title: 'Opposing team', defaultWidth: 60 },
  { key: 'difficulty',      label: 'Diff',    title: 'Matchup difficulty (1=easiest, 10=hardest)', defaultWidth: 70 },
  { key: 'score',           label: 'Score',   title: 'Fantasy score for selected profile', defaultWidth: 70 },
  { key: 'game_date',       label: 'Date',    title: 'Game date',    defaultWidth: 80 },
  { key: 'era',             label: 'ERA',     title: 'Earned Run Average (lower is better)', defaultWidth: 60 },
  { key: 'whip',            label: 'WHIP',    title: 'Walks + Hits per Inning Pitched (lower is better)', defaultWidth: 60 },
  { key: 'k_per_9',         label: 'K/9',    title: 'Strikeouts per 9 innings (display only)', defaultWidth: 60 },
  { key: 'k_minus_bb',      label: 'K%-BB%',  title: 'Strikeout rate minus walk rate — used for scoring', defaultWidth: 70 },
  { key: 'quality_starts',  label: 'QS',      title: 'Quality Starts', defaultWidth: 50 },
  { key: 'svh',             label: 'SV+H',    title: 'Saves + Holds', defaultWidth: 55 },
  { key: 'opp_avg',         label: 'Opp BA',  title: 'Opposing team batting average', defaultWidth: 65 },
  { key: 'opp_ops',         label: 'Opp OPS', title: 'Opposing team OPS', defaultWidth: 70 },
  { key: 'opp_k_rate',      label: 'Opp K%',  title: 'Opposing team strikeout rate as batters', defaultWidth: 65 },
]

const DEFAULT_WIDTHS = Object.fromEntries(COLUMNS.map(c => [c.key, c.defaultWidth]))

const DAY_NAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
const MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June',
                     'July', 'August', 'September', 'October', 'November', 'December']

function formatDayBtn(dateStr) {
  // dateStr is "YYYY-MM-DD"
  const [y, m, d] = dateStr.split('-').map(Number)
  const date = new Date(y, m - 1, d)
  const dayName = DAY_NAMES[date.getDay()]
  const monthName = MONTH_NAMES[date.getMonth()]
  return `${dayName} (${monthName} ${d})`
}

function fmt(val, decimals = 2) {
  if (val == null) return <span className="rank-na">—</span>
  return typeof val === 'number' ? val.toFixed(decimals) : val
}

function fmtPct(val) {
  if (val == null) return <span className="rank-na">—</span>
  return `${(val * 100).toFixed(1)}%`
}

function fmtKminusBB(val) {
  if (val == null) return <span className="rank-na">—</span>
  const pct = (val * 100).toFixed(1)
  return (
    <span className={val >= 0.10 ? 'stat--good' : val < 0.05 ? 'stat--bad' : ''}>
      {pct}%
    </span>
  )
}

function DifficultyBadge({ value }) {
  if (value == null) return <span className="rank-na">—</span>
  const cls = value >= 7 ? 'diff-hard' : value >= 4 ? 'diff-medium' : 'diff-easy'
  return <span className={`diff-badge ${cls}`}>{value.toFixed(1)}</span>
}

function DoubleStartBadge() {
  return <span className="double-start-badge" title="Scheduled for two starts this week">2x</span>
}

function SortIcon({ colKey, sortKey, sortDir }) {
  if (sortKey !== colKey) return <ArrowUpDown size={12} className="sort-icon sort-icon--inactive" />
  return sortDir === 'asc'
    ? <ArrowUp size={12} className="sort-icon" />
    : <ArrowDown size={12} className="sort-icon" />
}

export function Rankings() {
  const {
    pitchers, profiles, loading, error,
    profile, setProfile,
    week, setWeek,
    sortKey, sortDir, handleSort,
    refresh,
  } = useRankings()

  const { widths, startResize, resetWidth, getWidth } = useColumnResize(
    COLUMNS.map(c => c.key),
    DEFAULT_WIDTHS
  )

  const [selectedDay, setSelectedDay] = useState(null)

  // Derive sorted unique dates from both weeks' pitchers
  const availableDays = useMemo(() => {
    const seen = new Set()
    pitchers.forEach(p => { if (p.game_date) seen.add(p.game_date) })
    return [...seen].sort()
  }, [pitchers])

  // Reset day filter when week changes, but auto-select today/tomorrow if selected
  const handleWeekChange = (w) => {
    if (w === 'today') {
      const today = new Date()
      const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
      setSelectedDay(todayStr)
    } else if (w === 'tomorrow') {
      const tomorrow = new Date()
      tomorrow.setDate(tomorrow.getDate() + 1)
      const tomorrowStr = `${tomorrow.getFullYear()}-${String(tomorrow.getMonth() + 1).padStart(2, '0')}-${String(tomorrow.getDate()).padStart(2, '0')}`
      setSelectedDay(tomorrowStr)
    } else {
      setSelectedDay(null)
    }
    setWeek(w)
  }

  const displayed = selectedDay
    ? pitchers.filter(p => p.game_date === selectedDay)
    : pitchers

  // Count starts per pitcher (by name) to find double-start candidates
  const startCounts = useMemo(() => {
    const counts = {}
    pitchers.forEach(p => {
      if (p.name) {
        counts[p.name] = (counts[p.name] || 0) + 1
      }
    })
    return counts
  }, [pitchers])

  const doubleStarters = new Set(
    Object.entries(startCounts).filter(([_, count]) => count >= 2).map(([name]) => name)
  )

  return (
    <div className="rankings-page">

      {/* ── Toolbar row 1: profiles + week + refresh ── */}
      <div className="rankings-toolbar">
        <div className="rankings-profiles">
          {profiles.map(p => (
            <button
              key={p.id}
              className={`profile-btn ${profile === p.id ? 'profile-btn--active' : ''}`}
              onClick={() => setProfile(p.id)}
              title={p.description}
            >
              {p.label}
            </button>
          ))}
        </div>

        <div className="week-toggle">
          <button
            className={`profile-btn ${week === 'today' ? 'profile-btn--active' : ''}`}
            onClick={() => handleWeekChange('today')}
          >
            Today
          </button>
          <button
            className={`profile-btn ${week === 'tomorrow' ? 'profile-btn--active' : ''}`}
            onClick={() => handleWeekChange('tomorrow')}
          >
            Tomorrow
          </button>
          <button
            className={`profile-btn ${week === 'current' ? 'profile-btn--active' : ''}`}
            onClick={() => handleWeekChange('current')}
          >
            This Week
          </button>
          <button
            className={`profile-btn ${week === 'next' ? 'profile-btn--active' : ''}`}
            onClick={() => handleWeekChange('next')}
          >
            Next Week
          </button>
        </div>

        <button className="btn btn-ghost" onClick={refresh} disabled={loading} title="Refresh">
          <RefreshCw size={15} className={loading ? 'spin' : ''} />
          <span>Refresh</span>
        </button>
      </div>

      {/* ── Toolbar row 2: day filter buttons ── */}
      {availableDays.length > 0 && (
        <div className="day-filter">
          <button
            className={`day-btn ${selectedDay === null ? 'day-btn--active' : ''}`}
            onClick={() => setSelectedDay(null)}
          >
            All Days
          </button>
          {availableDays.map(d => (
            <button
              key={d}
              className={`day-btn ${selectedDay === d ? 'day-btn--active' : ''}`}
              onClick={() => setSelectedDay(d)}
            >
              {formatDayBtn(d)}
            </button>
          ))}
        </div>
      )}

      {error && (
        <div className="error-banner"><strong>Could not load rankings.</strong> {error}</div>
      )}

      {loading && (
        <div className="rankings-loading">
          {Array.from({ length: 12 }).map((_, i) => (
            <div key={i} className="rankings-row-skeleton" />
          ))}
        </div>
      )}

      {!loading && !error && pitchers.length === 0 && (
        <div className="rankings-empty">
          No probable pitchers found for this week yet. Check back closer to game time.
        </div>
      )}

      {!loading && !error && pitchers.length > 0 && (
        <div className="rankings-table-wrap">
          <table className="rankings-table">
            <thead>
              <tr>
                {COLUMNS.map(col => (
                  <th
                    key={col.key}
                    onClick={() => handleSort(col.key)}
                    onDoubleClick={() => resetWidth(col.key)}
                    title={`${col.title}\nDouble-click to reset width`}
                    className={sortKey === col.key ? 'col--sorted' : ''}
                    style={{
                      width: getWidth(col.key),
                      minWidth: 40,
                    }}
                  >
                    <span className="th-inner">
                      {col.label}
                      <SortIcon colKey={col.key} sortKey={sortKey} sortDir={sortDir} />
                    </span>
                    <span
                      className="resize-handle"
                      onMouseDown={(e) => { e.stopPropagation(); startResize(e, col.key) }}
                    />
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {displayed.map((p, i) => (
                <tr key={`${p.name}-${p.game_date}`} className={i % 2 === 0 ? 'row-even' : 'row-odd'}>
                  <td className="col-rank" style={{ width: getWidth('rank'), minWidth: 40 }}>{p.rank}</td>
                  <td className="col-team" style={{ width: getWidth('team_abbrev'), minWidth: 40 }}><span className="team-pill">{p.team_abbrev}</span></td>
                  <td className="col-name" style={{ width: getWidth('name'), minWidth: 80 }}>
                    {p.name}{doubleStarters.has(p.name) && <DoubleStartBadge />}
                  </td>
                  <td className="col-hand" style={{ width: getWidth('hand'), minWidth: 40 }}>{p.hand || '—'}</td>
                  <td className="col-opp" style={{ width: getWidth('opp_team_abbrev'), minWidth: 40 }}><span className="team-pill team-pill--opp">{p.opp_team_abbrev}</span></td>
                  <td className="col-difficulty" style={{ width: getWidth('difficulty'), minWidth: 50 }}><DifficultyBadge value={p.difficulty} /></td>
                  <td className="col-score" style={{ width: getWidth('score'), minWidth: 50 }}><strong>{p.score != null ? p.score.toFixed(1) : '—'}</strong></td>
                  <td className="col-date" style={{ width: getWidth('game_date'), minWidth: 60 }}>{p.game_date ? p.game_date.slice(5) : '—'}</td>
                  <td className={`col-stat ${p.era != null && p.era < 3.5 ? 'stat--good' : p.era != null && p.era > 4.5 ? 'stat--bad' : ''}`} style={{ width: getWidth('era'), minWidth: 50 }}>
                    {fmt(p.era)}
                  </td>
                  <td className={`col-stat ${p.whip != null && p.whip < 1.2 ? 'stat--good' : p.whip != null && p.whip > 1.4 ? 'stat--bad' : ''}`} style={{ width: getWidth('whip'), minWidth: 50 }}>
                    {fmt(p.whip)}
                  </td>
                  <td className="col-stat" style={{ width: getWidth('k_per_9'), minWidth: 50 }}>{fmt(p.k_per_9)}</td>
                  <td className="col-stat" style={{ width: getWidth('k_minus_bb'), minWidth: 60 }}>{fmtKminusBB(p.k_minus_bb)}</td>
                  <td className="col-stat" style={{ width: getWidth('quality_starts'), minWidth: 40 }}>{fmt(p.quality_starts, 0)}</td>
                  <td className="col-stat" style={{ width: getWidth('svh'), minWidth: 50 }}>{fmt(p.svh, 0)}</td>
                  <td className="col-stat" style={{ width: getWidth('opp_avg'), minWidth: 50 }}>{fmt(p.opp_avg, 3)}</td>
                  <td className="col-stat" style={{ width: getWidth('opp_ops'), minWidth: 50 }}>{fmt(p.opp_ops, 3)}</td>
                  <td className="col-stat" style={{ width: getWidth('opp_k_rate'), minWidth: 50 }}>{fmtPct(p.opp_k_rate)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
