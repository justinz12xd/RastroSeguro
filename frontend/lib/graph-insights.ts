import { ClaimSummary } from '@/lib/api'
import { ClaimGraphPayload } from '@/components/graph/graph-types'
import { buildGlobalRecurrenceInsight, buildGlobalRecurrenceRanking } from '@/lib/global-recurrence'
import { humanizeComponentKey, humanizeEntityType } from '@/lib/human-labels'
import { COMPONENT_LABELS, ScoreComponentKey } from '@/lib/score-weights'

const SPIDER_AXES: { key: ScoreComponentKey; label: string }[] = [
  { key: 'score_reglas', label: COMPONENT_LABELS.score_reglas },
  { key: 'score_modelo', label: COMPONENT_LABELS.score_modelo },
  { key: 'score_anomalia', label: COMPONENT_LABELS.score_anomalia },
  { key: 'score_nlp', label: COMPONENT_LABELS.score_nlp },
  { key: 'score_grafo', label: COMPONENT_LABELS.score_grafo },
  { key: 'score_categorico', label: COMPONENT_LABELS.score_categorico },
]

const num = (v: unknown) => Number(v ?? 0)

export interface SpiderAxisData {
  dimension: string
  caseValue: number
  average: number
  diff: number
}

export function computeSpiderData(selectedClaim: ClaimSummary, claims: ClaimSummary[]): SpiderAxisData[] {
  return SPIDER_AXES.map((axis) => {
    const avg = claims.length
      ? claims.reduce((acc, c) => acc + num(c[axis.key]), 0) / claims.length
      : 0
    const caseValue = num(selectedClaim[axis.key])
    return {
      dimension: axis.label,
      caseValue: Math.round(caseValue * 100) / 100,
      average: Math.round(avg * 100) / 100,
      diff: Math.round((caseValue - avg) * 100) / 100,
    }
  })
}

export function getTopSpiderDrivers(selectedClaim: ClaimSummary, claims: ClaimSummary[], limit = 3) {
  return [...computeSpiderData(selectedClaim, claims)]
    .sort((a, b) => b.diff - a.diff)
    .filter((d) => d.diff > 0)
    .slice(0, limit)
}

export function buildSpiderNarrative(selectedClaim: ClaimSummary | null, claims: ClaimSummary[]): string {
  if (!selectedClaim) return 'Selecciona un caso para ver la comparación con la cartera.'
  const drivers = getTopSpiderDrivers(selectedClaim, claims, 3)
  if (!drivers.length) {
    return 'Este caso no supera el promedio de la cartera en ninguna señal clave del puntaje.'
  }
  const parts = drivers.map((d) => `${d.dimension} (+${d.diff})`)
  return `El caso destaca respecto al promedio en ${parts.join(', ')}. Conviene revisar esos puntos con criterio humano.`
}

export function buildNetworkInsight(payload: ClaimGraphPayload): string {
  const connections = payload.connections?.length ?? 0
  const alert = payload.alerta_red
  if (!connections) {
    return 'Este caso no muestra conexiones adicionales con otros siniestros de la cartera.'
  }
  const topEntity = [...payload.recurring_entities].sort((a, b) => b.total_siniestros - a.total_siniestros)[0]
  const entityPart = topEntity
    ? ` El elemento que más se repite es ${humanizeEntityType(topEntity.type)} «${topEntity.value}» (${topEntity.total_siniestros} casos).`
    : ''
  const alertPart = alert ? ' Se detectó una alerta en la red de relaciones.' : ''
  return `El caso tiene ${connections} conexión(es) con otros elementos.${entityPart}${alertPart}`
}

export function buildRecurrenceInsight(claims: ClaimSummary[], currentClaimId?: string | null): string {
  const globalRows = buildGlobalRecurrenceRanking(claims, currentClaimId, 50)
  if (globalRows.length) {
    return buildGlobalRecurrenceInsight(globalRows, currentClaimId)
  }
  return 'No hay elementos que se repitan de forma relevante en la cartera.'
}

/** @deprecated use buildRecurrenceInsight */
export const buildRankingInsight = buildRecurrenceInsight

export function buildRingsInsight(): string {
  return 'Los grupos relacionados reúnen siniestros que comparten personas, proveedores u otros datos. Sirven para ver patrones que un caso aislado no muestra.'
}

export function buildChartInsights(
  selectedClaim: ClaimSummary | null,
  claims: ClaimSummary[],
  payload: ClaimGraphPayload,
) {
  const recurrence = buildRecurrenceInsight(claims, selectedClaim?.id_siniestro)
  return {
    graph: buildNetworkInsight(payload),
    rings: buildRingsInsight(),
    recurrence,
    spider: buildSpiderNarrative(selectedClaim, claims),
  }
}

export function resolveMainDriverLabel(component?: string | null): string {
  if (!component) return 'Sin señal principal'
  return humanizeComponentKey(component)
}
