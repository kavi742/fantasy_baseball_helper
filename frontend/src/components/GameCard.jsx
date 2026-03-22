function PitcherLine({ pitcher, side }) {
  const isTbd = !pitcher?.name || pitcher.name === 'TBD'
  return (
    <div className={`pitcher-line pitcher-${side}`}>
      <span className="pitcher-role">{side === 'away' ? 'Away' : 'Home'}</span>
      <span className={`pitcher-name ${isTbd ? 'pitcher-tbd' : ''}`}>
        {isTbd ? 'TBD' : pitcher.name}
      </span>
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

export function GameCard({ game }) {
  const time = formatTime(game.game_time)
  const bothTbd = game.away_pitcher?.name === 'TBD' && game.home_pitcher?.name === 'TBD'

  return (
    <div className={`game-card ${bothTbd ? 'game-card-tbd' : ''}`}>
      <div className="game-card-header">
        <div className="matchup">
          <span className="team-abbrev">{game.away_team_abbrev}</span>
          <span className="matchup-at">@</span>
          <span className="team-abbrev">{game.home_team_abbrev}</span>
        </div>
        {time && <span className="game-time">{time}</span>}
      </div>

      <div className="game-card-teams">
        <span className="team-full">{game.away_team}</span>
        <span className="team-vs">vs</span>
        <span className="team-full">{game.home_team}</span>
      </div>

      <div className="game-card-pitchers">
        <PitcherLine pitcher={game.away_pitcher} side="away" />
        <div className="pitcher-divider" />
        <PitcherLine pitcher={game.home_pitcher} side="home" />
      </div>
    </div>
  )
}
