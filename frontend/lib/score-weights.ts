/** Mirrors src/scoring/final_score.py COMPONENT_WEIGHTS */
export const COMPONENT_WEIGHTS = {
  score_reglas: 0.30,
  score_modelo: 0.25,
  score_anomalia: 0.15,
  score_nlp: 0.15,
  score_grafo: 0.10,
  score_categorico: 0.05,
} as const

export type ScoreComponentKey = keyof typeof COMPONENT_WEIGHTS

export const COMPONENT_LABELS: Record<ScoreComponentKey, string> = {
  score_reglas: 'Reglas de negocio',
  score_modelo: 'Patrones históricos',
  score_anomalia: 'Comportamiento inusual',
  score_nlp: 'Narrativa del relato',
  score_grafo: 'Relaciones',
  score_categorico: 'Contexto del caso',
}

export const WATERFALL_KEYS = ['reglas', 'modelo', 'anomalia', 'nlp', 'grafo', 'categorico'] as const

export function waterfallToScoreKey(key: (typeof WATERFALL_KEYS)[number]): ScoreComponentKey {
  return `score_${key}` as ScoreComponentKey
}

const num = (v: unknown) => Math.min(100, Math.max(0, Number(v ?? 0)))

export function computeWeightedScore(components: Record<string, number | null | undefined>): number {
  let total = 0
  for (const [key, weight] of Object.entries(COMPONENT_WEIGHTS)) {
    total += num(components[key]) * weight
  }
  return Math.round(total * 100) / 100
}

export function buildContributionRows(components: Record<string, number | null | undefined>) {
  return (Object.entries(COMPONENT_WEIGHTS) as [ScoreComponentKey, number][]).map(([key, weight]) => {
    const value = num(components[key])
    return {
      key,
      label: COMPONENT_LABELS[key],
      value,
      weight,
      weightPct: Math.round(weight * 100),
      contribution: Math.round(value * weight * 100) / 100,
    }
  })
}
