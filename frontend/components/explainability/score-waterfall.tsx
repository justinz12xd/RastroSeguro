'use client'

import { useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'
import { COMPONENT_LABELS } from '@/lib/score-weights'
import { Gavel, ReceiptText, ShieldAlert, FileText, Link2, TrendingDown, RotateCcw, Info } from 'lucide-react'

export interface ScoreComponents {
  reglas?: number | null
  modelo?: number | null
  anomalia?: number | null
  nlp?: number | null
  grafo?: number | null
  categorico?: number | null
}

const NEUTRAL = 50

// Pesos reales del motor (src/scoring/final_score.py)
const COMPONENT_DEFS = [
  { key: 'reglas', label: COMPONENT_LABELS.score_reglas, weight: 0.3, Icon: Gavel, desc: 'Reglas de negocio críticas activadas.' },
  { key: 'modelo', label: COMPONENT_LABELS.score_modelo, weight: 0.25, Icon: ReceiptText, desc: 'Comparación con casos históricos similares.' },
  { key: 'anomalia', label: COMPONENT_LABELS.score_anomalia, weight: 0.15, Icon: ShieldAlert, desc: 'Comportamiento distinto al habitual.' },
  { key: 'nlp', label: COMPONENT_LABELS.score_nlp, weight: 0.15, Icon: FileText, desc: 'Similitud del relato con casos previos.' },
  { key: 'grafo', label: COMPONENT_LABELS.score_grafo, weight: 0.1, Icon: Link2, desc: 'Elementos que se repiten en la red de relaciones.' },
  { key: 'categorico', label: COMPONENT_LABELS.score_categorico, weight: 0.05, Icon: TrendingDown, desc: 'Contexto cualitativo del caso.' },
] as const

const num = (value: unknown) => {
  const n = Number(value ?? NEUTRAL)
  return Number.isFinite(n) ? n : NEUTRAL
}

interface ScoreWaterfallProps {
  componentes: ScoreComponents | undefined
  scoreFinal: number
}

export function ScoreWaterfall({ componentes, scoreFinal }: ScoreWaterfallProps) {
  const [disabled, setDisabled] = useState<Set<string>>(new Set())

  const rows = useMemo(
    () =>
      COMPONENT_DEFS.map((def) => {
        const raw = num((componentes as Record<string, unknown> | undefined)?.[def.key])
        const contribution = def.weight * (raw - NEUTRAL)
        return { ...def, raw, contribution }
      }),
    [componentes],
  )

  const blended = useMemo(
    () => NEUTRAL + rows.reduce((sum, r) => sum + r.contribution, 0),
    [rows],
  )
  const whatIf = useMemo(
    () => NEUTRAL + rows.reduce((sum, r) => (disabled.has(r.key) ? sum : sum + r.contribution), 0),
    [rows, disabled],
  )

  const maxAbs = Math.max(1, ...rows.map((r) => Math.abs(r.contribution)))
  const delta = whatIf - blended
  const hasWhatIf = disabled.size > 0

  const toggle = (key: string) =>
    setDisabled((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })

  return (
    <div className="space-y-5">
      <header className="flex flex-col justify-between gap-3 md:flex-row md:items-start">
        <div>
          <h2 className="label-mono-md font-bold uppercase">Desglose del puntaje</h2>
          <p className="text-sm text-muted-foreground">
            Cuánto aporta cada señal desde una base neutral de {NEUTRAL}.
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="label-mono text-[10px] uppercase text-muted-foreground">Riesgo combinado</p>
            <motion.p
              key={Math.round(whatIf)}
              initial={{ opacity: 0.4, y: -2 }}
              animate={{ opacity: 1, y: 0 }}
              className="font-display text-3xl leading-none"
            >
              {Math.round(whatIf)}
            </motion.p>
          </div>
          {hasWhatIf && (
            <div className="text-right">
              <p className="label-mono text-[10px] uppercase text-muted-foreground">Escenario alternativo</p>
              <p className={cn('font-display text-2xl leading-none', delta < 0 ? 'text-[var(--risk-verde)]' : 'text-destructive')}>
                {delta > 0 ? '+' : ''}
                {Math.round(delta)}
              </p>
            </div>
          )}
        </div>
      </header>

      <div className="space-y-2.5">
        {rows.map((row) => {
          const off = disabled.has(row.key)
          const positive = row.contribution >= 0
          const width = (Math.abs(row.contribution) / maxAbs) * 100
          return (
            <div
              key={row.key}
              className={cn(
                'rounded-lg border border-border bg-[var(--surface-low)] p-3 transition-opacity',
                off && 'opacity-45',
              )}
            >
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  role="switch"
                  aria-checked={!off}
                  onClick={() => toggle(row.key)}
                  className={cn(
                    'focus-ring relative h-5 w-9 shrink-0 rounded-full transition-colors',
                    off ? 'bg-[var(--surface-high)]' : 'bg-primary',
                  )}
                  aria-label={`${off ? 'Reactivar' : 'Neutralizar'} señal ${row.label}`}
                >
                  <span
                    className={cn(
                      'absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-transform',
                      off ? 'left-0.5' : 'left-[18px]',
                    )}
                  />
                </button>

                <div className="flex w-32 shrink-0 items-center gap-2">
                  <row.Icon className="h-4 w-4 text-muted-foreground" />
                  <div className="min-w-0">
                    <p className="truncate label-mono-md font-bold">{row.label}</p>
                    <p className="label-mono text-[10px] text-muted-foreground">peso {Math.round(row.weight * 100)}%</p>
                  </div>
                </div>

                <div className="relative flex-1">
                  <div className="absolute left-1/2 top-0 h-full w-px bg-border" aria-hidden />
                  <div className="flex h-7 items-center">
                    <div className="flex w-1/2 justify-end pr-1">
                      {!positive && (
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${width}%` }}
                          transition={{ duration: 0.4, ease: 'easeOut' }}
                          className="h-4 rounded-l bg-[var(--risk-verde)]/75"
                        />
                      )}
                    </div>
                    <div className="flex w-1/2 justify-start pl-1">
                      {positive && (
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${width}%` }}
                          transition={{ duration: 0.4, ease: 'easeOut' }}
                          className="h-4 rounded-r bg-destructive/80"
                        />
                      )}
                    </div>
                  </div>
                </div>

                <span
                  className={cn(
                    'w-14 shrink-0 text-right label-mono-md font-bold',
                    positive ? 'text-destructive' : 'text-[var(--risk-verde)]',
                  )}
                >
                  {positive ? '+' : ''}
                  {row.contribution.toFixed(1)}
                </span>
              </div>
              <p className="mt-1.5 pl-12 text-xs text-muted-foreground">
                {row.desc} <span className="text-foreground/70">Valor base: {Math.round(row.raw)}/100.</span>
              </p>
            </div>
          )
        })}
      </div>

      <div className="flex flex-col gap-2 border-t border-border pt-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="flex items-start gap-2 text-xs text-muted-foreground">
          <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          El puntaje final ({Math.round(scoreFinal)}) también aplica calibración de cartera y reglas
          críticas, por lo que puede diferir del riesgo combinado mostrado aquí.
        </p>
        {hasWhatIf && (
          <button
            type="button"
            onClick={() => setDisabled(new Set())}
            className="focus-ring inline-flex shrink-0 items-center gap-1.5 rounded-md border border-border px-3 py-1.5 label-mono text-xs text-muted-foreground hover:text-foreground"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            Restablecer escenario
          </button>
        )}
      </div>
    </div>
  )
}
