'use client'

import { Moon, Sun } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useTheme } from '@/components/theme-provider'
import { cn } from '@/lib/utils'

export function ThemeToggle({ className }: { className?: string }) {
  const { theme, setTheme, resolvedTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  useEffect(() => setMounted(true), [])

  if (!mounted) {
    return (
      <button
        type="button"
        aria-label="Cambiar tema"
        className={cn('focus-ring rounded p-1.5 text-muted-foreground', className)}
        disabled
      >
        <Sun className="h-5 w-5" />
      </button>
    )
  }

  const isDark = (theme === 'system' ? resolvedTheme : theme) === 'dark'

  return (
    <button
      type="button"
      aria-label={isDark ? 'Activar modo claro' : 'Activar modo oscuro'}
      onClick={() => setTheme(isDark ? 'light' : 'dark')}
      className={cn(
        'focus-ring rounded p-1.5 text-foreground transition-colors hover:bg-[var(--surface-container)]',
        className,
      )}
    >
      {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
    </button>
  )
}
