'use client'

import { useMemo, useState } from 'react'
import { cn } from '@/lib/utils'
import { ChevronDown, ShieldAlert } from 'lucide-react'

interface NormalizedAlert {
  code: string
  name: string
  message: string
  points: number | null
  severity: string
  pdfRef: string | null
  evidence: Record<string, unknown>
}

function humanizeKey(key: string): string {
  return key.replace(/_/g, ' ').replace(/\b(\w)/g, (m) => m.toUpperCase())
}

function normalizeAlert(alert: unknown): NormalizedAlert {
  if (typeof alert === 'string') {
    return { code: '', name: alert, message: alert, points: null, severity: '', pdfRef: null, evidence: {} }
  }
  if (alert && typeof alert === 'object') {
    const a = alert as Record<string, unknown>
    return {
      code: String(a.code ?? a.codigo ?? ''),
      name: String(a.name ?? a.senal ?? a.code ?? 'Alerta de riesgo'),
      message: String(a.message ?? a.mensaje ?? a.name ?? 'Alerta de riesgo activada'),
      points: a.points != null ? Number(a.points) : a.puntos != null ? Number(a.puntos) : null,
      severity: String(a.severity ?? a.severidad ?? '').toLowerCase(),
      pdfRef: a.pdf_ref ? String(a.pdf_ref) : null,
      evidence: (a.evidence ?? a.evidencia ?? {}) as Record<string, unknown>,
    }
  }
  return { code: '', name: 'Alerta de riesgo', message: 'Alerta de riesgo activada', points: null, severity: '', pdfRef: null, evidence: {} }
}

const SEVERITY_RANK: Record<string, number> = { critica: 4, alta: 3, media: 2, baja: 1 }

function severityClasses(severity: string): string {
  switch (severity) {
    case 'critica':
    case 'alta':
      return 'risk-badge-rojo'
    case 'media':
      return 'risk-badge-amarillo'
    case 'baja':
      return 'risk-badge-verde'
    default:
      return 'bg-secondary text-secondary-foreground'
  }
}

function severityLabel(severity: string): string {
  if (!severity) return 'Señal'
  return severity.charAt(0).toUpperCase() + severity.slice(1)
}

function AlertRow({ alert }: { alert: NormalizedAlert }) {
  const [open, setOpen] = useState(false)
  const evidenceEntries = Object.entries(alert.evidence).filter(([, v]) => v != null && typeof v !== 'object')
  const hasEvidence = evidenceEntries.length > 0

  return (
    <div className="rounded-lg border border-border bg-[var(--surface-low)]">
      <div className="flex items-start gap-3 p-3">
        <div className="flex flex-wrap items-center gap-2">
          {alert.code && (
            <span className="label-mono rounded bg-foreground px-2 py-0.5 text-[11px] font-bold text-background">
              {alert.code}
            </span>
          )}
          <span className={cn('px-2 py-0.5 text-[10px] font-bold uppercase', severityClasses(alert.severity))}>
            {severityLabel(alert.severity)}
          </span>
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-foreground">{alert.name}</p>
          {alert.message && alert.message !== alert.name && (
            <p className="mt-0.5 text-sm text-muted-foreground">{alert.message}</p>
          )}
          <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1">
            {alert.points != null && alert.points > 0 && (
              <span className="label-mono text-[11px] text-destructive">+{alert.points} pts</span>
            )}
            {alert.pdfRef && (
              <span className="label-mono text-[11px] text-muted-foreground">Ref. {alert.pdfRef}</span>
            )}
            {hasEvidence && (
              <button
                type="button"
                onClick={() => setOpen((v) => !v)}
                className="focus-ring inline-flex items-center gap-1 label-mono text-[11px] text-primary"
              >
                Evidencia
                <ChevronDown className={cn('h-3 w-3 transition-transform', open && 'rotate-180')} />
              </button>
            )}
          </div>
        </div>
      </div>
      {open && hasEvidence && (
        <div className="grid grid-cols-2 gap-2 border-t border-border px-3 py-2.5 sm:grid-cols-3">
          {evidenceEntries.map(([key, value]) => (
            <div key={key}>
              <p className="label-mono text-[10px] uppercase text-muted-foreground">{humanizeKey(key)}</p>
              <p className="text-sm text-foreground">
                {typeof value === 'boolean' ? (value ? 'Sí' : 'No') : String(value)}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

const VISIBLE_LIMIT = 5

interface RuleTraceProps {
  alertas: unknown[]
}

export function RuleTrace({ alertas }: RuleTraceProps) {
  const [expanded, setExpanded] = useState(false)

  const normalized = useMemo(() => {
    return alertas
      .map(normalizeAlert)
      .sort((a, b) => (SEVERITY_RANK[b.severity] ?? 0) - (SEVERITY_RANK[a.severity] ?? 0) || (b.points ?? 0) - (a.points ?? 0))
  }, [alertas])

  const hasMore = normalized.length > VISIBLE_LIMIT
  const visible = expanded || !hasMore ? normalized : normalized.slice(0, VISIBLE_LIMIT)
  const hiddenCount = normalized.length - VISIBLE_LIMIT

  if (!normalized.length) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-border bg-[var(--surface-low)] p-4 text-sm text-muted-foreground">
        <ShieldAlert className="h-4 w-4" />
        Sin reglas de riesgo activadas para este siniestro.
      </div>
    )
  }

  return (
    <div className="space-y-2.5">
      {visible.map((alert, idx) => (
        <AlertRow key={`${alert.code || alert.name}-${idx}`} alert={alert} />
      ))}

      {hasMore && (
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="focus-ring flex w-full items-center justify-center gap-2 rounded-lg border border-dashed border-border bg-[var(--surface-low)] py-2.5 label-mono text-xs text-muted-foreground transition-colors hover:border-primary hover:text-foreground"
          aria-expanded={expanded}
        >
          <ChevronDown className={cn('h-4 w-4 transition-transform', expanded && 'rotate-180')} />
          {expanded
            ? 'Ver menos reglas'
            : `Ver ${hiddenCount} regla${hiddenCount === 1 ? '' : 's'} más de este caso`}
        </button>
      )}
    </div>
  )
}
