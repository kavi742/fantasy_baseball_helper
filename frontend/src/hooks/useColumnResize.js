import { useState, useCallback, useEffect, useRef } from 'react'

const STORAGE_KEY = 'fp-col-widths'

function loadWidths(key) {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored ? JSON.parse(stored) : null
  } catch {
    return null
  }
}

function saveWidths(key, widths) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(widths))
  } catch {}
}

export function useColumnResize(columnKeys, defaultWidths = {}) {
  const [widths, setWidths] = useState(() => {
    const stored = loadWidths()
    if (stored) return stored
    return { ...defaultWidths }
  })

  const resizing = useRef(null)

  useEffect(() => {
    saveWidths(null, widths)
  }, [widths])

  const startResize = useCallback((e, colKey) => {
    e.preventDefault()
    const startX = e.clientX
    const startWidth = widths[colKey] || 100

    resizing.current = {
      colKey,
      startX,
      startWidth,
    }

    const onMouseMove = (moveEvent) => {
      if (!resizing.current) return
      const delta = moveEvent.clientX - resizing.current.startX
      const newWidth = Math.max(40, resizing.current.startWidth + delta)
      setWidths(prev => ({
        ...prev,
        [resizing.current.colKey]: newWidth,
      }))
    }

    const onMouseUp = () => {
      resizing.current = null
      document.removeEventListener('mousemove', onMouseMove)
      document.removeEventListener('mouseup', onMouseUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }

    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
    document.addEventListener('mousemove', onMouseMove)
    document.addEventListener('mouseup', onMouseUp)
  }, [widths])

  const resetWidth = useCallback((colKey) => {
    setWidths(prev => {
      const next = { ...prev }
      delete next[colKey]
      return next
    })
  }, [])

  const getWidth = useCallback((colKey) => {
    return widths[colKey] || defaultWidths[colKey] || null
  }, [widths, defaultWidths])

  return {
    widths,
    startResize,
    resetWidth,
    getWidth,
    isResizing: !!resizing.current,
  }
}
