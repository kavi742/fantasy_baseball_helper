import { useState, useEffect, useCallback } from 'react'
import { fetchWeek } from '../api/client'

function getTodayISO() {
  const d = new Date()
  return d.toISOString().split('T')[0]
}

function getMondayISO(date = new Date()) {
  const d = new Date(date)
  const day = d.getDay()
  const diff = day === 0 ? -6 : 1 - day  // Sunday wraps to previous Monday
  d.setDate(d.getDate() + diff)
  return d.toISOString().split('T')[0]
}

export function useWeek() {
  const [weekStart, setWeekStart] = useState(() => getMondayISO())
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async (startDate) => {
    setLoading(true)
    setError(null)
    try {
      const result = await fetchWeek(startDate)
      setData(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load(weekStart)
  }, [weekStart, load])

  const goToPrevWeek = () => {
    const d = new Date(weekStart)
    d.setDate(d.getDate() - 7)
    setWeekStart(d.toISOString().split('T')[0])
  }

  const goToNextWeek = () => {
    const d = new Date(weekStart)
    d.setDate(d.getDate() + 7)
    setWeekStart(d.toISOString().split('T')[0])
  }

  const goToCurrentWeek = () => {
    setWeekStart(getMondayISO())
  }

  const isCurrentWeek = weekStart === getMondayISO()

  return {
    data,
    loading,
    error,
    weekStart,
    isCurrentWeek,
    goToPrevWeek,
    goToNextWeek,
    goToCurrentWeek,
    refresh: () => load(weekStart),
  }
}
