import { Header } from './components/Header'
import { Filters } from './components/Filters'
import { WeekView } from './components/WeekView'
import { useWeek } from './hooks/useWeek'
import { useFilters } from './hooks/useFilters'

export default function App() {
  const { data, loading, error, isCurrentWeek, goToPrevWeek, goToNextWeek, goToCurrentWeek, refresh } = useWeek()
  const { search, setSearch, selectedDate, setSelectedDate, hideTbd, setHideTbd, filtered, dates } = useFilters(data?.games ?? [])

  return (
    <div className="app">
      <Header
        data={data}
        loading={loading}
        isCurrentWeek={isCurrentWeek}
        onPrev={goToPrevWeek}
        onNext={goToNextWeek}
        onToday={goToCurrentWeek}
        onRefresh={refresh}
      />

      <main className="app-main">
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
      </main>
    </div>
  )
}
