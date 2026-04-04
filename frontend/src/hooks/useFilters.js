import { useState, useMemo } from 'react'

export function useFilters(games = []) {
  const today = new Date().toISOString().split('T')[0]

  // Get unique dates from games
  const dates = useMemo(() => {
    const seen = new Set()
    return games
      .map(g => g.game_date)
      .filter(d => { if (seen.has(d)) return false; seen.add(d); return true })
      .sort()
  }, [games])

  // Default to today if available, otherwise null (all days)
  const defaultDate = dates.includes(today) ? today : null

  const [search, setSearch] = useState('')
  const [selectedDate, setSelectedDate] = useState(defaultDate)
  const [hideTbd, setHideTbd] = useState(false)

  const filtered = useMemo(() => {
    let result = games

    if (selectedDate) {
      result = result.filter(g => g.game_date === selectedDate)
    }

    if (search.trim()) {
      const q = search.trim().toLowerCase()
      result = result.filter(g =>
        g.away_team.toLowerCase().includes(q) ||
        g.home_team.toLowerCase().includes(q) ||
        (g.away_pitcher?.name || '').toLowerCase().includes(q) ||
        (g.home_pitcher?.name || '').toLowerCase().includes(q)
      )
    }

    if (hideTbd) {
      result = result.filter(g =>
        g.away_pitcher?.name !== 'TBD' && g.home_pitcher?.name !== 'TBD'
      )
    }

    return result
  }, [games, search, selectedDate, hideTbd])

  return {
    search, setSearch,
    selectedDate, setSelectedDate,
    hideTbd, setHideTbd,
    filtered,
    dates,
  }
}
