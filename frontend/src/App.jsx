import { useState } from 'react'
import { Header } from './components/Header'
import { Filters } from './components/Filters'
import { WeekView } from './components/WeekView'
import { Rankings } from './pages/Rankings'
import { useWeek } from './hooks/useWeek'
import { useFilters } from './hooks/useFilters'
import { useTheme } from './hooks/useTheme'

const TABS = [
  { id: 'week',     label: 'Week View' },
  { id: 'rankings', label: 'Rankings' },
]

export default function App() {
  const [tab, setTab] = useState('week')
  const { data, loading, error, isCurrentWeek, goToPrevWeek, goToNextWeek, goToCurrentWeek, refresh } = useWeek()
  const { search, setSearch, selectedDate, setSelectedDate, hideTbd, setHideTbd, filtered, dates } = useFilters(data?.games ?? [])
  const { themeId, setThemeId } = useTheme()

  return (
    <div className="app">
      <Header
        data={data}
        loading={loading && tab === 'week'}
        isCurrentWeek={isCurrentWeek}
        onPrev={goToPrevWeek}
        onNext={goToNextWeek}
        onToday={goToCurrentWeek}
        onRefresh={refresh}
        showWeekNav={tab === 'week'}
        themeId={themeId}
        setThemeId={setThemeId}
      />

      <nav className="tab-nav">
        {TABS.map(t => (
          <button
            key={t.id}
            className={`tab-btn ${tab === t.id ? 'tab-btn--active' : ''}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <main className="app-main">
        {tab === 'week' && (
          <>
            {error && (
              <div className="error-banner">
                <strong>Could not load data.</strong> {error}
              </div>
            )}
            {!error && (
              <>
                <Filters
                  search={search} setSearch={setSearch}
                  selectedDate={selectedDate} setSelectedDate={setSelectedDate}
                  hideTbd={hideTbd} setHideTbd={setHideTbd}
                  dates={dates}
                  totalGames={data?.games?.length ?? 0}
                  filteredCount={filtered.length}
                />
                {loading
                  ? <div className="loading-grid">{Array.from({ length: 8 }).map((_, i) => <div key={i} className="game-card-skeleton" />)}</div>
                  : <WeekView games={filtered} />
                }
              </>
            )}
          </>
        )}
        {tab === 'rankings' && <Rankings />}
      </main>
    </div>
  )
}
