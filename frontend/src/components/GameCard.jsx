function PitcherLine({ pitcher, side, qs }) {
  const isTbd = !pitcher?.name || pitcher.name === 'TBD'
  return (
    <div className={`pitcher-line pitcher-${side}`}>
      <span className="pitcher-role">{side === 'away' ? 'Away' : 'Home'}</span>
      <span className={`pitcher-name ${isTbd ? 'pitcher-tbd' : ''}`}>
        {isTbd ? 'TBD' : pitcher.name}
      </span>
      {pitcher?.hand && <span className="pitcher-hand">{pitcher.hand}</span>}
      {qs === true && <span className="qs-badge" title="Quality Start">QS</span>}
      {qs === false && <span className="no-qs-badge" title="No Quality Start">-</span>}
    </div>
  )
}

function formatTime(gameTime) {
  if (!gameTime) return null
  try {
    const d = new Date(gameTime)
    return d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', timeZoneName: 'short' })
  } catch {
    return null
  }
}

import { Link } from 'react-router-dom'

function GameLinks({ gameId }) {
  const mlbUrl = `https://www.mlb.com/gameday/${gameId}/final/box`
  const savantUrl = `https://baseballsavant.mlb.com/gamefeed?gamePk=${gameId}`
  const fgUrl = `https://www.fangraphs.com/boxscore.aspx?gameid=${gameId}`

  return (
    <div className="game-links">
      <Link to={`/game/${gameId}`} title="Matchup Splits">Splits</Link>
      <a href={mlbUrl} target="_blank" rel="noopener noreferrer" title="MLB.com Boxscore">MLB</a>
      <a href={savantUrl} target="_blank" rel="noopener noreferrer" title="Baseball Savant">Savant</a>
      <a href={fgUrl} target="_blank" rel="noopener noreferrer" title="FanGraphs">FG</a>
    </div>
  )
}

export function GameCard({ game, liveScore }) {
  const time = formatTime(game.game_time)
  const bothTbd = game.away_pitcher?.name === 'TBD' && game.home_pitcher?.name === 'TBD'

  // Use live score if available, otherwise use cached score
  const awayScore = liveScore?.away_score ?? game.away_score
  const homeScore = liveScore?.home_score ?? game.home_score
  const status = liveScore?.status ?? game.status
  const currentInning = liveScore?.current_inning ?? game.current_inning
  const inningState = liveScore?.inning_state ?? game.inning_state

  const hasScore = awayScore != null && homeScore != null
  const isLive = status === 'In Progress' || status === 'Live'
  const isFinal = status === 'Final'
  const isDelayed = status === 'Delayed' || status === 'Suspended'

  return (
    <div className={`game-card ${bothTbd ? 'game-card-tbd' : ''}`}>
      <div className="game-card-header">
        <div className="matchup">
          <span className="team-abbrev">{game.away_team_abbrev}</span>
          <span className="matchup-at">@</span>
          <span className="team-abbrev">{game.home_team_abbrev}</span>
        </div>
        <div className="game-meta">
          {hasScore && (
            <span className={`game-score ${isLive ? 'game-score-live' : ''}`}>
              {awayScore} - {homeScore}
            </span>
          )}
          {time && !hasScore && <span className="game-time">{time}</span>}
          {isLive && currentInning && (
            <span className="game-inning">
              {inningState === 'Top' ? '↑ ' : inningState === 'Bottom' ? '↓ ' : ''}{currentInning}
            </span>
          )}
          {isDelayed && <span className="game-inning game-inning-delayed">{status}</span>}
          {!isLive && !isDelayed && status && !hasScore && <span className="game-status">{status}</span>}
        </div>
      </div>

      <div className="game-card-teams">
        <span className="team-full">{game.away_team}</span>
        <span className="team-vs">vs</span>
        <span className="team-full">{game.home_team}</span>
      </div>

      <div className="game-card-pitchers">
        <PitcherLine pitcher={game.away_pitcher} side="away" qs={game.away_qs} />
        <div className="pitcher-divider" />
        <PitcherLine pitcher={game.home_pitcher} side="home" qs={game.home_qs} />
      </div>

      {(hasScore || isFinal) && <GameLinks gameId={game.game_id} />}
    </div>
  )
}
