'use client'

import { useEffect, useMemo, useState } from 'react'
import ReactFlow, { Background, Controls, Edge, MarkerType, Node } from 'reactflow'
import 'reactflow/dist/style.css'
import { GraphEdge, GraphNode } from './graph-types'

const TYPE_LABEL: Record<string, string> = {
  claim: 'Siniestro',
  proveedor: 'Proveedor',
  beneficiario: 'Beneficiario',
  vehiculo: 'Vehículo',
  taller: 'Taller',
  conductor: 'Conductor',
  intermediario: 'Intermediario',
}

function toRingFlow(nodes: GraphNode[], edges: GraphEdge[], revealCount: number): { flowNodes: Node[]; flowEdges: Edge[] } {
  const claimNodes = nodes.filter((node) => node.type === 'claim')
  const hubNodes = nodes.filter((node) => node.type !== 'claim')
  const visibleClaimIds = new Set(claimNodes.slice(0, Math.max(0, revealCount - hubNodes.length)).map((n) => n.id))
  const hubVisible = revealCount > 0
  const claimsVisibleFrom = hubVisible ? hubNodes.length : 0
  const visibleClaims = claimNodes.slice(0, Math.max(0, revealCount - claimsVisibleFrom))

  const flowNodes: Node[] = []

  hubNodes.forEach((node, idx) => {
    if (!hubVisible) return
    flowNodes.push({
      id: node.id,
      position: { x: 340, y: 80 + idx * 100 },
      data: { label: `${TYPE_LABEL[node.type] || node.type}\n${node.label}` },
      style: {
        background: 'var(--error-container)',
        color: 'var(--on-error-container)',
        borderRadius: 12,
        border: '2px solid var(--risk-rojo)',
        fontWeight: 700,
        padding: 10,
        width: 170,
        textAlign: 'center',
        whiteSpace: 'pre-line',
        opacity: hubVisible ? 1 : 0,
        transition: 'opacity 0.4s ease',
      },
      draggable: false,
    })
  })

  const leftClaims = visibleClaims.filter((_, idx) => idx % 2 === 0)
  const rightClaims = visibleClaims.filter((_, idx) => idx % 2 === 1)

  leftClaims.forEach((node, idx) => {
    flowNodes.push({
      id: node.id,
      position: { x: 60, y: 60 + idx * 110 },
      data: { label: `Siniestro\n${node.label}` },
      style: {
        background: node.risk === 'high' ? 'var(--risk-amarillo)' : 'var(--brand)',
        color: node.risk === 'high' ? 'var(--risk-amarillo-foreground)' : 'var(--primary-foreground)',
        borderRadius: 14,
        border: node.risk === 'high' ? '2px solid color-mix(in oklch, var(--risk-amarillo) 70%, black)' : '2px solid var(--brand-strong)',
        fontWeight: 700,
        padding: 10,
        width: 150,
        textAlign: 'center',
        whiteSpace: 'pre-line',
        transition: 'opacity 0.45s ease, transform 0.45s ease',
      },
      draggable: false,
    })
  })

  rightClaims.forEach((node, idx) => {
    flowNodes.push({
      id: node.id,
      position: { x: 620, y: 60 + idx * 110 },
      data: { label: `Siniestro\n${node.label}` },
      style: {
        background: node.risk === 'high' ? 'var(--risk-amarillo)' : 'var(--brand)',
        color: node.risk === 'high' ? 'var(--risk-amarillo-foreground)' : 'var(--primary-foreground)',
        borderRadius: 14,
        border: node.risk === 'high' ? '2px solid color-mix(in oklch, var(--risk-amarillo) 70%, black)' : '2px solid var(--brand-strong)',
        fontWeight: 700,
        padding: 10,
        width: 150,
        textAlign: 'center',
        whiteSpace: 'pre-line',
        transition: 'opacity 0.45s ease, transform 0.45s ease',
      },
      draggable: false,
    })
  })

  const visibleIds = new Set([
    ...(hubVisible ? hubNodes.map((n) => n.id) : []),
    ...visibleClaims.map((n) => n.id),
  ])

  const flowEdges: Edge[] = edges
    .filter((edge) => visibleIds.has(edge.source) && visibleIds.has(edge.target))
    .map((edge, idx) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: 'Vínculo de red',
      style: {
        stroke: 'var(--risk-rojo)',
        strokeWidth: 2.4,
        opacity: idx < revealCount ? 1 : 0,
        transition: 'opacity 0.35s ease',
      },
      labelStyle: { fill: 'var(--muted-foreground)', fontSize: 10, fontWeight: 600 },
      markerEnd: { type: MarkerType.ArrowClosed, color: 'var(--risk-rojo)' },
      animated: true,
    }))

  void visibleClaimIds
  return { flowNodes, flowEdges }
}

export function FraudRingReactFlow({
  nodes,
  edges,
  animateReveal = true,
}: {
  nodes: GraphNode[]
  edges: GraphEdge[]
  animateReveal?: boolean
}) {
  const totalSteps = nodes.length + edges.length
  const [revealCount, setRevealCount] = useState(animateReveal ? 1 : totalSteps)

  useEffect(() => {
    if (!animateReveal) {
      setRevealCount(totalSteps)
      return
    }
    setRevealCount(1)
    const timer = window.setInterval(() => {
      setRevealCount((prev) => {
        if (prev >= totalSteps) {
          window.clearInterval(timer)
          return prev
        }
        return prev + 1
      })
    }, 280)
    return () => window.clearInterval(timer)
  }, [animateReveal, nodes, edges, totalSteps])

  const { flowNodes, flowEdges } = useMemo(
    () => toRingFlow(nodes, edges, revealCount),
    [nodes, edges, revealCount],
  )

  return (
    <div className="relative h-[520px] rounded border border-border bg-[var(--surface-low)]">
      <ReactFlow
        nodes={flowNodes}
        edges={flowEdges}
        fitView
        nodesDraggable={false}
        nodesConnectable={false}
        zoomOnScroll
        panOnDrag
        attributionPosition="bottom-left"
      >
        <Background gap={24} size={1} />
        <Controls />
      </ReactFlow>
      {animateReveal && revealCount < totalSteps ? (
        <div className="pointer-events-none absolute inset-x-0 top-3 flex justify-center">
          <span className="label-mono rounded bg-background/90 px-3 py-1 text-xs text-muted-foreground shadow-sm">
            Revelando red… {Math.min(revealCount, totalSteps)}/{totalSteps}
          </span>
        </div>
      ) : null}
    </div>
  )
}
