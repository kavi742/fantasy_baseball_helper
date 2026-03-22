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

export function WeekView({ games }) {
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
        return (
          <section key={date} className="day-section">
            <div className="day-heading">
              <span className="day-heading-label">{label}</span>
              <span className="day-heading-date">{dateLabel}</span>
              <span className="day-heading-count">{dayGames.length} game{dayGames.length !== 1 ? 's' : ''}</span>
            </div>
            <div className="game-grid">
              {dayGames.map(game => (
                <GameCard key={game.game_id} game={game} />
              ))}
            </div>
          </section>
        )
      })}
    </div>
  )
}
