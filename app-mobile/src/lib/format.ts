export function formatCurrency(value?: number | null): string {
  const amount = Number(value ?? 0)
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  }).format(amount)
}

export function formatNumber(value?: number | null): string {
  return new Intl.NumberFormat('es-CO').format(Number(value ?? 0))
}

export function formatPercent(value?: number | null): string {
  return `${Number(value ?? 0).toFixed(1)}%`
}

export function normalizeRisk(level?: string | null): 'critico' | 'alto' | 'medio' | 'bajo' {
  const value = String(level || '').toLowerCase()
  if (['critico', 'crítico', 'rojo'].includes(value)) return 'critico'
  if (['alto', 'high'].includes(value)) return 'alto'
  if (['medio', 'amarillo', 'medium'].includes(value)) return 'medio'
  if (['bajo', 'verde', 'low'].includes(value)) return 'bajo'
  return 'medio'
}

export function riskLabel(level?: string | null): string {
  const risk = normalizeRisk(level)
  if (risk === 'critico') return 'Crítico'
  if (risk === 'alto') return 'Alto'
  if (risk === 'bajo') return 'Bajo'
  return 'Medio'
}
