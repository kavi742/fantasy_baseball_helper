import { useState, useEffect, useCallback } from 'react'
import { fetchRankings, getCachedData } from '../api/client'

function getMondayISO(offsetWeeks = 0) {
  const d = new Date()
  const day = d.getDay()
  const diff = day === 0 ? -6 : 1 - day
  d.setDate(d.getDate() + diff + offsetWeeks * 7)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function getTodayISO() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function getTomorrowISO() {
  const d = new Date()
  d.setDate(d.getDate() + 1)
  return d.toISOString().split('T')[0]
}

const PREFETCH_TTL_MS = 10 * 60 * 1000 // 10 minutes

function buildCacheKey(profile, weekStart) {
  return `rankings:${profile}:${weekStart || 'current'}`
}

function getWeekStart(w) {
  if (w === 'today') return getTodayISO()
  if (w === 'tomorrow') return getTomorrowISO()
  if (w === 'current') return getMondayISO()
  return getMondayISO(1)
}

export function useRankings() {
  const [profile, setProfile] = useState('balanced')
  const [week, setWeek] = useState('tomorrow')  // 'today' | 'current' | 'next' | 'tomorrow'
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [sortKey, setSortKey] = useState('rank')
  const [sortDir, setSortDir] = useState('asc')

  const load = useCallback(async (p, w, force = false) => {
    setLoading(true)
    setError(null)
    try {
      const weekStart = getWeekStart(w)
      const result = await fetchRankings(p, weekStart, force)
      setData(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  // Check cache on mount before loading
  useEffect(() => {
    const weekStart = getWeekStart(week)
    const cacheKey = buildCacheKey(profile, weekStart)
    const cached = getCachedData(cacheKey, PREFETCH_TTL_MS)
    
    if (cached) {
      setData(cached)
      setLoading(false)
    } else {
      load(profile, week)
    }
  }, []) // Only run once on mount

  // Reload when profile or week changes
  useEffect(() => {
    const weekStart = getWeekStart(week)
    const cacheKey = buildCacheKey(profile, weekStart)
    const cached = getCachedData(cacheKey, PREFETCH_TTL_MS)
    
    if (cached) {
      setData(cached)
      setLoading(false)
    } else {
      load(profile, week)
    }
  }, [profile, week, load])

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDir(['rank', 'name', 'team', 'game_date', 'difficulty'].includes(key) ? 'asc' : 'desc')
    }
  }

  const sorted = data?.pitchers ? [...data.pitchers].sort((a, b) => {
    const av = a[sortKey] ?? (sortDir === 'asc' ? Infinity : -Infinity)
    const bv = b[sortKey] ?? (sortDir === 'asc' ? Infinity : -Infinity)
    if (av < bv) return sortDir === 'asc' ? -1 : 1
    if (av > bv) return sortDir === 'asc' ? 1 : -1
    return 0
  }) : []

  return {
    data,
    pitchers: sorted,
    profiles: data?.profiles ?? [],
    loading,
    error,
    profile,
    setProfile,
    week,
    setWeek,
    sortKey,
    sortDir,
    handleSort,
    refresh: () => load(profile, week, true),
  }
}
