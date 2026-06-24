'use client'

import { GraphEdge, GraphNode } from './graph-types'
import { ClaimNetworkReactFlow } from './claim-network-reactflow'

export function ClaimNetworkMini({ nodes, edges }: { nodes: GraphNode[]; edges: GraphEdge[] }) {
  if (!nodes.length) return <p className="text-sm text-muted-foreground">Sin conexiones para visualizar.</p>

  return (
    <div className="space-y-2">
      <ClaimNetworkReactFlow nodes={nodes} edges={edges} compact />

      <div className="rounded border border-border bg-[var(--surface-low)] p-3 text-sm text-muted-foreground">
        <p><span className="font-semibold text-foreground">Cómo leer:</span> azul = siniestro actual, rojo = relación recurrente, gris = contexto.</p>
        <p>Las líneas animadas rojas son patrones que más elevan el riesgo por recurrencia.</p>
      </div>
    </div>
  )
}
