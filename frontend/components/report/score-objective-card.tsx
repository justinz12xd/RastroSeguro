'use client'

import { ClaimExplanation, ClaimSummary } from '@/lib/api'
import { RiskBadge } from '@/components/ui/risk-badge'
import { getRiskLabel } from '@/lib/claims-data'
import { buildContributionRows, computeWeightedScore } from '@/lib/score-weights'
import { resolveMainDriverLabel } from '@/lib/graph-insights'
import { UI_COPY } from '@/lib/human-labels'
import { cn, sanitizeAiText } from '@/lib/utils'
import { ShieldCheck, Target } from 'lucide-react'

const num = (v: unknown) => Number(v ?? 0)

function normalizeRisk(level?: string | null) {
  const value = String(level || '').toLowerCase()
  if (['critico', 'crítico', 'rojo'].includes(value)) return 'critico'
  if (['alto', 'high'].includes(value)) return 'alto'
  if (['medio', 'amarillo', 'medium'].includes(value)) return 'medio'
  if (['bajo', 'verde', 'low'].includes(value)) return 'bajo'
  return 'medio'
}

function contributionTone(contribution: number) {
  if (contribution >= 20) return 'bg-destructive'
  if (contribution >= 12) return 'bg-amber-500'
  if (contribution > 0) return 'bg-primary'
  return 'bg-muted-foreground'
}

export function ScoreObjectiveCard({
  claim,
  explanation,
  mainDriverComponent,
  mainDriverValue,
  compact = false,
}: {
  claim: ClaimSummary
  explanation?: ClaimExplanation | null
  mainDriverComponent?: string | null
  mainDriverValue?: number | null
  compact?: boolean
}) {
  const scoreFinal = num(explanation?.score_final ?? claim.score_final)
  const nivelRiesgo = explanation?.nivel_riesgo || claim.nivel_riesgo || 'Sin clasificar'
  const accion = sanitizeAiText(explanation?.accion_sugerida || claim.accion_sugerida || 'Revisar el caso con criterio humano.')
  const explicacion = sanitizeAiText(explanation?.explicacion || claim.explicacion || '')

  const rawFromExplain = explanation?.componentes_score
  const components = {
    score_reglas: rawFromExplain?.reglas ?? claim.score_reglas,
    score_modelo: rawFromExplain?.modelo ?? claim.score_modelo,
    score_anomalia: rawFromExplain?.anomalia ?? claim.score_anomalia,
    score_nlp: rawFromExplain?.nlp ?? claim.score_nlp,
    score_grafo: rawFromExplain?.grafo ?? claim.score_grafo,
    score_categorico: rawFromExplain?.categorico ?? claim.score_categorico,
  }

  const rows = buildContributionRows(components)
  const weightedCalc = computeWeightedScore(components)
  const driverLabel = resolveMainDriverLabel(mainDriverComponent)
  const driverValue = mainDriverValue != null ? Math.round(num(mainDriverValue)) : null

  return (
    <section className="institutional-card overflow-hidden">
      <div className="section-header flex items-center gap-2">
        <Target className="h-4 w-4" />
        {UI_COPY.scoreObjective}
      </div>
      <div className="space-y-4 p-4">
        <div className={cn('grid gap-4', compact ? 'md:grid-cols-1' : 'md:grid-cols-[200px_1fr]')}>
          <div className="flex flex-col items-center justify-center rounded-md border border-border bg-[var(--surface-low)] p-4 text-center">
            <p className="label-mono text-muted-foreground">Puntaje final</p>
            <p className="font-display text-5xl font-semibold">{Math.round(scoreFinal)}</p>
            <p className="label-mono text-muted-foreground">de 100</p>
            <div className="mt-3 flex flex-wrap justify-center gap-2">
              <RiskBadge level={normalizeRisk(nivelRiesgo)} />
              <span className="label-mono-md rounded-full border border-border px-2 py-0.5 text-xs">{getRiskLabel(nivelRiesgo)}</span>
            </div>
          </div>

          <div className="space-y-3">
            {driverLabel !== 'Sin señal principal' && (
              <p className="text-sm">
                <span className="font-semibold">Señal principal:</span> {driverLabel}
                {driverValue != null ? ` (${driverValue}/100)` : ''}
              </p>
            )}
            {explicacion && <p className="text-sm text-muted-foreground">{explicacion}</p>}
            <div className="rounded-md border border-border bg-[var(--surface-low)] p-3 text-sm">
              <p className="label-mono-md font-bold uppercase text-muted-foreground">Recomendación</p>
              <p className="mt-1">{accion}</p>
            </div>
            <p className="text-xs text-muted-foreground">
              Cálculo ponderado (sin calibración de cartera): {weightedCalc}/100
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[480px] text-sm">
            <thead>
              <tr className="border-b border-border text-left label-mono-md text-muted-foreground">
                <th className="pb-2 pr-3">{UI_COPY.whatInfluenced}</th>
                <th className="pb-2 pr-3">Valor</th>
                <th className="pb-2 pr-3">{UI_COPY.weight}</th>
                <th className="pb-2 pr-3">{UI_COPY.contribution}</th>
                <th className="pb-2">Barra</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.key} className="border-b border-border/60">
                  <td className="py-2 pr-3 font-medium">{row.label}</td>
                  <td className="py-2 pr-3">{Math.round(row.value)}</td>
                  <td className="py-2 pr-3">{row.weightPct}%</td>
                  <td className="py-2 pr-3 font-semibold">{row.contribution}</td>
                  <td className="py-2">
                    <div className="h-2 w-full max-w-[120px] overflow-hidden rounded-full bg-background">
                      <div
                        className={cn('h-full rounded-full', contributionTone(row.contribution))}
                        style={{ width: `${Math.min(100, row.contribution * 3)}%` }}
                      />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="flex items-start gap-2 rounded-md border border-border bg-[var(--surface-low)] p-3 text-xs italic text-muted-foreground">
          <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
          RastroSeguro prioriza siniestros para revisión humana. No acusa fraude ni rechaza reclamos automáticamente.
        </p>
      </div>
    </section>
  )
}
