import { useState } from 'react'
import { useRelievers } from '../hooks/useRelievers'
import { useColumnResize } from '../hooks/useColumnResize'
import { RefreshCw, ArrowUp, ArrowDown, ArrowUpDown } from 'lucide-react'

const COLUMNS = [
  { key: 'rank',          label: '#',       title: 'Rank',            defaultWidth: 40 },
  { key: 'team_abbrev',   label: 'Team',    title: 'Team',            defaultWidth: 60 },
  { key: 'name',          label: 'Reliever', title: 'Reliever name',   defaultWidth: 150 },
  { key: 'hand',          label: 'Throws',   title: 'Throwing hand',   defaultWidth: 50 },
  { key: 'saves',         label: 'SV',      title: 'Saves',           defaultWidth: 50 },
  { key: 'holds',         label: 'HLD',     title: 'Holds',           defaultWidth: 50 },
  { key: 'svh',           label: 'SV+H',    title: 'Saves + Holds',   defaultWidth: 55 },
  { key: 'k_pct',         label: 'K%',       title: 'Strikeout rate',  defaultWidth: 55 },
  { key: 'bb_pct',        label: 'BB%',      title: 'Walk rate',       defaultWidth: 55 },
  { key: 'k_minus_bb',    label: 'K%-BB%',  title: 'Strikeout rate minus walk rate', defaultWidth: 70 },
  { key: 'era',           label: 'ERA',     title: 'Earned Run Average', defaultWidth: 60 },
  { key: 'whip',          label: 'WHIP',    title: 'Walks + Hits per Inning Pitched', defaultWidth: 60 },
  { key: 'k_per_9',       label: 'K/9',     title: 'Strikeouts per 9 innings', defaultWidth: 60 },
  { key: 'xfip',          label: 'xFIP',    title: 'Expected FIP',    defaultWidth: 60 },
  { key: 'siera',         label: 'SIERA',   title: 'SIERA',          defaultWidth: 60 },
  { key: 'innings_pitched', label: 'IP',    title: 'Innings Pitched', defaultWidth: 60 },
]

const DEFAULT_WIDTHS = Object.fromEntries(COLUMNS.map(c => [c.key, c.defaultWidth]))

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

  const { getWidth, startResize, resetWidth } = useColumnResize(
    COLUMNS.map(c => c.key),
    DEFAULT_WIDTHS
  )

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
              {pitchers.map((p, i) => (
                <tr key={`${p.name}-${p.team_abbrev}`} className={i % 2 === 0 ? 'row-even' : 'row-odd'}>
                  <td className="col-rank" style={{ width: getWidth('rank'), minWidth: 40 }}>{p.rank}</td>
                  <td className="col-team" style={{ width: getWidth('team_abbrev'), minWidth: 40 }}><span className="team-pill">{p.team_abbrev}</span></td>
                  <td className="col-name" style={{ width: getWidth('name'), minWidth: 80 }}>{p.name}</td>
                  <td className="col-hand" style={{ width: getWidth('hand'), minWidth: 40 }}>{p.hand || '—'}</td>
                  <td className="col-stat" style={{ width: getWidth('saves'), minWidth: 40 }}>{fmt(p.saves, 0)}</td>
                  <td className="col-stat" style={{ width: getWidth('holds'), minWidth: 40 }}>{fmt(p.holds, 0)}</td>
                  <td className="col-stat" style={{ width: getWidth('svh'), minWidth: 50 }}><strong>{fmt(p.svh, 0)}</strong></td>
                  <td className="col-stat" style={{ width: getWidth('k_pct'), minWidth: 50 }}>{fmtPct(p.k_pct)}</td>
                  <td className="col-stat" style={{ width: getWidth('bb_pct'), minWidth: 50 }}>{fmtPct(p.bb_pct)}</td>
                  <td className="col-stat" style={{ width: getWidth('k_minus_bb'), minWidth: 60 }}>{fmtPct(p.k_minus_bb)}</td>
                  <td className={`col-stat ${p.era != null && p.era < 3.0 ? 'stat--good' : p.era != null && p.era > 4.5 ? 'stat--bad' : ''}`} style={{ width: getWidth('era'), minWidth: 50 }}>
                    {fmt(p.era)}
                  </td>
                  <td className={`col-stat ${p.whip != null && p.whip < 1.2 ? 'stat--good' : p.whip != null && p.whip > 1.5 ? 'stat--bad' : ''}`} style={{ width: getWidth('whip'), minWidth: 50 }}>
                    {fmt(p.whip)}
                  </td>
                  <td className="col-stat" style={{ width: getWidth('k_per_9'), minWidth: 50 }}>{fmt(p.k_per_9)}</td>
                  <td className="col-stat" style={{ width: getWidth('xfip'), minWidth: 50 }}>{fmt(p.xfip)}</td>
                  <td className="col-stat" style={{ width: getWidth('siera'), minWidth: 50 }}>{fmt(p.siera)}</td>
                  <td className="col-stat" style={{ width: getWidth('innings_pitched'), minWidth: 50 }}>{fmt(p.innings_pitched, 1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
