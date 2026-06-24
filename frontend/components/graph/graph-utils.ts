import { FraudRing } from '@/lib/api'
import { ClaimGraphPayload, GraphEdge, GraphNode } from './graph-types'

export function buildClaimGraph(payload: ClaimGraphPayload): { nodes: GraphNode[]; edges: GraphEdge[] } {
  const nodes: GraphNode[] = [
    {
      id: payload.id_siniestro,
      label: payload.id_siniestro,
      type: 'claim',
      risk: payload.alerta_red ? 'high' : 'normal',
      count: 1,
    },
  ]

  const edges: GraphEdge[] = []

  for (const connection of payload.connections) {
    const recurring = payload.recurring_entities.find((entity) => entity.key === connection.key)
    nodes.push({
      id: connection.key,
      label: connection.value,
      type: (connection.type as GraphNode['type']) || 'ciudad',
      risk: recurring ? 'high' : 'normal',
      count: recurring?.total_siniestros ?? 1,
    })

    edges.push({
      id: `${payload.id_siniestro}-${connection.key}`,
      source: payload.id_siniestro,
      target: connection.key,
      label: connection.type,
      weight: recurring?.total_siniestros ?? 1,
    })
  }

  return { nodes, edges }
}

export function buildFraudRingGraph(ring: FraudRing): { nodes: GraphNode[]; edges: GraphEdge[] } {
  const nodes: GraphNode[] = []
  const edges: GraphEdge[] = []

  for (const entity of ring.entidades_compartidas) {
    nodes.push({
      id: entity.key,
      label: entity.value,
      type: (entity.type as GraphNode['type']) || 'proveedor',
      risk: 'high',
      count: entity.siniestros_vinculados,
    })
  }

  for (const claim of ring.claims_resumen) {
    const claimId = claim.id_siniestro
    const isRed = String(claim.nivel_riesgo || '').toLowerCase().includes('rojo')
    nodes.push({
      id: claimId,
      label: claimId,
      type: 'claim',
      risk: isRed ? 'high' : 'normal',
      count: 1,
    })

    for (const entity of ring.entidades_compartidas) {
      if (!entity.siniestros_relacionados.includes(claimId)) {
        continue
      }
      edges.push({
        id: `${claimId}-${entity.key}`,
        source: claimId,
        target: entity.key,
        label: entity.type,
        weight: entity.siniestros_vinculados,
      })
    }
  }

  const orphanClaims = ring.claims_resumen.filter((claim) =>
    !ring.entidades_compartidas.some((entity) => entity.siniestros_relacionados.includes(claim.id_siniestro)),
  )
  if (orphanClaims.length >= 2 && ring.entidades_compartidas.length > 0) {
    const bridge = ring.entidades_compartidas[0].key
    for (const claim of orphanClaims) {
      if (!edges.some((edge) => edge.id === `${claim.id_siniestro}-${bridge}`)) {
        edges.push({
          id: `${claim.id_siniestro}-${bridge}`,
          source: claim.id_siniestro,
          target: bridge,
          label: 'vinculo_indirecto',
          weight: 1,
        })
      }
    }
  }

  return { nodes, edges }
}

export function safeGraphPayload(value: unknown, fallbackClaimId = 'SIN-NA'): ClaimGraphPayload {
  const raw = (value && typeof value === 'object' ? value : {}) as Record<string, unknown>

  const explanation = raw.explanation ?? raw.explicacion
  const connections = raw.connections ?? raw.conexiones
  const recurringEntities = raw.recurring_entities ?? raw.entidades_recurrentes

  return {
    id_siniestro: String(raw.id_siniestro || fallbackClaimId),
    score_grafo: Number(raw.score_grafo || 0),
    alerta_red: Boolean(raw.alerta_red),
    explanation: String(explanation || 'Sin hallazgos de red relevantes.'),
    connections: Array.isArray(connections) ? (connections as ClaimGraphPayload['connections']) : [],
    recurring_entities: Array.isArray(recurringEntities)
      ? (recurringEntities as ClaimGraphPayload['recurring_entities'])
      : [],
  }
}
