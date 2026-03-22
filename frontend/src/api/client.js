const BASE = '/api'

async function request(path) {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API error ${res.status}: ${text}`)
  }
  return res.json()
}

/**
 * Fetch the week's games and probable pitchers.
 * @param {string|null} startDate - ISO date string (YYYY-MM-DD), or null for current week
 */
export function fetchWeek(startDate = null) {
  const query = startDate ? `?start=${startDate}` : ''
  return request(`/week${query}`)
}
