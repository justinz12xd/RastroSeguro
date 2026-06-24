import { ClaimSummary } from '@/lib/api'
import { humanizeEntityType } from '@/lib/human-labels'

const ENTITY_FIELDS: Record<string, string[]> = {
  asegurado: ['id_asegurado'],
  proveedor: ['id_proveedor', 'proveedor', 'clinica', 'proveedor_reparacion'],
  beneficiario: ['beneficiario'],
  vehiculo: ['id_vehiculo', 'placa_hash'],
  taller: ['taller'],
  conductor: ['id_conductor', 'conductor', 'conductor_hash'],
  ciudad: ['ciudad'],
  ramo: ['ramo'],
  cobertura: ['cobertura'],
  intermediario: ['id_intermediario', 'intermediario'],
}

function isPresent(value: unknown): boolean {
  if (value == null) return false
  const text = String(value).trim()
  return Boolean(text) && !['nan', 'none', 'null', 'na', 'n/a'].includes(text.toLowerCase())
}

export interface GlobalRecurrenceRow {
  rank: number
  type: string
  value: string
  field: string
  key: string
  total: number
  inCurrentCase: boolean
}

function extractEntitiesFromClaim(claim: ClaimSummary) {
  const entities: Array<{ type: string; value: string; field: string; key: string }> = []
  const record = claim as unknown as Record<string, unknown>

  for (const [type, fields] of Object.entries(ENTITY_FIELDS)) {
    for (const field of fields) {
      const value = record[field]
      if (isPresent(value)) {
        const normalized = String(value).trim()
        entities.push({
          type,
          value: normalized,
          field,
          key: `${type}:${normalized}`,
        })
        break
      }
    }
  }

  return entities
}

export function buildGlobalRecurrenceRanking(
  claims: ClaimSummary[],
  currentClaimId?: string | null,
  limit = 50,
): GlobalRecurrenceRow[] {
  const counts = new Map<string, number>()
  const meta = new Map<string, { type: string; value: string; field: string }>()
  const caseKeys = new Set<string>()

  if (currentClaimId) {
    const current = claims.find((c) => c.id_siniestro === currentClaimId)
    if (current) {
      for (const entity of extractEntitiesFromClaim(current)) {
        caseKeys.add(entity.key)
      }
    }
  }

  for (const claim of claims) {
    const seenInClaim = new Set<string>()
    for (const entity of extractEntitiesFromClaim(claim)) {
      if (seenInClaim.has(entity.key)) continue
      seenInClaim.add(entity.key)
      counts.set(entity.key, (counts.get(entity.key) ?? 0) + 1)
      if (!meta.has(entity.key)) {
        meta.set(entity.key, { type: entity.type, value: entity.value, field: entity.field })
      }
    }
  }

  return [...counts.entries()]
    .filter(([, total]) => total >= 2)
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .slice(0, limit)
    .map(([key, total], index) => {
      const info = meta.get(key)!
      return {
        rank: index + 1,
        type: info.type,
        value: info.value,
        field: info.field,
        key,
        total,
        inCurrentCase: caseKeys.has(key),
      }
    })
}

export function formatGlobalRecurrenceLabel(row: GlobalRecurrenceRow, short = false): string {
  const typeLabel = humanizeEntityType(row.type)
  if (short) {
    return `#${row.rank} ${typeLabel}: ${row.value}`
  }
  return `#${row.rank} del ranking · ${typeLabel}: ${row.value}`
}

export function buildGlobalRecurrenceInsight(rows: GlobalRecurrenceRow[], currentClaimId?: string | null): string {
  if (!rows.length) {
    return 'No hay elementos que se repitan de forma relevante en la cartera.'
  }
  const top = rows[0]
  const inCase = rows.filter((r) => r.inCurrentCase)
  const topPart = `El #1 global es ${humanizeEntityType(top.type)} «${top.value}», presente en ${top.total} siniestro(s).`
  if (!currentClaimId || !inCase.length) return topPart
  const casePart = inCase
    .slice(0, 2)
    .map((r) => `#${r.rank} ${humanizeEntityType(r.type)} «${r.value}» (${r.total} veces)`)
    .join('; ')
  return `${topPart} En este caso aparecen: ${casePart}.`
}
