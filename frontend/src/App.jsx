import { useState } from 'react'
import { BrowserRouter, Routes, Route, useLocation, useNavigate } from 'react-router-dom'
import { Header } from './components/Header'
import { Filters } from './components/Filters'
import { WeekView } from './components/WeekView'
import { Rankings } from './pages/Rankings'
import { RelieverRankings } from './pages/RelieverRankings'
import { GameDetail } from './pages/GameDetail'
import { useWeek } from './hooks/useWeek'
import { useFilters } from './hooks/useFilters'
import { useTheme } from './hooks/useTheme'

const TABS = [
  { id: 'week',       label: 'Week View' },
  { id: 'starters',   label: 'Starters' },
  { id: 'relievers',  label: 'Relievers' },
]

function AppContent() {
  const location = useLocation()
  const navigate = useNavigate()
  const [tab, setTab] = useState('week')
  const { data, loading, error, isCurrentWeek, goToPrevWeek, goToNextWeek, goToCurrentWeek } = useWeek()
  const { search, setSearch, selectedDate, setSelectedDate, hideTbd, setHideTbd, filtered, dates } = useFilters(data?.games ?? [])
  const { themeId, setThemeId } = useTheme()

  const isGameDetail = location.pathname.startsWith('/game/')

  const handleTabClick = (tabId) => {
    setTab(tabId)
    if (tabId === 'week') navigate('/')
    else if (tabId === 'starters') navigate('/starters')
    else if (tabId === 'relievers') navigate('/relievers')
  }

  return (
    <div className="app">
      <Header
        data={data}
        isCurrentWeek={isCurrentWeek}
        onPrev={goToPrevWeek}
        onNext={goToNextWeek}
        onToday={goToCurrentWeek}
        showWeekNav={tab === 'week' && !isGameDetail}
        themeId={themeId}
        setThemeId={setThemeId}
      />

      {!isGameDetail && (
        <nav className="tab-nav">
          {TABS.map(t => (
            <button
              key={t.id}
              className={`tab-btn ${tab === t.id ? 'tab-btn--active' : ''}`}
              onClick={() => handleTabClick(t.id)}
            >
              {t.label}
            </button>
          ))}
        </nav>
      )}

      <main className="app-main">
        {tab === 'week' && !isGameDetail && (
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
        {tab === 'starters' && <Rankings />}
        {tab === 'relievers' && <RelieverRankings />}
      </main>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppContent />} />
        <Route path="/starters" element={<AppContent />} />
        <Route path="/relievers" element={<AppContent />} />
        <Route path="/game/:gameId" element={<GameDetail />} />
      </Routes>
    </BrowserRouter>
  )
}
