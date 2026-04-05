import { GameCard } from './GameCard'

function formatDayHeading(dateStr) {
  const d = new Date(dateStr + 'T12:00:00')
  const today = new Date()
  today.setHours(12, 0, 0, 0)
  const tomorrow = new Date(today)
  tomorrow.setDate(today.getDate() + 1)

  const label =
    d.toDateString() === today.toDateString() ? 'Today' :
    d.toDateString() === tomorrow.toDateString() ? 'Tomorrow' :
    d.toLocaleDateString('en-US', { weekday: 'long' })

  const dateLabel = d.toLocaleDateString('en-US', { month: 'long', day: 'numeric' })
  return { label, dateLabel }
}

function groupByDate(games) {
  const map = new Map()
  for (const game of games) {
    if (!map.has(game.game_date)) map.set(game.game_date, [])
    map.get(game.game_date).push(game)
  }
  return [...map.entries()].sort(([a], [b]) => a.localeCompare(b))
}

function getGamePriority(game, scores) {
  const liveScore = scores[game.game_id]
  const status = liveScore?.status ?? game.status

  if (status === 'In Progress' || status === 'Live') return 0  // Active games first
  if (status === 'Final') return 2  // Final games last
  return 1  // Scheduled/Upcoming in the middle
}

function sortByStatus(dayGames, scores) {
  return [...dayGames].sort((a, b) => {
    const priorityA = getGamePriority(a, scores)
    const priorityB = getGamePriority(b, scores)
    if (priorityA !== priorityB) return priorityA - priorityB
    // Within same priority, sort by game_id
    return a.game_id.localeCompare(b.game_id)
  })
}

export function WeekView({ games, scores = {} }) {
  if (games.length === 0) {
    return (
      <div className="empty-state">
        <p className="empty-title">No games found</p>
        <p className="empty-sub">Try adjusting your filters or selecting a different week.</p>
      </div>
    )
  }

  const grouped = groupByDate(games)

  return (
    <div className="week-view">
      {grouped.map(([date, dayGames]) => {
        const { label, dateLabel } = formatDayHeading(date)
        const sortedGames = sortByStatus(dayGames, scores)
        return (
          <section key={date} className="day-section">
            <div className="day-heading">
              <span className="day-heading-label">{label}</span>
              <span className="day-heading-date">{dateLabel}</span>
              <span className="day-heading-count">{sortedGames.length} game{sortedGames.length !== 1 ? 's' : ''}</span>
            </div>
            <div className="game-grid">
              {sortedGames.map(game => (
                <GameCard key={game.game_id} game={game} liveScore={scores[game.game_id]} />
              ))}
            </div>
          </section>
        )
      })}
    </div>
  )
}
