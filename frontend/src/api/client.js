const BASE = '/api'

const cache = new Map()
const CACHE_TTL_MS = 5 * 60 * 1000

function getCached(key) {
  const entry = cache.get(key)
  if (entry && Date.now() - entry.ts < CACHE_TTL_MS) {
    return entry.data
  }
  cache.delete(key)
  return null
}

function setCache(key, data) {
  cache.set(key, { data, ts: Date.now() })
}

async function request(path, cacheKey = null) {
  if (cacheKey) {
    const cached = getCached(cacheKey)
    if (cached) return cached
  }
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API error ${res.status}: ${text}`)
  }
  const data = await res.json()
  if (cacheKey) setCache(cacheKey, data)
  return data
}

/**
 * Fetch the week's games and probable pitchers.
 * @param {string|null} startDate - ISO date string (YYYY-MM-DD), or null for current week
 */
export function fetchWeek(startDate = null) {
  const query = startDate ? `?start=${startDate}` : ''
  return request(`/week${query}`, `week:${startDate || 'current'}`)
}

/**
 * Fetch ranked probable pitchers for the current week.
 * @param {string} profile - scoring profile id (balanced, k_focused, era_whip, closer)
 */
export function fetchRankings(profile = 'balanced', weekStart = null) {
  const params = new URLSearchParams({ profile })
  if (weekStart) params.append('week_start', weekStart)
  const cacheKey = `rankings:${profile}:${weekStart || 'current'}`
  return request(`/rankings?${params}`, cacheKey)
}

/**
 * Fetch ranked relievers/bullpen pitchers.
 * @param {number|null} season - season year, or null for current year
 */
export function fetchRelievers(season = null) {
  const params = new URLSearchParams()
  if (season) params.append('season', season)
  return request(`/relievers?${params}`, `relievers:${season || new Date().getFullYear()}`)
}
