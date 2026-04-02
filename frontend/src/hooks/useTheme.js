import { useState, useEffect } from 'react'
import { THEMES } from '../themes'

const STORAGE_KEY = 'fp-theme'

export const DEFAULT_THEME = 'catpuccin_macchiato'

export function useTheme() {
  const [themeId, setThemeId] = useState(
    () => localStorage.getItem(STORAGE_KEY) || DEFAULT_THEME
  )

  useEffect(() => {
    const theme = THEMES[themeId] || THEMES[DEFAULT_THEME]
    const root = document.documentElement

    // Apply all CSS vars
    Object.entries(theme.vars).forEach(([key, val]) => {
      root.style.setProperty(key, val)
    })

    // Set dark/light data attribute for any future use
    root.setAttribute('data-theme', themeId)
    root.setAttribute('data-dark', theme.dark ? 'true' : 'false')

    localStorage.setItem(STORAGE_KEY, themeId)
  }, [themeId])

  return { themeId, setThemeId, themes: THEMES }
}
