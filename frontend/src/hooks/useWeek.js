import { useState, useEffect, useCallback } from 'react'
import { fetchWeek, getCachedData } from '../api/client'

const PREFETCH_TTL_MS = 10 * 60 * 1000 // 10 minutes

function getMondayISO(date = new Date()) {
  const d = new Date(date)
  const day = d.getDay()
  const diff = day === 0 ? -6 : 1 - day
  d.setDate(d.getDate() + diff)
  return d.toISOString().split('T')[0]
}

export function useWeek() {
  const [weekStart, setWeekStart] = useState(() => getMondayISO())
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async (startDate, force = false) => {
    setLoading(true)
    setError(null)
    try {
      const result = await fetchWeek(startDate, force)
      setData(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  // Check cache on mount first
  useEffect(() => {
    const cacheKey = `week:${weekStart}`
    const cached = getCachedData(cacheKey, PREFETCH_TTL_MS)

    if (cached) {
      setData(cached)
      setLoading(false)
    } else {
      load(weekStart)
    }
  }, []) // Only run once on mount

  // Reload when week changes (but check cache first)
  useEffect(() => {
    const cacheKey = `week:${weekStart}`
    const cached = getCachedData(cacheKey, PREFETCH_TTL_MS)

    if (cached) {
      setData(cached)
      setLoading(false)
    } else {
      load(weekStart)
    }
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
    refresh: () => load(weekStart, true),
  }
}
