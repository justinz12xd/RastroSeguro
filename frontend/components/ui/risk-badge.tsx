import * as React from 'react'
import { cn } from '@/lib/utils'
import { getRiskBadgeClasses, getRiskLabel } from '@/lib/claims-data'

/**
 * Risk semaphore chip. Background + foreground come from the risk tokens
 * (verde / amarillo / rojo) so contrast holds in both themes — amarillo uses
 * dark text, verde/rojo use light text. Defaults to the level label as content.
 */
export function RiskBadge({
  level,
  children,
  size = 'md',
  className,
}: {
  level: string
  children?: React.ReactNode
  size?: 'sm' | 'md'
  className?: string
}) {
  return (
    <span
      className={cn(
        'inline-flex items-center justify-center rounded-md font-bold uppercase',
        size === 'sm' ? 'label-mono px-2 py-0.5' : 'label-mono-md px-2.5 py-1',
        getRiskBadgeClasses(level),
        className,
      )}
    >
      {children ?? getRiskLabel(level)}
    </span>
  )
}
