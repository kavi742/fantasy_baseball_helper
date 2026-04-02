function PitcherLine({ pitcher, side, qs }) {
  const isTbd = !pitcher?.name || pitcher.name === 'TBD'
  return (
    <div className={`pitcher-line pitcher-${side}`}>
      <span className="pitcher-role">{side === 'away' ? 'Away' : 'Home'}</span>
      <span className={`pitcher-name ${isTbd ? 'pitcher-tbd' : ''}`}>
        {isTbd ? 'TBD' : pitcher.name}
      </span>
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

function GameLinks({ gameId }) {
  const mlbUrl = `https://www.mlb.com/gameday/${gameId}/final/box`
  const savantUrl = `https://baseballsavant.mlb.com/gamefeed?gamePk=${gameId}`
  const fgUrl = `https://www.fangraphs.com/boxscore.aspx?gameid=${gameId}`

  return (
    <div className="game-links">
      <a href={mlbUrl} target="_blank" rel="noopener noreferrer" title="MLB.com Boxscore">MLB</a>
      <a href={savantUrl} target="_blank" rel="noopener noreferrer" title="Baseball Savant">Savant</a>
      <a href={fgUrl} target="_blank" rel="noopener noreferrer" title="FanGraphs">FG</a>
    </div>
  )
}

export function GameCard({ game }) {
  const time = formatTime(game.game_time)
  const bothTbd = game.away_pitcher?.name === 'TBD' && game.home_pitcher?.name === 'TBD'
  const hasScore = game.away_score != null && game.home_score != null
  const isLive = game.status === 'In Progress' || game.status === 'Live'
  const isFinal = game.status === 'Final'

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
              {game.away_score} - {game.home_score}
            </span>
          )}
          {time && !hasScore && <span className="game-time">{time}</span>}
          {isLive && <span className="game-inning">{'Top'.length > 0 ? '' : ''}</span>}
          {!isLive && game.status && !hasScore && <span className="game-status">{game.status}</span>}
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
