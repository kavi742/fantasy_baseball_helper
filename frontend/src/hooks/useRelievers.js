import { useState, useEffect, useCallback } from 'react'
import { fetchRelievers, getCachedData } from '../api/client'

const PREFETCH_TTL_MS = 10 * 60 * 1000 // 10 minutes

function buildCacheKey(period) {
  return `relievers:${new Date().getFullYear()}:${period}`
}

export function useRelievers(period = 'season') {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [sortKey, setSortKey] = useState('rank')
  const [sortDir, setSortDir] = useState('asc')

  const load = useCallback(async (force = false) => {
    setLoading(true)
    setError(null)
    try {
      const result = await fetchRelievers(null, period, force)
      setData(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [period])

  // Check cache on mount before loading
  useEffect(() => {
    const cacheKey = buildCacheKey(period)
    const cached = getCachedData(cacheKey, PREFETCH_TTL_MS)
    
    if (cached) {
      setData(cached)
      setLoading(false)
    } else {
      load()
    }
  }, []) // Only run once on mount

  // Reload when period changes
  useEffect(() => {
    const cacheKey = buildCacheKey(period)
    const cached = getCachedData(cacheKey, PREFETCH_TTL_MS)
    
    if (cached) {
      setData(cached)
      setLoading(false)
    } else {
      load()
    }
  }, [period, load])

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDir(['rank', 'name', 'team'].includes(key) ? 'asc' : 'desc')
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
    pitchers: sorted,
    loading,
    error,
    sortKey,
    sortDir,
    handleSort,
    refresh: () => load(true),
    period: data?.period || period,
  }
}
