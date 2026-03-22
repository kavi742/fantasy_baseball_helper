import { Search, X } from 'lucide-react'

function formatDayTab(dateStr) {
  const d = new Date(dateStr + 'T12:00:00')
  return {
    day: d.toLocaleDateString('en-US', { weekday: 'short' }),
    date: d.toLocaleDateString('en-US', { month: 'numeric', day: 'numeric' }),
  }
}

export function Filters({ search, setSearch, selectedDate, setSelectedDate, hideTbd, setHideTbd, dates, totalGames, filteredCount }) {
  return (
    <div className="filters">
      <div className="filters-row">
        {/* Search */}
        <div className="search-wrap">
          <Search size={14} className="search-icon" />
          <input
            className="search-input"
            type="text"
            placeholder="Search team or pitcher…"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
          {search && (
            <button className="search-clear" onClick={() => setSearch('')}>
              <X size={12} />
            </button>
          )}
        </div>

        {/* TBD toggle */}
        <label className="toggle-label">
          <span>Hide TBD</span>
          <div
            className={`toggle ${hideTbd ? 'toggle-on' : ''}`}
            onClick={() => setHideTbd(v => !v)}
            role="switch"
            aria-checked={hideTbd}
          >
            <div className="toggle-thumb" />
          </div>
        </label>

        {/* Game count */}
        <span className="game-count">
          {filteredCount === totalGames
            ? `${totalGames} games`
            : `${filteredCount} of ${totalGames} games`}
        </span>
      </div>

      {/* Day tabs */}
      {dates.length > 0 && (
        <div className="day-tabs">
          <button
            className={`day-tab ${selectedDate === null ? 'day-tab-active' : ''}`}
            onClick={() => setSelectedDate(null)}
          >
            All days
          </button>
          {dates.map(date => {
            const { day, date: dateLabel } = formatDayTab(date)
            return (
              <button
                key={date}
                className={`day-tab ${selectedDate === date ? 'day-tab-active' : ''}`}
                onClick={() => setSelectedDate(date === selectedDate ? null : date)}
              >
                <span className="day-tab-day">{day}</span>
                <span className="day-tab-date">{dateLabel}</span>
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
