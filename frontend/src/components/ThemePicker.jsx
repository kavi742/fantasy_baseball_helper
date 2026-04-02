import { useState } from 'react'
import { Palette } from 'lucide-react'
import { THEMES } from '../themes'

export function ThemePicker({ themeId, setThemeId }) {
  const [open, setOpen] = useState(false)

  return (
    <div className="theme-picker">
      <button
        className="btn btn-ghost theme-toggle"
        onClick={() => setOpen(o => !o)}
        title="Change theme"
      >
        <Palette size={16} />
        <span>{THEMES[themeId]?.label ?? 'Theme'}</span>
      </button>

      {open && (
        <>
          <div className="theme-backdrop" onClick={() => setOpen(false)} />
          <div className="theme-dropdown">
            <div className="theme-dropdown-header">Theme</div>
            {Object.entries(THEMES).map(([id, theme]) => (
              <button
                key={id}
                className={`theme-option ${themeId === id ? 'theme-option--active' : ''}`}
                onClick={() => { setThemeId(id); setOpen(false) }}
              >
                <span className="theme-swatch" style={{
                  background: theme.vars['--accent'],
                  boxShadow: `inset 0 0 0 2px ${theme.vars['--bg-subtle']}`
                }} />
                <span>{theme.label}</span>
                {theme.dark
                  ? <span className="theme-tag">dark</span>
                  : <span className="theme-tag theme-tag--light">light</span>
                }
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
