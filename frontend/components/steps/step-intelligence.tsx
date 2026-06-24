'use client'

import { useEffect, useMemo } from 'react'
import { ArrowRight } from 'lucide-react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useAppState } from '@/lib/app-context'
import { safeGraphPayload } from '@/components/graph/graph-utils'
import { buildClaimGraph } from '@/components/graph/graph-utils'
import { ClaimNetworkReactFlow } from '@/components/graph/claim-network-reactflow'
import { GlobalRecurrenceList, RecurringEntitiesList } from '@/components/graph/recurring-entities-list'
import { RecurrenceTopChart } from '@/components/graph/recurrence-top-chart'
import { RiskSpiderChart } from '@/components/graph/risk-spider-chart'
import { FraudRingsView } from '@/components/graph/fraud-rings-view'
import { ChartInsight } from '@/components/report/chart-insight'
import { buildChartInsights } from '@/lib/graph-insights'
import { UI_COPY } from '@/lib/human-labels'

export function StepIntelligence() {
  const { selectedClaim, selectedClaimId, selectedExplanation, loadClaimExplanation, claims, setCurrentStep } = useAppState()

  useEffect(() => {
    if (selectedClaimId && selectedExplanation?.id_siniestro !== selectedClaimId) {
      void loadClaimExplanation(selectedClaimId)
    }
  }, [loadClaimExplanation, selectedClaimId, selectedExplanation?.id_siniestro])

  const payload = useMemo(() => {
    const hasCurrentExplanation = selectedExplanation?.id_siniestro === selectedClaimId
    const details = hasCurrentExplanation
      ? (selectedExplanation?.detalles_avanzados as Record<string, unknown> | undefined)?.grafo
      : null

    return safeGraphPayload(
      details
        ? { ...(details as Record<string, unknown>), id_siniestro: selectedClaim?.id_siniestro, score_grafo: selectedClaim?.score_grafo }
        : null,
      selectedClaim?.id_siniestro || 'SIN-NA',
    )
  }, [selectedClaim?.id_siniestro, selectedClaim?.score_grafo, selectedClaimId, selectedExplanation?.detalles_avanzados, selectedExplanation?.id_siniestro])

  const graph = buildClaimGraph(payload)
  const insights = useMemo(
    () => buildChartInsights(selectedClaim, claims, payload),
    [selectedClaim, claims, payload],
  )

  return (
    <section className="px-3 py-5 lg:px-6">
      <div className="mx-auto max-w-7xl space-y-4">
        <header>
          <span className="label-mono uppercase tracking-widest text-muted-foreground">{UI_COPY.alertReview}</span>
          <h1 className="display-heading text-3xl lg:text-4xl">Paso 4: {UI_COPY.caseConnections}</h1>
          <p className="mt-2 text-base text-readable text-muted-foreground">
            Red de relaciones, elementos repetidos y comparación con la cartera.
          </p>
        </header>

        <Tabs defaultValue="graph" className="w-full">
          <TabsList>
            <TabsTrigger value="graph">Red del caso</TabsTrigger>
            <TabsTrigger value="rings">{UI_COPY.relatedGroups}</TabsTrigger>
            <TabsTrigger value="recurrence">Elementos que mas se repiten</TabsTrigger>
            <TabsTrigger value="spider">{UI_COPY.comparePortfolio}</TabsTrigger>
          </TabsList>
          <TabsContent value="graph" className="mt-3 space-y-2">
            <div className="institutional-card space-y-2 p-4">
              <p className="text-sm text-muted-foreground">
                Vista completa de la red del siniestro. Puede ampliar la vista y desplazarse por el diagrama.
              </p>
              <ClaimNetworkReactFlow nodes={graph.nodes} edges={graph.edges} />
            </div>
            <ChartInsight text={insights.graph} />
          </TabsContent>
          <TabsContent value="rings" className="mt-4 space-y-2">
            <FraudRingsView />
            <ChartInsight text={insights.rings} />
          </TabsContent>
          <TabsContent value="recurrence" className="mt-3 space-y-4">
            <div className="institutional-card space-y-4 p-4">
              <RecurrenceTopChart claims={claims} currentClaimId={selectedClaimId} />
              <div>
                <h3 className="label-mono-md mb-2 font-bold uppercase text-muted-foreground">Ranking general de la cartera</h3>
                <GlobalRecurrenceList claims={claims} currentClaimId={selectedClaimId} limit={12} />
              </div>
              {payload.recurring_entities.length > 0 && (
                <div>
                  <h3 className="label-mono-md mb-2 font-bold uppercase text-muted-foreground">{UI_COPY.repeatingElements} (en este caso)</h3>
                  <RecurringEntitiesList entities={payload.recurring_entities} limit={8} />
                </div>
              )}
            </div>
            <ChartInsight text={insights.recurrence} />
          </TabsContent>
          <TabsContent value="spider" className="mt-4">
            <RiskSpiderChart selectedClaim={selectedClaim} claims={claims} />
          </TabsContent>
        </Tabs>

        <footer className="flex items-center justify-between border-t border-border pt-6">
          <button onClick={() => setCurrentStep(3)} className="label-mono-md text-muted-foreground hover:text-primary">
            ← Anterior
          </button>
          <button
            onClick={() => setCurrentStep(5)}
            className="focus-ring inline-flex items-center gap-2 bg-primary px-6 py-2 label-mono-md text-primary-foreground"
          >
            Continuar al reporte
            <ArrowRight className="h-4 w-4" />
          </button>
        </footer>
      </div>
    </section>
  )
}
