import { ChevronLeft, ChevronRight, RefreshCw } from 'lucide-react'

function formatWeekRange(startDate, endDate) {
  if (!startDate || !endDate) return ''
  const fmt = (d) => new Date(d + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  const endYear = new Date(endDate + 'T12:00:00').getFullYear()
  return `${fmt(startDate)} – ${fmt(endDate)}, ${endYear}`
}

export function Header({ data, loading, isCurrentWeek, onPrev, onNext, onToday, onRefresh }) {
  return (
    <header className="app-header">
      <div className="header-top">
        <div className="header-brand">
          <span className="header-logo">⚾</span>
          <div>
            <h1 className="header-title">Probable Pitchers</h1>
            <p className="header-subtitle">Fantasy Baseball Week Planner</p>
          </div>
        </div>
        <button
          className="btn btn-ghost"
          onClick={onRefresh}
          disabled={loading}
          title="Refresh data"
        >
          <RefreshCw size={16} className={loading ? 'spin' : ''} />
          <span>Refresh</span>
        </button>
      </div>

      <div className="week-nav">
        <button className="btn btn-icon" onClick={onPrev} title="Previous week">
          <ChevronLeft size={18} />
        </button>
        <div className="week-nav-center">
          <span className="week-range">
            {data ? formatWeekRange(data.start_date, data.end_date) : '—'}
          </span>
          {!isCurrentWeek && (
            <button className="btn btn-small" onClick={onToday}>
              This week
            </button>
          )}
        </div>
        <button className="btn btn-icon" onClick={onNext} title="Next week">
          <ChevronRight size={18} />
        </button>
      </div>
    </header>
  )
}
