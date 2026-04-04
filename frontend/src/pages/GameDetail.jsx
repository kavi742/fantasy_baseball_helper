import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { fetchGame } from '../api/client'

function formatStat(val, decimals = 3) {
  if (val === null || val === undefined) return '—'
  if (typeof val === 'number') return val.toFixed(decimals)
  return val
}

function formatPA(pa) {
  if (!pa) return '—'
  return pa
}

function StatCell({ label, value, highlight }) {
  return (
    <td className={`stat-cell ${highlight ? 'stat-highlight' : ''}`}>
      <span className="stat-value">{value}</span>
    </td>
  )
}

function BatterRow({ batter, pitcherHand }) {
  const favorable = batter.favorable_split
  const splits = batter.splits || {}
  const season = batter.season_stats || {}

  return (
    <tr className={favorable ? 'favorable-matchup' : ''}>
      <td className="batter-name-cell">
        <div className="batter-name">
          <span className="batter-position">{batter.position}</span>
          <span className="batter-full-name">{batter.name}</span>
          {batter.bat_hand && <span className="bat-hand">{batter.bat_hand}</span>}
        </div>
        {favorable && <span className="matchup-badge">↑ Favorable</span>}
      </td>
      <td className="stat-cell"> <span className="stat-value">{formatPA(season.pa)}</span> </td>
      <td className="stat-cell"> <span className="stat-value">{formatStat(season.avg)}</span> </td>
      <td className="stat-cell"> <span className="stat-value">{formatStat(season.obp)}</span> </td>
      <td className="stat-cell stat-highlight"> <span className="stat-value">{formatStat(season.ops)}</span> </td>
      {pitcherHand === 'L' ? (
        <>
          <td className="stat-cell stat-highlight-col"> <span className="stat-value">{formatPA(splits.vs_lhp?.pa)}</span> </td>
          <td className="stat-cell stat-highlight-col"> <span className="stat-value">{formatStat(splits.vs_lhp?.avg)}</span> </td>
          <td className="stat-cell stat-highlight-col"> <span className="stat-value">{formatStat(splits.vs_lhp?.obp)}</span> </td>
          <td className="stat-cell stat-highlight-col"> <span className="stat-value">{formatStat(splits.vs_lhp?.ops)}</span> </td>
          <td className="stat-cell dim-col"> <span className="stat-value">{formatPA(splits.vs_rhp?.pa)}</span> </td>
          <td className="stat-cell dim-col"> <span className="stat-value">{formatStat(splits.vs_rhp?.avg)}</span> </td>
          <td className="stat-cell dim-col"> <span className="stat-value">{formatStat(splits.vs_rhp?.obp)}</span> </td>
          <td className="stat-cell dim-col"> <span className="stat-value">{formatStat(splits.vs_rhp?.ops)}</span> </td>
        </>
      ) : (
        <>
          <td className="stat-cell dim-col"> <span className="stat-value">{formatPA(splits.vs_lhp?.pa)}</span> </td>
          <td className="stat-cell dim-col"> <span className="stat-value">{formatStat(splits.vs_lhp?.avg)}</span> </td>
          <td className="stat-cell dim-col"> <span className="stat-value">{formatStat(splits.vs_lhp?.obp)}</span> </td>
          <td className="stat-cell dim-col"> <span className="stat-value">{formatStat(splits.vs_lhp?.ops)}</span> </td>
          <td className="stat-cell stat-highlight-col"> <span className="stat-value">{formatPA(splits.vs_rhp?.pa)}</span> </td>
          <td className="stat-cell stat-highlight-col"> <span className="stat-value">{formatStat(splits.vs_rhp?.avg)}</span> </td>
          <td className="stat-cell stat-highlight-col"> <span className="stat-value">{formatStat(splits.vs_rhp?.obp)}</span> </td>
          <td className="stat-cell stat-highlight-col"> <span className="stat-value">{formatStat(splits.vs_rhp?.ops)}</span> </td>
        </>
      )}
    </tr>
  )
}

function TeamSection({ teamName, abbrev, pitcher, batters, pitcherHand }) {
  return (
    <div className="team-section">
      <div className="team-header">
        <h2>{teamName}</h2>
        <div className="probable-pitcher">
          <span className="pitcher-label">Opposing Pitcher:</span>
          <span className="pitcher-name">
            {pitcher?.name || 'TBD'}
            {pitcher?.hand && <span className="pitcher-hand">{pitcher.hand}</span>}
          </span>
        </div>
      </div>

      <div className="batters-table-wrapper">
        <table className="batters-table">
          <thead>
            <tr>
              <th className="batter-col">Batter</th>
              <th colSpan="4" className="season-header">Season Stats</th>
              <th colSpan="4" className={`split-header ${pitcherHand === 'L' ? 'split-header-active' : 'split-header-dim'}`}>vs LHP</th>
              <th colSpan="4" className={`split-header ${pitcherHand === 'R' ? 'split-header-active' : 'split-header-dim'}`}>vs RHP</th>
            </tr>
            <tr className="sub-header">
              <th></th>
              <th>PA</th>
              <th>AVG</th>
              <th>OBP</th>
              <th className="highlight-col">OPS</th>
              <th className={pitcherHand === 'L' ? 'col-active' : 'col-dim'}>PA</th>
              <th className={pitcherHand === 'L' ? 'col-active' : 'col-dim'}>AVG</th>
              <th className={pitcherHand === 'L' ? 'col-active' : 'col-dim'}>OBP</th>
              <th className={pitcherHand === 'L' ? 'col-active' : 'col-dim'}>OPS</th>
              <th className={pitcherHand === 'R' ? 'col-active' : 'col-dim'}>PA</th>
              <th className={pitcherHand === 'R' ? 'col-active' : 'col-dim'}>AVG</th>
              <th className={pitcherHand === 'R' ? 'col-active' : 'col-dim'}>OBP</th>
              <th className={pitcherHand === 'R' ? 'col-active' : 'col-dim'}>OPS</th>
            </tr>
          </thead>
          <tbody>
            {batters.length === 0 ? (
              <tr>
                <td colSpan="12" className="no-data">No lineup data available</td>
              </tr>
            ) : (
              batters.map((batter, idx) => (
                <BatterRow
                  key={batter.id || idx}
                  batter={batter}
                  pitcherHand={pitcherHand}
                />
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export function GameDetail() {
  const { gameId } = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    fetchGame(gameId)
      .then(setData)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [gameId])

  if (loading) {
    return (
      <div className="game-detail-loading">
        <div className="loading-spinner" />
        <p>Loading game details...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="game-detail-error">
        <h2>Error</h2>
        <p>{error}</p>
        <Link to="/" className="back-link">← Back to Week View</Link>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="game-detail">
      <div className="game-detail-header">
        <Link to="/" className="back-link">← Back to Week View</Link>
        <div className="game-title">
          <span className="team">{data.away_abbrev}</span>
          <span className="at">@</span>
          <span className="team">{data.home_abbrev}</span>
          {data.away_score != null && data.home_score != null && (
            <span className="score">{data.away_score} - {data.home_score}</span>
          )}
        </div>
        <div className="game-meta">
          <span>{data.game_date}</span>
          {data.status && <span className="status">{data.status}</span>}
        </div>
      </div>

      <div className="game-links">
        <a
          href={`https://www.mlb.com/gameday/${gameId}/final/box`}
          target="_blank"
          rel="noopener noreferrer"
        >
          MLB
        </a>
        <a
          href={`https://baseballsavant.mlb.com/gamefeed?gamePk=${gameId}`}
          target="_blank"
          rel="noopener noreferrer"
        >
          Savant
        </a>
        <a
          href={`https://www.fangraphs.com/boxscore.aspx?gameid=${gameId}`}
          target="_blank"
          rel="noopener noreferrer"
        >
          FG
        </a>
      </div>

      <div className="splits-info">
        <p>
          <strong>Platoon Advantage:</strong> Batters highlighted in green have favorable splits
          against the opposing pitcher's handedness. Look at the vs LHP / vs RHP columns
          to see how each batter performs against lefties vs righties.
        </p>
      </div>

      <TeamSection
        teamName={data.away_team}
        abbrev={data.away_abbrev}
        pitcher={data.home_pitcher}
        batters={data.away_batters}
        pitcherHand={data.home_pitcher?.hand}
      />

      <TeamSection
        teamName={data.home_team}
        abbrev={data.home_abbrev}
        pitcher={data.away_pitcher}
        batters={data.home_batters}
        pitcherHand={data.away_pitcher?.hand}
      />
    </div>
  )
}
