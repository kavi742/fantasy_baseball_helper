const BASE = '/api'

const cache = new Map()
const CACHE_TTL_MS = 5 * 60 * 1000

function getCached(key, ttlMs = CACHE_TTL_MS) {
  const entry = cache.get(key)
  if (entry && Date.now() - entry.ts < ttlMs) {
    return entry.data
  }
  cache.delete(key)
  return null
}

function setCache(key, data) {
  cache.set(key, { data, ts: Date.now() })
}

function clearCacheKey(key) {
  cache.delete(key)
}

async function request(path, cacheKey = null, force = false) {
  if (!force && cacheKey) {
    const cached = getCached(cacheKey)
    if (cached) return cached
  }
  if (force && cacheKey) {
    clearCacheKey(cacheKey)
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
 * Get cached data if available and fresh (within ttlMs).
 * @param {string} cacheKey 
 * @param {number} ttlMs - TTL in milliseconds
 * @returns {object|null} Cached data or null
 */
export function getCachedData(cacheKey, ttlMs) {
  return getCached(cacheKey, ttlMs)
}

/**
 * Fetch the week's games and probable pitchers.
 * @param {string|null} startDate - ISO date string (YYYY-MM-DD), or null for current week
 * @param {boolean} force - bypass cache, fetch fresh data
 */
export function fetchWeek(startDate = null, force = false) {
  const query = startDate ? `?start=${startDate}` : ''
  return request(`/week${query}`, `week:${startDate || 'current'}`, force)
}

/**
 * Fetch ranked probable pitchers for the current week.
 * @param {string} profile - scoring profile id (balanced, k_focused, era_whip, closer)
 * @param {string|null} weekStart - week start date
 * @param {boolean} force - bypass cache, fetch fresh data
 */
export function fetchRankings(profile = 'balanced', weekStart = null, force = false) {
  const params = new URLSearchParams({ profile })
  if (weekStart) params.append('week_start', weekStart)
  const cacheKey = `rankings:${profile}:${weekStart || 'current'}`
  return request(`/rankings?${params}`, cacheKey, force)
}

/**
 * Fetch ranked relievers/bullpen pitchers.
 * @param {number|null} season - season year, or null for current year
 * @param {string} period - "season", "this_week", or "last_week"
 * @param {boolean} force - bypass cache, fetch fresh data
 */
export function fetchRelievers(season = null, period = 'season', force = false) {
  const params = new URLSearchParams({ period })
  if (season) params.append('season', season)
  return request(`/relievers?${params}`, `relievers:${season || new Date().getFullYear()}:${period}`, force)
}

/**
 * Fetch game detail with lineups and splits.
 * @param {number|string} gameId - MLB game ID
 * @param {boolean} force - bypass cache, fetch fresh data
 */
export function fetchGame(gameId, force = false) {
  return request(`/game/${gameId}`, `game:${gameId}`, force)
}

/**
 * Fetch live scores for specified game IDs.
 * @param {string[]} gameIds - Array of game IDs
 * @param {boolean} force - bypass cache, fetch fresh data
 */
export function fetchScores(gameIds, force = false) {
  if (!gameIds || gameIds.length === 0) {
    return Promise.resolve({ scores: [] })
  }
  const gameIdsStr = gameIds.join(',')
  // Scores should not be cached long - always fetch fresh
  return request(`/scores?game_ids=${gameIdsStr}`, null, force)
}

/**
 * Clear all cached data.
 */
export function clearCache() {
  cache.clear()
}
