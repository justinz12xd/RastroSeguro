'use client'

import { useEffect, useState } from 'react'
import { useAppState } from '@/lib/app-context'
import { alertToText } from '@/lib/api'
import { getRiskBadgeClasses, getActionPanelClasses, getRiskColor, getRiskLabel } from '@/lib/claims-data'
import { downloadCaseReportPdf } from '@/lib/case-report-export'
import { AlertTriangle, ArrowLeft, ArrowRight, Bot, BrainCircuit, CheckCircle2, Download, Info } from 'lucide-react'
import { cn, sanitizeAiText } from '@/lib/utils'
import { safeGraphPayload } from '@/components/graph/graph-utils'
import { ScoreWaterfall } from '@/components/explainability/score-waterfall'
import { RuleTrace } from '@/components/explainability/rule-trace'
import { NarrativeCompare, type SimilarMatch } from '@/components/explainability/narrative-compare'
import { resolveMainDriverLabel } from '@/lib/graph-insights'
const num = (value: unknown) => Number(value ?? 0)

export function StepAnalysis() {
  const { claims, selectedClaim, selectedClaimId, selectedExplanation, isLoadingExplanation, apiError, apiHint, loadClaimExplanation, setCurrentStep, setShowChat, saveAnalystCaseAnalysis } = useAppState()
  const [isExporting, setIsExporting] = useState(false)

  useEffect(() => {
    if (selectedClaim && selectedClaimId && selectedExplanation?.id_siniestro !== selectedClaimId) {
      void loadClaimExplanation(selectedClaimId)
    }
  }, [loadClaimExplanation, selectedClaim, selectedClaimId, selectedExplanation?.id_siniestro])

  if (!selectedClaim) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 text-muted-foreground">
        <p>No hay caso seleccionado</p>
        <button onClick={() => setCurrentStep(1)} className="focus-ring bg-primary px-4 py-2 text-sm text-primary-foreground">Volver al Paso 1</button>
      </div>
    )
  }

  const scoreFinal = num(selectedExplanation?.score_final ?? selectedClaim.score_final)
  const nivelRiesgo = selectedExplanation?.nivel_riesgo || selectedClaim.nivel_riesgo || 'Sin clasificar'
  const rawExplicacion = selectedExplanation?.explicacion || selectedClaim.explicacion || 'La explicación estará disponible cuando el sistema termine de cargar la información.'
  const explicacion = sanitizeAiText(rawExplicacion)
  const accion = sanitizeAiText(selectedExplanation?.accion_sugerida || selectedClaim.accion_sugerida || 'Revisar el caso con criterio humano.')
  const componentes = selectedExplanation?.componentes_score
  const alertas = (selectedExplanation?.alertas?.length ? selectedExplanation.alertas : selectedClaim.alertas_activadas instanceof Array ? selectedClaim.alertas_activadas : []) as unknown[]
  const riskColor = getRiskColor(nivelRiesgo)
  const meterRadius = 58
  const circumference = 2 * Math.PI * meterRadius
  const dashOffset = circumference - (scoreFinal / 100) * circumference
  const hasCurrentExplanation = selectedExplanation?.id_siniestro === selectedClaimId
  const graphPayload = safeGraphPayload(
    hasCurrentExplanation ? ((selectedExplanation?.detalles_avanzados as Record<string, unknown> | undefined)?.grafo) : null,
    selectedClaim.id_siniestro,
  )

  const waterfallComponents = componentes ?? {
    reglas: selectedClaim.score_reglas,
    modelo: selectedClaim.score_modelo,
    anomalia: selectedClaim.score_anomalia,
    nlp: selectedClaim.score_nlp,
    grafo: selectedClaim.score_grafo,
    categorico: selectedClaim.score_categorico,
  }
  const topAlerts = (alertas.length ? alertas : ['Sin alertas principales.']).slice(0, 3)
  const topEntity = [...graphPayload.recurring_entities].sort((a, b) => b.total_siniestros - a.total_siniestros)[0]
  const relationSummary = topEntity
    ? `${topEntity.type} ${topEntity.value} aparece en ${topEntity.total_siniestros} casos.`
    : 'No se detectan coincidencias fuertes con otros casos.'

  const nlpDetails = hasCurrentExplanation
    ? ((selectedExplanation?.detalles_avanzados as Record<string, unknown> | undefined)?.nlp as
        | { similares?: unknown[] }
        | undefined)
    : undefined
  const similarMatches: SimilarMatch[] = Array.isArray(nlpDetails?.similares)
    ? (nlpDetails.similares as Array<Record<string, unknown>>)
        .map((m) => ({ target_id: String(m.target_id ?? ''), similarity: Number(m.similarity ?? 0) }))
        .filter((m) => m.target_id)
    : []
  const currentNarrative = selectedClaim.narrativa || selectedClaim.descripcion || ''
  const lookupNarrative = (id: string) => {
    const match = claims.find((c) => c.id_siniestro === id)
    return match?.narrativa || match?.descripcion || undefined
  }

  const mainDriverRaw = hasCurrentExplanation
    ? ((selectedExplanation?.detalles_avanzados as Record<string, unknown> | undefined)?.main_driver as { componente?: string; valor?: number } | undefined)
    : undefined
  const oneLineSummary = mainDriverRaw?.componente
    ? `En una frase: la señal que más explica este puntaje es ${resolveMainDriverLabel(mainDriverRaw.componente)}${mainDriverRaw.valor != null ? ` (${Math.round(num(mainDriverRaw.valor))}/100)` : ''}.`
    : topAlerts.length
      ? `En una frase: las alertas principales (${topAlerts.map((a) => alertToText(a)).slice(0, 2).join('; ')}) concentran la priorización.`
      : null

  const exportCertificate = () => {
    if (isExporting) return
    setIsExporting(true)
    void downloadCaseReportPdf({
      claim: selectedClaim,
      explanation: selectedExplanation,
      graphPayload,
      claims,
    })
      .catch(() => undefined)
      .finally(() => setIsExporting(false))
  }

  const saveAndCloseAnalysis = () => {
    saveAnalystCaseAnalysis({
      id: selectedClaim.id_siniestro,
      score: scoreFinal,
      riskLevel: nivelRiesgo,
      summary: explicacion,
      recommendation: accion,
      topAlerts: topAlerts.map((alert) => alertToText(alert)),
      amount: selectedClaim.monto_reclamado ?? null,
      branch: selectedClaim.ramo ?? null,
      city: selectedClaim.ciudad ?? null,
      provider: selectedClaim.id_proveedor || selectedClaim.beneficiario || null,
    })
    setCurrentStep(5)
  }

  return (
    <section className="px-3 py-5 lg:px-6">
      <div className="mx-auto max-w-7xl space-y-4">
        <header className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div>
            <span className="label-mono uppercase tracking-widest text-muted-foreground">Explicación del caso</span>
            <h1 className="display-heading text-3xl lg:text-4xl">Paso 3: Resultado y motivos</h1>
            <p className="mt-2 text-base text-readable text-muted-foreground">Resumen claro del puntaje, las señales principales y la recomendación.</p>
          </div>
          <div className="flex items-center gap-2 border border-border bg-[var(--surface-high)] px-4 py-2">
            <Info className="h-4 w-4" />
            <span className="label-mono">{isLoadingExplanation ? 'REVISANDO...' : 'INFORMACIÓN ACTUALIZADA'}</span>
          </div>
        </header>

        {apiError && (
          <div className="border border-destructive bg-[var(--error-container)] p-4 text-[var(--on-error-container)]">
            <p className="font-semibold">{apiError}</p>
            {apiHint && <p className="mt-1 text-sm">{apiHint}</p>}
          </div>
        )}

        <div className="grid grid-cols-12 gap-4">
          <section className="institutional-card col-span-12 p-4 lg:col-span-8">
            <div className="grid gap-4 md:grid-cols-[180px_1fr] md:items-center">
              <div className="flex justify-center">
                <div className="relative shrink-0">
                  <svg viewBox="0 0 160 160" className="h-40 w-40 -rotate-90">
                    <circle cx="80" cy="80" r={meterRadius} fill="transparent" stroke="var(--surface-high)" strokeWidth="12" />
                    <circle cx="80" cy="80" r={meterRadius} fill="transparent" stroke={riskColor} strokeWidth="12" strokeDasharray={circumference} strokeDashoffset={dashOffset} strokeLinecap="round" />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="font-display text-4xl">{Math.round(scoreFinal)}</span>
                    <span className="label-mono text-muted-foreground">DE 100</span>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex flex-wrap items-center gap-2">
                  <span className={cn('px-4 py-1 label-mono-md font-bold uppercase', getRiskBadgeClasses(nivelRiesgo))}>{getRiskLabel(nivelRiesgo)}</span>
                  <span className="border border-border bg-[var(--surface-low)] px-3 py-1 label-mono text-foreground">{selectedClaim.id_siniestro}</span>
                </div>
                <p className="text-base text-readable">{explicacion}</p>
                <div className={cn('p-4', getActionPanelClasses(nivelRiesgo))}>
                  <div className="mb-1 flex items-center gap-2"><AlertTriangle className="h-5 w-5" /><span className="label-mono-md font-bold uppercase">Recomendación</span></div>
                  <p className="text-sm leading-relaxed">{accion}</p>
                </div>
              </div>
            </div>
          </section>

          <aside className="institutional-card col-span-12 p-4 lg:col-span-4">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="label-mono-md font-bold uppercase">Señales clave</h3>
              <span className="label-mono text-muted-foreground">Principales 3</span>
            </div>
            <div className="space-y-3">
              {topAlerts.map((a, i) => (
                <div key={`${i}-${alertToText(a)}`} className="border border-border bg-[var(--surface-low)] p-3">
                  <p className="label-mono text-muted-foreground">SEÑAL {String(i + 1).padStart(2, '0')}</p>
                  <p className="mt-1 text-sm">{alertToText(a)}</p>
                </div>
              ))}
            </div>
            {alertas.length > 3 && <p className="mt-3 text-xs text-muted-foreground">+{alertas.length - 3} señales adicionales disponibles en el detalle.</p>}
          </aside>

          <section className="institutional-card col-span-12 p-4 lg:col-span-7">
            <ScoreWaterfall componentes={waterfallComponents} scoreFinal={scoreFinal} />
            {oneLineSummary && (
              <p className="mt-3 rounded-md border border-border bg-[var(--surface-low)] p-3 text-sm text-muted-foreground">{oneLineSummary}</p>
            )}
          </section>

          <section className="institutional-card col-span-12 p-4 lg:col-span-5">
            <div className="mb-4 flex flex-col justify-between gap-2 md:flex-row md:items-end">
              <div>
                <h2 className="label-mono-md font-bold uppercase">Detalle de señales</h2>
                <p className="text-sm text-muted-foreground">Listado de señales encontradas y su evidencia.</p>
              </div>
              <button onClick={() => setCurrentStep(4)} className="focus-ring shrink-0 self-start border border-border px-4 py-2 label-mono-md text-foreground hover:bg-[var(--surface-container)] md:self-auto">
                Ver detalle completo
              </button>
            </div>
            <RuleTrace alertas={alertas} />
          </section>

          {similarMatches.length > 0 && currentNarrative && (
            <section className="institutional-card col-span-12 p-4">
              <NarrativeCompare
                currentId={selectedClaim.id_siniestro}
                currentNarrative={currentNarrative}
                matches={similarMatches}
                lookupNarrative={lookupNarrative}
              />
            </section>
          )}

          <section className="institutional-card col-span-12 p-4 lg:col-span-8">
            <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
              <div>
                <h2 className="label-mono-md font-bold uppercase">Coincidencia principal</h2>
                <p className="mt-2 text-base font-medium">{relationSummary}</p>
                <p className="mt-1 text-sm text-muted-foreground">Estas coincidencias ayudan a decidir qué comparar primero, pero no confirman nada por sí solas.</p>
              </div>
              <button onClick={() => setCurrentStep(4)} className="focus-ring flex shrink-0 items-center justify-center gap-2 bg-primary px-4 py-2.5 label-mono-md text-primary-foreground">
                <BrainCircuit className="h-4 w-4" />Ver relaciones completas
              </button>
            </div>
          </section>

          <aside className="institutional-card col-span-12 p-4 lg:col-span-4">
            <div className="flex items-start gap-3">
              <Info className="mt-1 h-5 w-5 shrink-0" />
              <div>
                <h3 className="font-display text-lg font-semibold">Importante</h3>
                <p className="mt-1 text-sm italic text-muted-foreground">Este resultado ayuda a priorizar la revisión humana; no acusa ni rechaza automáticamente.</p>
              </div>
            </div>
            <button onClick={exportCertificate} disabled={isExporting} className="focus-ring mt-5 flex w-full items-center justify-center gap-2 border border-border py-2 label-mono-md text-foreground transition-colors hover:bg-[var(--surface-container)] disabled:cursor-not-allowed disabled:opacity-50"><Download className="h-4 w-4" />{isExporting ? 'Generando PDF…' : 'Descargar resumen (PDF)'}</button>
          </aside>
        </div>

        <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-6">
          <button onClick={() => setCurrentStep(2)} className="focus-ring flex items-center gap-2 px-4 py-2 label-mono-md text-muted-foreground hover:text-primary"><ArrowLeft className="h-4 w-4" />Anterior</button>
          <div className="flex flex-wrap items-center gap-2">
            <button onClick={() => setShowChat(true)} className="focus-ring flex items-center gap-2 border border-border px-4 py-2 label-mono-md text-foreground hover:bg-[var(--surface-container)]"><Bot className="h-4 w-4" />Preguntar al asistente</button>
            <button onClick={saveAndCloseAnalysis} className="focus-ring flex items-center gap-2 border border-[var(--risk-verde)] px-4 py-2 label-mono-md text-[var(--risk-verde)] hover:bg-[var(--surface-container)]">
              <CheckCircle2 className="h-4 w-4" />Guardar y cerrar
            </button>
            <button onClick={() => setCurrentStep(4)} className="focus-ring flex items-center gap-2 bg-primary px-6 py-2 label-mono-md text-primary-foreground">
              Continuar a conexiones
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </footer>
      </div>
    </section>
  )
}
