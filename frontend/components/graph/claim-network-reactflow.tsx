'use client'

import { useMemo } from 'react'
import ReactFlow, { Background, Controls, Edge, MarkerType, Node } from 'reactflow'
import 'reactflow/dist/style.css'
import { GraphEdge, GraphNode } from './graph-types'

const TYPE_LABEL: Record<string, string> = {
  claim: 'Siniestro',
  asegurado: 'Asegurado',
  proveedor: 'Proveedor',
  beneficiario: 'Beneficiario',
  ciudad: 'Ciudad',
  ramo: 'Ramo',
  cobertura: 'Cobertura',
}

const CONTEXT_TYPES = new Set(['ciudad', 'ramo', 'cobertura', 'asegurado'])
const RISK_TYPES = new Set(['proveedor', 'beneficiario'])

function layerPosition(type: string, idx: number, compact: boolean) {
  const yStep = compact ? 72 : 90
  const startY = compact ? 46 : 70

  if (type === 'claim') return { x: compact ? 300 : 430, y: compact ? 142 : 220 }
  if (CONTEXT_TYPES.has(type)) return { x: compact ? 70 : 80, y: startY + idx * yStep }
  if (RISK_TYPES.has(type)) return { x: compact ? 520 : 760, y: startY + idx * yStep }
  return { x: compact ? 300 : 430, y: compact ? 40 : 60 }
}

function toFlow(nodes: GraphNode[], edges: GraphEdge[], compact = false): { flowNodes: Node[]; flowEdges: Edge[] } {
  const claim = nodes[0]
  const contextNodes = nodes.slice(1).filter((n) => CONTEXT_TYPES.has(n.type))
  const riskNodes = nodes.slice(1).filter((n) => RISK_TYPES.has(n.type))
  const otherNodes = nodes.slice(1).filter((n) => !CONTEXT_TYPES.has(n.type) && !RISK_TYPES.has(n.type))

  const flowNodes: Node[] = [
    {
      id: claim?.id || 'claim',
      position: layerPosition('claim', 0, compact),
      data: { label: `Siniestro\n${claim?.label || 'N/A'}` },
      style: {
        background: 'var(--brand)', color: 'var(--primary-foreground)', borderRadius: 14, border: '2px solid var(--brand-strong)',
        fontWeight: 700, padding: 10, width: compact ? 150 : 170, textAlign: 'center', whiteSpace: 'pre-line'
      },
      draggable: false,
    },
    {
      id: 'header-context',
      position: { x: compact ? 85 : 95, y: compact ? 8 : 16 },
      data: { label: 'Contexto del caso' },
      style: { background: 'var(--surface-low)', border: '1px solid var(--border)', color: 'var(--muted-foreground)', padding: 6, fontSize: 11, fontWeight: 700, width: compact ? 130 : 160, textAlign: 'center' },
      draggable: false,
      selectable: false,
    },
    {
      id: 'header-risk',
      position: { x: compact ? 528 : 768, y: compact ? 8 : 16 },
      data: { label: 'Señales críticas' },
      style: { background: 'var(--error-container)', border: '1px solid var(--risk-rojo)', color: 'var(--on-error-container)', padding: 6, fontSize: 11, fontWeight: 700, width: compact ? 130 : 160, textAlign: 'center' },
      draggable: false,
      selectable: false,
    },
  ]

  contextNodes.forEach((node, idx) => {
    const p = layerPosition(node.type, idx, compact)
    flowNodes.push({
      id: node.id,
      position: p,
      data: { label: `${TYPE_LABEL[node.type] || node.type}\n${node.label}` },
      style: {
        background: 'var(--surface-container)', color: 'var(--foreground)', borderRadius: 12, border: '2px solid var(--surface-highest)',
        fontWeight: 600, padding: 8, width: compact ? 130 : 160, textAlign: 'center', whiteSpace: 'pre-line'
      },
      draggable: false,
    })
  })

  riskNodes.forEach((node, idx) => {
    const p = layerPosition(node.type, idx, compact)
    flowNodes.push({
      id: node.id,
      position: p,
      data: { label: `${TYPE_LABEL[node.type] || node.type}\n${node.label}` },
      style: {
        background: 'var(--error-container)', color: 'var(--on-error-container)', borderRadius: node.type === 'beneficiario' ? 999 : 8, border: '2px solid var(--risk-rojo)',
        fontWeight: 700, padding: 8, width: compact ? 130 : 160, textAlign: 'center', whiteSpace: 'pre-line'
      },
      draggable: false,
    })
  })

  otherNodes.forEach((node, idx) => {
    flowNodes.push({
      id: node.id,
      position: { x: compact ? 300 : 430, y: compact ? 258 + idx * 60 : 360 + idx * 70 },
      data: { label: `${TYPE_LABEL[node.type] || node.type}\n${node.label}` },
      style: { background: 'var(--surface-low)', border: '1px solid var(--surface-highest)', color: 'var(--foreground)', padding: 8, width: compact ? 140 : 160, textAlign: 'center', whiteSpace: 'pre-line' },
      draggable: false,
    })
  })

  const flowEdges: Edge[] = edges
    .filter((edge) => edge.source !== 'header-context' && edge.source !== 'header-risk')
    .map((edge) => {
      const target = nodes.find((n) => n.id === edge.target)
      const recurrent = target?.risk === 'high'
      return {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        label: recurrent ? `Recurrente (${target?.count || edge.weight})` : 'Relación del caso',
        style: { stroke: recurrent ? 'var(--risk-rojo)' : 'var(--surface-highest)', strokeWidth: recurrent ? 2.8 : 1.8 },
        labelStyle: { fill: 'var(--muted-foreground)', fontSize: 10, fontWeight: 600 },
        markerEnd: { type: MarkerType.ArrowClosed, color: recurrent ? 'var(--risk-rojo)' : 'var(--surface-highest)' },
        animated: recurrent,
      }
    })

  return { flowNodes, flowEdges }
}

export function ClaimNetworkReactFlow({ nodes, edges, compact = false }: { nodes: GraphNode[]; edges: GraphEdge[]; compact?: boolean }) {
  const { flowNodes, flowEdges } = useMemo(() => toFlow(nodes, edges, compact), [nodes, edges, compact])

  return (
    <div className={`rounded border border-border bg-[var(--surface-low)] ${compact ? 'h-[300px]' : 'h-[460px]'}`}>
      <ReactFlow nodes={flowNodes} edges={flowEdges} fitView nodesDraggable={false} nodesConnectable={false} zoomOnScroll panOnDrag attributionPosition="bottom-left">
        <Background gap={24} size={1} />
        <Controls />
      </ReactFlow>
    </div>
  )
}
