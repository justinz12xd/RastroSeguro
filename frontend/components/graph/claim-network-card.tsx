'use client'

import { Button } from '@/components/ui/button'
import { ClaimGraphPayload } from './graph-types'
import { buildClaimGraph } from './graph-utils'
import { ClaimNetworkMini } from './claim-network-mini'
import { RecurringEntitiesList } from './recurring-entities-list'

function buildHypotheses(payload: ClaimGraphPayload): { main: string; secondary: string; action: string } {
  const top = [...payload.recurring_entities].sort((a, b) => b.total_siniestros - a.total_siniestros)[0]

  const main = top
    ? `La señal principal de riesgo es la recurrencia de ${top.type} ${top.value} (${top.total_siniestros} siniestros).`
    : 'No hay recurrencias fuertes; el riesgo por red es bajo o contextual.'

  const secondary = payload.recurring_entities.length > 1
    ? `Existe un patrón secundario: más de una entidad repetida en este caso.`
    : 'El patrón se concentra en una sola entidad recurrente.'

  const action = top
    ? `Acción sugerida: comparar este expediente con ${top.siniestros_relacionados.slice(0, 3).join(', ') || 'casos relacionados'} y validar documentos.`
    : 'Acción sugerida: continuar revisión normal y monitorear nuevas conexiones.'

  return { main, secondary, action }
}

export function ClaimNetworkCard({ payload, onOpenFullView }: { payload: ClaimGraphPayload; onOpenFullView: () => void }) {
  const { nodes, edges } = buildClaimGraph(payload)
  const h = buildHypotheses(payload)

  return (
    <div className="institutional-card col-span-12 p-6 lg:col-span-8 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="label-mono-md font-bold uppercase">Relaciones y recurrencia</h3>
        <span className="label-mono text-muted-foreground">Riesgo por relaciones: {Math.round(payload.score_grafo)}/100</span>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <div className="border border-border bg-[var(--surface-low)] p-3">
          <p className="label-mono text-muted-foreground">Hipótesis principal</p>
          <p className="text-sm font-medium">{h.main}</p>
        </div>
        <div className="border border-border bg-[var(--surface-low)] p-3">
          <p className="label-mono text-muted-foreground">Patrón secundario</p>
          <p className="text-sm font-medium">{h.secondary}</p>
        </div>
        <div className="border border-border bg-[var(--surface-low)] p-3">
          <p className="label-mono text-muted-foreground">Qué revisar ahora</p>
          <p className="text-sm font-medium">{h.action}</p>
        </div>
      </div>

      <p className="text-sm leading-relaxed text-muted-foreground">{payload.explanation} Esta red no confirma fraude: solo prioriza revisión humana.</p>

      <div className="grid gap-4 md:grid-cols-2">
        <ClaimNetworkMini nodes={nodes} edges={edges} />
        <RecurringEntitiesList entities={payload.recurring_entities} limit={4} />
      </div>

      <div className="mt-2">
        <Button onClick={onOpenFullView}>Ver red completa</Button>
      </div>
    </div>
  )
}
