import { useState } from 'react'
import { useRelievers } from '../hooks/useRelievers'
import { RefreshCw, ArrowUp, ArrowDown, ArrowUpDown } from 'lucide-react'

const COLUMNS = [
  { key: 'rank',          label: '#',       title: 'Rank' },
  { key: 'team_abbrev',   label: 'Team',    title: 'Team' },
  { key: 'name',          label: 'Reliever', title: 'Reliever name' },
  { key: 'saves',         label: 'SV',      title: 'Saves' },
  { key: 'holds',         label: 'HLD',     title: 'Holds' },
  { key: 'svh',           label: 'SV+H',    title: 'Saves + Holds' },
  { key: 'k_pct',         label: 'K%',       title: 'Strikeout rate' },
  { key: 'bb_pct',        label: 'BB%',      title: 'Walk rate' },
  { key: 'k_minus_bb',    label: 'K%-BB%',  title: 'Strikeout rate minus walk rate' },
  { key: 'era',           label: 'ERA',     title: 'Earned Run Average' },
  { key: 'whip',          label: 'WHIP',    title: 'Walks + Hits per Inning Pitched' },
  { key: 'k_per_9',       label: 'K/9',     title: 'Strikeouts per 9 innings' },
  { key: 'xfip',          label: 'xFIP',    title: 'Expected FIP' },
  { key: 'siera',         label: 'SIERA',   title: 'SIERA' },
  { key: 'innings_pitched', label: 'IP',    title: 'Innings Pitched' },
]

function fmt(val, decimals = 2) {
  if (val == null) return <span className="rank-na">—</span>
  return typeof val === 'number' ? val.toFixed(decimals) : val
}

function fmtPct(val) {
  if (val == null) return <span className="rank-na">—</span>
  return `${(val * 100).toFixed(1)}%`
}

function SortIcon({ colKey, sortKey, sortDir }) {
  if (sortKey !== colKey) return <ArrowUpDown size={12} className="sort-icon sort-icon--inactive" />
  return sortDir === 'asc'
    ? <ArrowUp size={12} className="sort-icon" />
    : <ArrowDown size={12} className="sort-icon" />
}

export function RelieverRankings() {
  const {
    pitchers, loading, error,
    sortKey, sortDir, handleSort,
    refresh,
  } = useRelievers()

  return (
    <div className="rankings-page">

      {/* ── Toolbar row: refresh ── */}
      <div className="rankings-toolbar">
        <div className="rankings-profiles">
          <span className="profile-btn profile-btn--active">Bullpen Rankings</span>
        </div>
        <button className="btn btn-ghost" onClick={refresh} disabled={loading} title="Refresh">
          <RefreshCw size={15} className={loading ? 'spin' : ''} />
          <span>Refresh</span>
        </button>
      </div>

      {error && (
        <div className="error-banner"><strong>Could not load reliever rankings.</strong> {error}</div>
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
          No reliever data available yet.
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
                <tr key={`${p.name}-${p.team_abbrev}`} className={i % 2 === 0 ? 'row-even' : 'row-odd'}>
                  <td className="col-rank">{p.rank}</td>
                  <td className="col-team"><span className="team-pill">{p.team_abbrev}</span></td>
                  <td className="col-name">
                    {p.name}
                    {p.hand && <span className="pitcher-hand">{p.hand}</span>}
                  </td>
                  <td className="col-stat">{fmt(p.saves, 0)}</td>
                  <td className="col-stat">{fmt(p.holds, 0)}</td>
                  <td className="col-stat"><strong>{fmt(p.svh, 0)}</strong></td>
                  <td className="col-stat">{fmtPct(p.k_pct)}</td>
                  <td className="col-stat">{fmtPct(p.bb_pct)}</td>
                  <td className="col-stat">{fmtPct(p.k_minus_bb)}</td>
                  <td className={`col-stat ${p.era != null && p.era < 3.0 ? 'stat--good' : p.era != null && p.era > 4.5 ? 'stat--bad' : ''}`}>
                    {fmt(p.era)}
                  </td>
                  <td className={`col-stat ${p.whip != null && p.whip < 1.2 ? 'stat--good' : p.whip != null && p.whip > 1.5 ? 'stat--bad' : ''}`}>
                    {fmt(p.whip)}
                  </td>
                  <td className="col-stat">{fmt(p.k_per_9)}</td>
                  <td className="col-stat">{fmt(p.xfip)}</td>
                  <td className="col-stat">{fmt(p.siera)}</td>
                  <td className="col-stat">{fmt(p.innings_pitched, 1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
