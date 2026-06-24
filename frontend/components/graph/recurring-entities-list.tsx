'use client'

import { ClaimSummary } from '@/lib/api'
import { buildGlobalRecurrenceRanking } from '@/lib/global-recurrence'
import { humanizeEntityType } from '@/lib/human-labels'
import { RecurringEntity } from './graph-types'

/** Lista del caso activo (conexiones locales). */
export function RecurringEntitiesList({ entities, limit = 5 }: { entities: RecurringEntity[]; limit?: number }) {
  const top = [...entities].sort((a, b) => b.total_siniestros - a.total_siniestros).slice(0, limit)
  if (!top.length) {
    return <p className="text-sm text-muted-foreground">No hay elementos que se repitan en otros siniestros.</p>
  }

  return (
    <div className="space-y-2">
      {top.map((item) => (
        <div key={item.key} className="border border-border bg-[var(--surface-low)] p-3">
          <p className="label-mono text-muted-foreground">{humanizeEntityType(item.type)}</p>
          <p className="font-semibold">{item.value}</p>
          <p className="text-xs text-muted-foreground">Aparece en {item.total_siniestros} siniestros</p>
        </div>
      ))}
    </div>
  )
}

/** Ranking global de recurrencia en toda la cartera. */
export function GlobalRecurrenceList({
  claims,
  currentClaimId,
  limit = 12,
}: {
  claims: ClaimSummary[]
  currentClaimId?: string | null
  limit?: number
}) {
  const rows = buildGlobalRecurrenceRanking(claims, currentClaimId, limit)

  if (!rows.length) {
    return <p className="text-sm text-muted-foreground">No hay recurrencias globales en la cartera.</p>
  }

  return (
    <div className="space-y-2">
      {rows.map((row) => (
        <div
          key={row.key}
          className={
            row.inCurrentCase
              ? 'border border-primary/40 bg-[var(--secondary-container)] p-3'
              : 'border border-border bg-[var(--surface-low)] p-3'
          }
        >
          <div className="flex items-start justify-between gap-2">
            <p className="label-mono font-bold text-primary">#{row.rank}</p>
            <p className="text-xs text-muted-foreground">{humanizeEntityType(row.type)}</p>
          </div>
          <p className="font-semibold">{row.value}</p>
          <p className="text-xs text-muted-foreground">
            {row.total} {row.total === 1 ? 'vez' : 'veces'} en la cartera
            {row.inCurrentCase ? ' · en este caso' : ''}
          </p>
        </div>
      ))}
    </div>
  )
}
