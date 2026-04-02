import { useState, useEffect, useCallback } from 'react'
import { fetchRankings } from '../api/client'

function getMondayISO(offsetWeeks = 0) {
  const d = new Date()
  const day = d.getDay()
  const diff = day === 0 ? -6 : 1 - day
  d.setDate(d.getDate() + diff + offsetWeeks * 7)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

export function useRankings() {
  const [profile, setProfile] = useState('balanced')
  const [week, setWeek] = useState('current')  // 'current' | 'next'
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [sortKey, setSortKey] = useState('rank')
  const [sortDir, setSortDir] = useState('asc')

  const load = useCallback(async (p, w) => {
    setLoading(true)
    setError(null)
    try {
      const weekStart = getMondayISO(w === 'next' ? 1 : 0)
      const result = await fetchRankings(p, weekStart)
      setData(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load(profile, week)
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
    refresh: () => load(profile, week),
  }
}
