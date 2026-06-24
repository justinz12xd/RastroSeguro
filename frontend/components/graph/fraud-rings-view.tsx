'use client'

import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, Network, ShieldAlert } from 'lucide-react'
import { FraudRing, FraudRingsResponse, getFraudRings } from '@/lib/api'
import { buildFraudRingGraph } from './graph-utils'
import { FraudRingReactFlow } from './fraud-ring-reactflow'

function riskBadge(score: number) {
  if (score >= 76) return 'bg-[var(--error-container)] text-[var(--on-error-container)] border-[var(--risk-rojo)]/35'
  if (score >= 41) return 'bg-[var(--warning-container)] text-[var(--on-warning-container)] border-[var(--risk-amarillo)]/45'
  return 'bg-[var(--success-container)] text-[var(--on-success-container)] border-[var(--risk-verde)]/35'
}

export function FraudRingsView() {
  const [data, setData] = useState<FraudRingsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [revealKey, setRevealKey] = useState(0)

  useEffect(() => {
    let active = true
    setLoading(true)
    getFraudRings(12)
      .then((payload) => {
        if (!active) return
        setData(payload)
        setSelectedId(payload.anillos[0]?.id_anillo ?? null)
        setError(null)
      })
      .catch((err: Error) => {
        if (!active) return
        setError(err.message)
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  const selectedRing: FraudRing | null = useMemo(() => {
    if (!data?.anillos.length) return null
    return data.anillos.find((ring) => ring.id_anillo === selectedId) ?? data.anillos[0]
  }, [data, selectedId])

  const ringGraph = useMemo(() => {
    if (!selectedRing) return { nodes: [], edges: [] }
    return buildFraudRingGraph(selectedRing)
  }, [selectedRing])

  const handleSelectRing = (ringId: string) => {
    setSelectedId(ringId)
    setRevealKey((prev) => prev + 1)
  }

  if (loading) {
    return (
      <div className="institutional-card p-8 text-center text-muted-foreground">
        Analizando redes de fraude en la cartera…
      </div>
    )
  }

  if (error) {
    return (
      <div className="institutional-card border-[var(--risk-rojo)]/35 p-6 text-[var(--risk-rojo)]">
        <p className="font-medium">No se pudieron cargar las redes de fraude.</p>
        <p className="mt-1 text-sm text-muted-foreground">{error}</p>
      </div>
    )
  }

  if (!data || data.anillos.length === 0) {
    return (
      <div className="institutional-card space-y-3 p-6">
        <p className="font-medium">Sin anillos detectados</p>
        <p className="text-sm text-muted-foreground">
          {data?.explicacion_global || 'No hay suficientes siniestros conectados por entidades de riesgo compartidas.'}
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="action-panel-amarillo flex items-start gap-3 p-4">
        <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0" />
        <div>
          <p className="text-sm font-semibold">Red de priorización, no acusación</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Los anillos agrupan siniestros que comparten proveedores, talleres u otras entidades de riesgo.
            Sirven para revisión humana coordinada; no confirman fraude automáticamente.
          </p>
        </div>
      </div>

      <p className="text-sm text-muted-foreground">{data.explicacion_global}</p>

      <div className="grid gap-4 lg:grid-cols-12">
        <div className="institutional-card space-y-3 p-4 lg:col-span-4">
          <div className="flex items-center gap-2">
            <Network className="h-4 w-4 text-primary" />
            <h3 className="label-mono-md font-bold uppercase">Anillos detectados</h3>
            <span className="label-mono text-muted-foreground">({data.total_anillos})</span>
          </div>
          <ul className="max-h-[480px] space-y-2 overflow-y-auto">
            {data.anillos.map((ring) => (
              <li key={ring.id_anillo}>
                <button
                  type="button"
                  onClick={() => handleSelectRing(ring.id_anillo)}
                  className={`w-full border p-3 text-left transition-colors ${
                    selectedRing?.id_anillo === ring.id_anillo
                      ? 'border-primary bg-primary/5'
                      : 'border-border bg-[var(--surface-low)] hover:border-primary/40'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-mono text-sm font-bold">{ring.id_anillo}</span>
                    <span className={`rounded border px-2 py-0.5 text-xs font-semibold ${riskBadge(ring.ring_risk_score)}`}>
                      {Math.round(ring.ring_risk_score)}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {ring.tamano} siniestros · {ring.casos_rojos} rojos · ${ring.monto_expuesto.toLocaleString('es-EC')}
                  </p>
                  <p className="mt-2 line-clamp-2 text-xs leading-relaxed">{ring.explicacion}</p>
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div className="institutional-card space-y-4 p-4 lg:col-span-8">
          {selectedRing ? (
            <>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h3 className="text-lg font-semibold">{selectedRing.id_anillo}</h3>
                  <p className="text-sm text-muted-foreground">{selectedRing.explicacion}</p>
                </div>
                <div className="flex flex-wrap gap-2 text-xs">
                  <span className="rounded border border-border px-2 py-1">Puntaje de la red: {selectedRing.ring_risk_score}</span>
                  <span className="rounded border border-border px-2 py-1">Promedio: {selectedRing.score_promedio}</span>
                  <span className="rounded border border-border px-2 py-1">{selectedRing.pct_rojos}% rojos</span>
                </div>
              </div>

              <div key={revealKey}>
                <FraudRingReactFlow nodes={ringGraph.nodes} edges={ringGraph.edges} animateReveal />
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                <div className="border border-border bg-[var(--surface-low)] p-3">
                  <p className="label-mono text-muted-foreground">Entidades compartidas</p>
                  <ul className="mt-2 space-y-1 text-sm">
                    {selectedRing.entidades_compartidas.slice(0, 6).map((entity) => (
                      <li key={entity.key}>
                        <span className="font-medium">{entity.type}</span> {entity.value} ({entity.siniestros_vinculados})
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="border border-border bg-[var(--surface-low)] p-3">
                  <p className="label-mono text-muted-foreground">Siniestros del anillo</p>
                  <ul className="mt-2 space-y-1 text-sm font-mono">
                    {selectedRing.siniestros.map((id) => (
                      <li key={id} className="flex items-center gap-2">
                        {id}
                        {selectedRing.claims_resumen.find((c) => c.id_siniestro === id)?.nivel_riesgo === 'Rojo' ? (
                          <AlertTriangle className="h-3.5 w-3.5 text-[var(--risk-rojo)]" />
                        ) : null}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </>
          ) : null}
        </div>
      </div>
    </div>
  )
}
