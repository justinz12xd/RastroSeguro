'use client'

import { useMemo, useState } from 'react'
import type { AgentResponse } from '@/lib/api'
import { formatCurrency, getRiskBadgeClasses, getRiskLabel, normalizeRiskLevel } from '@/lib/claims-data'
import { cn } from '@/lib/utils'
import { UI_COPY } from '@/lib/human-labels'
import { ArrowUpRight, Bot, Database, FileText, Sparkles } from 'lucide-react'
import { renderMarkdownBlocks } from '@/lib/markdown'

const CURRENCY_HINTS = ['monto', 'ahorro', 'suma', 'prima', 'valor', 'expuesto', 'reclamado', 'pagado', 'estimado']
const SCORE_HINTS = ['score', 'puntos', 'porcentaje', 'pct', 'promedio', 'ratio']
const RISK_KEYS = ['nivel_riesgo', 'nivel', 'riesgo']
const ID_KEYS = ['id_siniestro', 'siniestro', 'id_anillo']
const COMPACT_MESSAGE_INTENTS = new Set(['fecha_actual', 'saludo'])

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function humanizeKey(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/\bpct\b/gi, '%')
    .replace(/\b(\w)/g, (m) => m.toUpperCase())
}

function looksLikeCurrency(key: string): boolean {
  const k = key.toLowerCase()
  return CURRENCY_HINTS.some((hint) => k.includes(hint))
}

function looksLikeScore(key: string): boolean {
  const k = key.toLowerCase()
  return SCORE_HINTS.some((hint) => k.includes(hint))
}

function formatValue(key: string, value: unknown): string {
  if (value == null) return '—'
  if (typeof value === 'boolean') return value ? 'Sí' : 'No'
  if (typeof value === 'number') {
    if (looksLikeCurrency(key)) return formatCurrency(value)
    if (looksLikeScore(key)) return Number.isInteger(value) ? String(value) : value.toFixed(2)
    return String(value)
  }
  if (typeof value === 'string') return value
  if (Array.isArray(value)) return `${value.length} elementos`
  if (isPlainObject(value)) return Object.keys(value).length ? '{…}' : '—'
  return String(value)
}

/** Recursively collect claim ids found anywhere in the agent payload. */
function extractClaimIds(data: unknown, acc = new Set<string>(), depth = 0): Set<string> {
  if (depth > 4 || acc.size > 12) return acc
  if (Array.isArray(data)) {
    data.forEach((item) => extractClaimIds(item, acc, depth + 1))
  } else if (isPlainObject(data)) {
    for (const [key, value] of Object.entries(data)) {
      if (ID_KEYS.includes(key.toLowerCase()) && typeof value === 'string' && /^[A-Z]+-?\d+/i.test(value)) {
        acc.add(value)
      } else {
        extractClaimIds(value, acc, depth + 1)
      }
    }
  } else if (typeof data === 'string') {
    const matches = data.match(/\bSIN-?\d{2,}/gi)
    matches?.forEach((m) => acc.add(m.toUpperCase()))
  }
  return acc
}

function RiskCell({ value }: { value: string }) {
  if (normalizeRiskLevel(value) === 'neutral') return <span className="text-sm">{value}</span>
  return (
    <span className={cn('inline-block px-2 py-0.5 text-[11px] font-bold uppercase', getRiskBadgeClasses(value))}>
      {getRiskLabel(value)}
    </span>
  )
}

function DataTable({ rows }: { rows: Record<string, unknown>[] }) {
  const columns = useMemo(() => {
    const seen: string[] = []
    for (const row of rows.slice(0, 12)) {
      for (const key of Object.keys(row)) {
        if (!seen.includes(key) && !isPlainObject(row[key]) && !Array.isArray(row[key])) seen.push(key)
      }
    }
    return seen.slice(0, 6)
  }, [rows])

  if (!columns.length) {
    return <p className="text-sm text-muted-foreground">Sin columnas tabulables en la respuesta.</p>
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <table className="zebra w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-border bg-[var(--surface-container)]">
            {columns.map((col) => (
              <th key={col} className="label-mono px-3 py-2 text-left text-xs text-muted-foreground">
                {humanizeKey(col)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, 12).map((row, idx) => (
            <tr key={idx} className="border-b border-border/60 last:border-0">
              {columns.map((col) => (
                <td key={col} className="px-3 py-2 align-top">
                  {RISK_KEYS.includes(col.toLowerCase()) && typeof row[col] === 'string' ? (
                    <RiskCell value={row[col] as string} />
                  ) : ID_KEYS.includes(col.toLowerCase()) ? (
                    <span className="label-mono text-foreground">{formatValue(col, row[col])}</span>
                  ) : (
                    <span className="text-foreground/90">{formatValue(col, row[col])}</span>
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > 12 && (
        <p className="border-t border-border px-3 py-1.5 text-xs text-muted-foreground">
          +{rows.length - 12} filas adicionales disponibles en el detalle completo.
        </p>
      )}
    </div>
  )
}

function KeyValueCards({ obj }: { obj: Record<string, unknown> }) {
  const scalarEntries = Object.entries(obj).filter(([, v]) => !isPlainObject(v) && !Array.isArray(v))
  const arrayEntries = Object.entries(obj).filter(([, v]) => Array.isArray(v) && (v as unknown[]).length > 0)

  return (
    <div className="space-y-3">
      {scalarEntries.length > 0 && (
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
          {scalarEntries.slice(0, 9).map(([key, value]) => (
            <div key={key} className="rounded-lg border border-border bg-[var(--surface-low)] p-3">
              <p className="label-mono text-[10px] uppercase text-muted-foreground">{humanizeKey(key)}</p>
              {RISK_KEYS.includes(key.toLowerCase()) && typeof value === 'string' ? (
                <div className="mt-1"><RiskCell value={value} /></div>
              ) : (
                <p className="mt-1 text-sm font-semibold text-foreground">{formatValue(key, value)}</p>
              )}
            </div>
          ))}
        </div>
      )}
      {arrayEntries.map(([key, value]) => {
        const arr = value as unknown[]
        if (arr.every(isPlainObject)) {
          return (
            <div key={key} className="space-y-1.5">
              <p className="label-mono text-[10px] uppercase text-muted-foreground">{humanizeKey(key)}</p>
              <DataTable rows={arr as Record<string, unknown>[]} />
            </div>
          )
        }
        return (
          <div key={key} className="space-y-1.5">
            <p className="label-mono text-[10px] uppercase text-muted-foreground">{humanizeKey(key)}</p>
            <ul className="space-y-1">
              {arr.slice(0, 8).map((item, i) => (
                <li key={i} className="flex gap-2 text-sm text-foreground/90">
                  <span className="text-muted-foreground">•</span>
                  <span>{String(item)}</span>
                </li>
              ))}
            </ul>
          </div>
        )
      })}
    </div>
  )
}

/** Claim explanation payload (explicar_siniestro / expediente_siniestro). */
function isClaimExplanation(data: unknown): data is Record<string, unknown> {
  return isPlainObject(data) && 'nivel_riesgo' in data && Array.isArray((data as Record<string, unknown>).alertas)
}

function severityDotClass(severity: string): string {
  const s = severity.toLowerCase()
  if (s.includes('crit') || s.includes('alta')) return 'bg-[var(--risk-high,#dc2626)]'
  if (s.includes('media')) return 'bg-[var(--risk-medium,#d97706)]'
  return 'bg-muted-foreground/50'
}

interface Signal {
  name?: unknown
  message?: unknown
  severity?: unknown
}

function SignalList({ alertas }: { alertas: Record<string, unknown>[] }) {
  const [expanded, setExpanded] = useState(false)
  const signals = alertas as Signal[]
  const visible = expanded ? signals : signals.slice(0, 3)
  const hidden = signals.length - visible.length

  return (
    <div className="space-y-1.5">
      <p className="label-mono text-[10px] uppercase text-muted-foreground">Señales detectadas</p>
      <ul className="space-y-2">
        {visible.map((signal, i) => {
          const severity = String(signal.severity ?? '')
          const name = String(signal.name ?? '')
          const detail = String(signal.message ?? '')
          return (
            <li key={i} className="flex gap-2.5">
              <span className={cn('mt-1.5 h-2 w-2 shrink-0 rounded-full', severityDotClass(severity))} aria-hidden />
              <p className="text-sm leading-6 text-foreground/90">
                <span className="font-semibold text-foreground">{name}</span>
                {detail && name ? ' — ' : ''}
                {detail}
              </p>
            </li>
          )
        })}
      </ul>
      {hidden > 0 && (
        <button
          type="button"
          onClick={() => setExpanded(true)}
          className="focus-ring text-xs font-medium text-primary hover:underline"
        >
          Ver {hidden} {hidden === 1 ? 'señal más' : 'señales más'}
        </button>
      )}
    </div>
  )
}

function ClaimExplanation({ data, source }: { data: Record<string, unknown>; source?: string }) {
  const nivel = String(data.nivel_riesgo ?? '')
  const score = data.score_final
  const explicacion = typeof data.explicacion === 'string' ? data.explicacion : ''
  const accion = typeof data.accion_sugerida === 'string' ? data.accion_sugerida : ''
  const alertas = Array.isArray(data.alertas) ? (data.alertas as Record<string, unknown>[]) : []
  // When the LLM synthesized a narrative it already covers the explanation;
  // only surface the traceable explicacion text on the deterministic fallback.
  const showExplanation = source !== 'llm' && Boolean(explicacion)

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        {normalizeRiskLevel(nivel) !== 'neutral' && <RiskCell value={nivel} />}
        {typeof score === 'number' && (
          <span className="label-mono text-xs text-muted-foreground">
            Score {Number.isInteger(score) ? score : score.toFixed(2)}
          </span>
        )}
      </div>

      {showExplanation && <p className="text-sm leading-6 text-foreground/90">{explicacion}</p>}

      {alertas.length > 0 && <SignalList alertas={alertas} />}

      {accion && (
        <div className="rounded-lg border border-border bg-[var(--surface-low)] p-3">
          <p className="label-mono text-[10px] uppercase text-muted-foreground">Acción sugerida</p>
          <p className="mt-1 text-sm leading-6 text-foreground">{accion}</p>
        </div>
      )}
    </div>
  )
}

function SourceBadge({ source }: { source?: string }) {
  if (!source) return null
  const config: Record<string, { label: string; Icon: typeof Database }> = {
    tools: { label: 'Datos del motor', Icon: Database },
    agent: { label: 'Respuesta directa', Icon: Bot },
    rag: { label: 'Base documental', Icon: FileText },
    llm: { label: UI_COPY.assistantSynthesis, Icon: Sparkles },
  }
  const { label, Icon } = config[source] ?? { label: source, Icon: Database }
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-[var(--surface-low)] px-2.5 py-1 text-[11px] text-muted-foreground">
      <Icon className="h-3 w-3" />
      {label}
    </span>
  )
}

interface AgentResultProps {
  response: AgentResponse
  onOpenClaim?: (id: string) => void
}

export function AgentResult({ response, onOpenClaim }: AgentResultProps) {
  const { data, message, source, intent } = response
  const claimIds = useMemo(() => Array.from(extractClaimIds(data ?? message)), [data, message])

  const claimExplanation = isClaimExplanation(data)
  const compactMessage = COMPACT_MESSAGE_INTENTS.has(intent ?? '')

  const body = useMemo(() => {
    if (compactMessage) {
      return null
    }
    if (isClaimExplanation(data)) {
      return <ClaimExplanation data={data} source={source} />
    }
    if (Array.isArray(data) && data.length > 0 && data.every(isPlainObject)) {
      return <DataTable rows={data as Record<string, unknown>[]} />
    }
    if (Array.isArray(data) && data.length > 0) {
      return (
        <ul className="space-y-1">
          {(data as unknown[]).slice(0, 12).map((item, i) => (
            <li key={i} className="flex gap-2 text-sm text-foreground/90">
              <span className="text-muted-foreground">•</span>
              <span>{String(item)}</span>
            </li>
          ))}
        </ul>
      )
    }
    if (isPlainObject(data) && Object.keys(data).length > 0) {
      return <KeyValueCards obj={data} />
    }
    return null
  }, [compactMessage, data, source])

  return (
    <div className="space-y-3">
      {/* On the deterministic fallback the message is a terse stub; the
          explanation lives in the data, so skip the robotic one-liner. */}
      {message && !(claimExplanation && source !== 'llm') && renderMarkdownBlocks(message)}

      {body}

      {onOpenClaim && claimIds.length > 0 && (
        <div className="flex flex-wrap gap-2 pt-1">
          {claimIds.slice(0, 6).map((id) => (
            <button
              key={id}
              type="button"
              onClick={() => onOpenClaim(id)}
              className="focus-ring inline-flex items-center gap-1.5 rounded-full border border-border bg-[var(--surface-low)] px-3 py-1.5 label-mono text-xs text-foreground transition-colors hover:border-primary hover:text-primary"
            >
              Abrir {id}
              <ArrowUpRight className="h-3.5 w-3.5" />
            </button>
          ))}
        </div>
      )}

      <div className="flex items-center justify-between gap-3 border-t border-border/60 pt-2">
        <SourceBadge source={source} />
        <span className="text-[11px] italic text-muted-foreground">Alerta para revisión humana, no acusa fraude.</span>
      </div>
    </div>
  )
}
