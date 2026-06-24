'use client'

import * as React from 'react'

type Theme = 'light' | 'dark' | 'system'
type ResolvedTheme = Exclude<Theme, 'system'>

type ThemeProviderProps = {
  attribute?: 'class'
  children: React.ReactNode
  defaultTheme?: Theme
  disableTransitionOnChange?: boolean
  enableSystem?: boolean
  storageKey?: string
}

type ThemeContextValue = {
  theme: Theme
  resolvedTheme: ResolvedTheme
  setTheme: (theme: Theme) => void
}

const ThemeContext = React.createContext<ThemeContextValue | null>(null)

function getSystemTheme(): ResolvedTheme {
  if (typeof window === 'undefined') return 'light'
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function applyTheme(theme: ResolvedTheme, disableTransitionOnChange: boolean) {
  const root = document.documentElement
  let cleanup = () => {}

  if (disableTransitionOnChange) {
    const style = document.createElement('style')
    style.appendChild(
      document.createTextNode('*{transition:none!important}'),
    )
    document.head.appendChild(style)
    cleanup = () => {
      void style.offsetHeight
      style.remove()
    }
  }

  root.classList.remove('light', 'dark')
  root.classList.add(theme)
  root.style.colorScheme = theme

  requestAnimationFrame(() => cleanup())
}

export function ThemeProvider({
  children,
  defaultTheme = 'system',
  disableTransitionOnChange = false,
  enableSystem = true,
  storageKey = 'rastros-seguro-theme',
}: ThemeProviderProps) {
  const [theme, setThemeState] = React.useState<Theme>(defaultTheme)
  const [resolvedTheme, setResolvedTheme] = React.useState<ResolvedTheme>(() =>
    defaultTheme === 'system' ? 'light' : defaultTheme,
  )

  React.useEffect(() => {
    const storedTheme = window.localStorage.getItem(storageKey) as Theme | null
    const nextTheme = storedTheme ?? defaultTheme
    setThemeState(nextTheme)
  }, [defaultTheme, storageKey])

  React.useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')

    const syncTheme = () => {
      const nextResolved =
        theme === 'system' && enableSystem ? getSystemTheme() : theme === 'dark' ? 'dark' : 'light'

      setResolvedTheme(nextResolved)
      applyTheme(nextResolved, disableTransitionOnChange)
    }

    syncTheme()

    if (!(enableSystem && theme === 'system')) return

    mediaQuery.addEventListener('change', syncTheme)
    return () => mediaQuery.removeEventListener('change', syncTheme)
  }, [disableTransitionOnChange, enableSystem, theme])

  const setTheme = React.useCallback(
    (nextTheme: Theme) => {
      setThemeState(nextTheme)
      window.localStorage.setItem(storageKey, nextTheme)
    },
    [storageKey],
  )

  const value = React.useMemo(
    () => ({ theme, resolvedTheme, setTheme }),
    [resolvedTheme, setTheme, theme],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme() {
  const context = React.useContext(ThemeContext)

  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider')
  }

  return context
}
