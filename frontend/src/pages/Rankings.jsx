import { useRankings } from '../hooks/useRankings'
import { RefreshCw, ArrowUp, ArrowDown, ArrowUpDown } from 'lucide-react'

const COLUMNS = [
  { key: 'rank',         label: '#',          title: 'Rank' },
  { key: 'name',         label: 'Pitcher',    title: 'Pitcher name' },
  { key: 'team_abbrev',  label: 'Team',       title: 'Team' },
  { key: 'opp_team_abbrev', label: 'Opp',    title: 'Opposing team' },
  { key: 'game_date',    label: 'Date',       title: 'Game date' },
  { key: 'era',          label: 'ERA',        title: 'Earned Run Average (lower is better)' },
  { key: 'whip',         label: 'WHIP',       title: 'Walks + Hits per Inning Pitched (lower is better)' },
  { key: 'k_per_9',      label: 'K/9',        title: 'Strikeouts per 9 innings' },
  { key: 'quality_starts', label: 'QS',       title: 'Quality Starts' },
  { key: 'svh',          label: 'SV+H',       title: 'Saves + Holds' },
  { key: 'opp_avg',      label: 'Opp BA',     title: 'Opposing team batting average' },
  { key: 'opp_ops',      label: 'Opp OPS',    title: 'Opposing team OPS' },
  { key: 'opp_k_rate',   label: 'Opp K%',     title: 'Opposing team strikeout rate as batters' },
  { key: 'difficulty',   label: 'Difficulty', title: 'Matchup difficulty score (1=easiest, 10=hardest)' },
  { key: 'score',        label: 'Score',      title: 'Fantasy score for selected profile' },
]

function fmt(val, decimals = 2) {
  if (val == null) return <span className="rank-na">—</span>
  return typeof val === 'number' ? val.toFixed(decimals) : val
}

function fmtPct(val) {
  if (val == null) return <span className="rank-na">—</span>
  return `${(val * 100).toFixed(1)}%`
}

function DifficultyBadge({ value }) {
  if (value == null) return <span className="rank-na">—</span>
  const cls = value >= 7 ? 'diff-hard' : value >= 4 ? 'diff-medium' : 'diff-easy'
  return <span className={`diff-badge ${cls}`}>{value.toFixed(1)}</span>
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
    sortKey, sortDir, handleSort,
    refresh,
  } = useRankings()

  return (
    <div className="rankings-page">
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
        <button className="btn btn-ghost" onClick={refresh} disabled={loading} title="Refresh">
          <RefreshCw size={15} className={loading ? 'spin' : ''} />
          <span>Refresh</span>
        </button>
      </div>

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
                    title={col.title}
                    className={sortKey === col.key ? 'col--sorted' : ''}
                  >
                    <span className="th-inner">
                      {col.label}
                      <SortIcon colKey={col.key} sortKey={sortKey} sortDir={sortDir} />
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {pitchers.map((p, i) => (
                <tr key={`${p.player_id}-${p.game_date}`} className={i % 2 === 0 ? 'row-even' : 'row-odd'}>
                  <td className="col-rank">{p.rank}</td>
                  <td className="col-name">{p.name}</td>
                  <td className="col-team"><span className="team-pill">{p.team_abbrev}</span></td>
                  <td className="col-opp"><span className="team-pill team-pill--opp">{p.opp_team_abbrev}</span></td>
                  <td className="col-date">{p.game_date ? p.game_date.slice(5) : '—'}</td>
                  <td className={`col-stat ${p.era != null && p.era < 3.5 ? 'stat--good' : p.era != null && p.era > 4.5 ? 'stat--bad' : ''}`}>
                    {fmt(p.era)}
                  </td>
                  <td className={`col-stat ${p.whip != null && p.whip < 1.2 ? 'stat--good' : p.whip != null && p.whip > 1.4 ? 'stat--bad' : ''}`}>
                    {fmt(p.whip)}
                  </td>
                  <td className="col-stat">{fmt(p.k_per_9)}</td>
                  <td className="col-stat">{fmt(p.quality_starts, 0)}</td>
                  <td className="col-stat">{fmt(p.svh, 0)}</td>
                  <td className="col-stat">{fmt(p.opp_avg, 3)}</td>
                  <td className="col-stat">{fmt(p.opp_ops, 3)}</td>
                  <td className="col-stat">{fmtPct(p.opp_k_rate)}</td>
                  <td className="col-difficulty"><DifficultyBadge value={p.difficulty} /></td>
                  <td className="col-score"><strong>{p.score != null ? p.score.toFixed(1) : '—'}</strong></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
