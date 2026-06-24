export type GraphNodeType = 'claim' | 'asegurado' | 'proveedor' | 'beneficiario' | 'ciudad' | 'ramo' | 'cobertura'

export interface GraphConnection {
  type: string
  value: string
  field: string
  key: string
}

export interface RecurringEntity {
  type: string
  value: string
  field: string
  key: string
  total_siniestros: number
  siniestros_relacionados: string[]
}

export interface ClaimGraphPayload {
  id_siniestro: string
  score_grafo: number
  alerta_red: boolean
  explanation: string
  connections: GraphConnection[]
  recurring_entities: RecurringEntity[]
}

export interface GraphNode {
  id: string
  label: string
  type: GraphNodeType
  risk: 'normal' | 'high'
  count: number
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  label: string
  weight: number
}
