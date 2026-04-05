import { useState, useEffect, useRef, useCallback } from 'react'
import { fetchScores } from '../api/client'

const POLL_INTERVALS = {
  IN_PROGRESS: 2 * 60 * 1000,   // 2 minutes when game is in progress
  DELAYED: 15 * 60 * 1000,       // 15 minutes when game is delayed/suspended
  FINAL: 0,                      // Don't poll when game is final
  OVERNIGHT: 0,                  // Don't poll between 1 AM - 8 AM
}

function isOvernight() {
  const hour = new Date().getHours()
  return hour >= 1 && hour < 8
}

function determinePollInterval(scores) {
  if (isOvernight()) return POLL_INTERVALS.OVERNIGHT

  // If all games are final, stop polling
  if (scores.length > 0 && scores.every(s => s.status === 'Final')) {
    return POLL_INTERVALS.FINAL
  }

  // If any game is delayed/suspended, poll less frequently
  if (scores.some(s => s.status === 'Delayed' || s.status === 'Suspended')) {
    return POLL_INTERVALS.DELAYED
  }

  // Default to in-progress polling
  return POLL_INTERVALS.IN_PROGRESS
}

export function useScores(gameIds = []) {
  const [scores, setScores] = useState({})
  const [loading, setLoading] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(null)
  const intervalRef = useRef(null)

  const updateScores = useCallback(async (force = false) => {
    if (gameIds.length === 0) return

    setLoading(true)
    try {
      const result = await fetchScores(gameIds, force)
      const newScores = {}
      result.scores.forEach(s => {
        newScores[s.game_id] = s
      })
      setScores(newScores)
      setLastUpdate(new Date())
    } catch (err) {
      console.error('Failed to fetch scores:', err)
    } finally {
      setLoading(false)
    }
  }, [gameIds.join(',')])  // eslint-disable-line react-hooks/exhaustive-deps

  // Poll for scores
  useEffect(() => {
    if (gameIds.length === 0) return

    // Initial fetch
    updateScores()

    // Set up polling
    const scheduleNextPoll = () => {
      if (intervalRef.current) {
        clearTimeout(intervalRef.current)
      }

      const pollInterval = determinePollInterval(Object.values(scores))
      if (pollInterval > 0) {
        intervalRef.current = setTimeout(async () => {
          await updateScores()
          scheduleNextPoll()
        }, pollInterval)
      }
    }

    scheduleNextPoll()

    return () => {
      if (intervalRef.current) {
        clearTimeout(intervalRef.current)
      }
    }
  }, [gameIds.join(','), updateScores])  // eslint-disable-line react-hooks/exhaustive-deps

  return {
    scores,
    loading,
    lastUpdate,
    refresh: () => updateScores(true),
  }
}
