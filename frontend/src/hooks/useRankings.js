import { useState, useEffect, useCallback } from 'react'
import { fetchRankings } from '../api/client'

export function useRankings() {
  const [profile, setProfile] = useState('balanced')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [sortKey, setSortKey] = useState('rank')
  const [sortDir, setSortDir] = useState('asc')

  const load = useCallback(async (p) => {
    setLoading(true)
    setError(null)
    try {
      const result = await fetchRankings(p)
      setData(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load(profile)
  }, [profile, load])

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      // For rank/name: asc by default. For stats: desc (higher = better)
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
    sortKey,
    sortDir,
    handleSort,
    refresh: () => load(profile),
  }
}
