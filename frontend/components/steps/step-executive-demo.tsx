'use client'

import { useEffect, useState } from 'react'
import { ArrowLeft, Bot, BriefcaseBusiness, CircleDollarSign, FileText, Loader2, PlayCircle, ShieldCheck, Star, Target } from 'lucide-react'
import { BusinessImpact, StarCasesResponse, getBusinessImpact, getStarCases } from '@/lib/api'
import { useAppState } from '@/lib/app-context'
import { formatCurrency } from '@/lib/claims-data'
import { RiskBadge } from '@/components/ui/risk-badge'

const num = (value: unknown) => Number(value ?? 0)

function normalizeRisk(level?: string | null) {
  const value = String(level || '').toLowerCase()
  if (['critico', 'critico', 'rojo'].includes(value)) return 'critico'
  if (['alto', 'high'].includes(value)) return 'alto'
  if (['medio', 'amarillo', 'medium'].includes(value)) return 'medio'
  if (['bajo', 'verde', 'low'].includes(value)) return 'bajo'
  return 'medio'
}

export function StepExecutiveDemo() {
  const { setCurrentStep, setSelectedClaimId, setIsDataLoaded, setShowChat } = useAppState()
  const [impact, setImpact] = useState<BusinessImpact | null>(null)
  const [stars, setStars] = useState<StarCasesResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    Promise.all([getBusinessImpact(0.1), getStarCases()])
      .then(([impactData, starData]) => {
        setImpact(impactData)
        setStars(starData)
      })
        .catch((err) => setError(err instanceof Error ? err.message : 'No se pudo cargar esta vista.'))
      .finally(() => setLoading(false))
  }, [])

  const openCase = (id: string) => {
    setSelectedClaimId(id)
    setIsDataLoaded(true)
    setCurrentStep(5)
  }

  return (
    <section className="px-3 py-5 lg:px-6">
      <div className="mx-auto max-w-7xl space-y-4">
        <header className="grid gap-4 lg:grid-cols-[1.2fr_.8fr]">
          <div className="dark-panel dark-panel-border border p-6">
            <div className="dark-panel-kicker flex items-center gap-2">
              <Star className="h-5 w-5" />
              <span className="label-mono-md uppercase">Resumen para decisión</span>
            </div>
            <h1 className="dark-panel-heading display-heading mt-3 text-3xl lg:text-4xl">Casos prioritarios e impacto esperado</h1>
            <p className="dark-panel-muted mt-2 max-w-2xl text-sm">
              Vista general para revisar exposición, casos relevantes y puntos que merecen atención.
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <button onClick={() => setShowChat(true)} className="dark-panel-cta inline-flex items-center gap-2 px-4 py-2 label-mono-md font-bold uppercase">
                <Bot className="h-4 w-4" />
                Preguntar al asistente
              </button>
              <button onClick={() => setCurrentStep(0)} className="inline-flex items-center gap-2 border border-[var(--primary-fixed-dim)] px-4 py-2 label-mono-md font-bold uppercase text-white">
                <ArrowLeft className="h-4 w-4" />
                Panel principal
              </button>
            </div>
          </div>
          <div className="institutional-card p-4">
            <div className="flex items-start gap-3">
              <ShieldCheck className="h-8 w-8 text-[var(--risk-verde)]" />
              <div>
                <p className="label-mono-md font-bold uppercase">Criterio de uso</p>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                  RastroSeguro no promete ahorros automáticos ni confirma fraude. Señala prioridades para revisión humana y muestra evidencia verificable.
                </p>
              </div>
            </div>
            {impact && <p className="mt-5 rounded-md border border-border bg-[var(--surface-low)] p-3 text-sm italic text-muted-foreground">{impact.mensaje}</p>}
          </div>
        </header>

        {loading && (
          <div className="institutional-card flex items-center gap-2 p-5 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Preparando información...
          </div>
        )}
        {error && <div className="border border-destructive bg-[var(--error-container)] p-4 text-[var(--on-error-container)]">{error}</div>}

        {impact && (
          <div className="grid gap-4 md:grid-cols-4">
            <Kpi label="Siniestros" value={impact.total_siniestros.toLocaleString()} Icon={FileText} />
            <Kpi label="Casos rojos" value={impact.casos_rojos.toLocaleString()} Icon={Target} />
            <Kpi label="Casos a revisar primero" value={impact.casos_a_revisar_top_percent.toLocaleString()} Icon={BriefcaseBusiness} />
            <Kpi label="Monto priorizado" value={formatCurrency(impact.monto_priorizado_top_percent)} Icon={CircleDollarSign} />
          </div>
        )}

        <div className="grid grid-cols-12 gap-4">
          <section className="institutional-card col-span-12 overflow-hidden xl:col-span-8">
            <div className="section-header flex items-center gap-2">
              <Star className="h-4 w-4" />
              Casos prioritarios para revisión
            </div>
            <div className="divide-y divide-border">
              {(stars?.cases || []).map((item) => {
                const risk = normalizeRisk(item.nivel_riesgo)
                return (
                  <button
                    key={`${item.tipo}-${item.id_siniestro}`}
                    onClick={() => openCase(item.id_siniestro)}
                    className="grid w-full gap-2 p-3 text-left transition-colors hover:bg-[var(--surface-low)] md:grid-cols-[1fr_auto]"
                  >
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="bg-[var(--surface-high)] px-2 py-1 label-mono-md font-bold uppercase">{item.tipo}</span>
                        <span className="font-mono text-sm font-semibold">{item.id_siniestro}</span>
                        <RiskBadge level={risk} size="sm" />
                      </div>
                      <p className="mt-2 text-sm font-medium">{item.por_que_destaca}</p>
                      <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{item.explicacion_demo || 'Caso preparado para revisión.'}</p>
                    </div>
                    <div className="text-left md:text-right">
                      <p className="font-display text-2xl font-semibold">{Math.round(num(item.score_final))}</p>
                      <p className="label-mono text-muted-foreground">{formatCurrency(item.monto_reclamado)}</p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {item.ramo || 'N/D'} / {item.ciudad || 'N/D'}
                      </p>
                    </div>
                  </button>
                )
              })}
            </div>
          </section>

          <aside className="institutional-card col-span-12 overflow-hidden xl:col-span-4">
            <div className="section-header flex items-center gap-2">
              <PlayCircle className="h-4 w-4" />
              Recorrido sugerido
            </div>
            <ol className="space-y-2 p-4 text-sm">
              {[
                'Abrir un caso rojo evidente y mostrar sus señales y documentos.',
                'Abrir un caso rojo no evidente y explicar sus relaciones y su relato.',
                'Revisar un caso amarillo con criterio humano: es una alerta, no una acusación.',
                'Preguntar al asistente qué proveedores concentran más alertas.',
                'Simular un caso nuevo ocurrido cerca del inicio de la póliza.',
              ].map((step, index) => (
                <li key={step} className="flex gap-3 border border-border bg-[var(--surface-low)] p-3">
                  <span className="label-mono-md font-bold text-primary">{index + 1}</span>
                  {step}
                </li>
              ))}
            </ol>
          </aside>
        </div>
      </div>
    </section>
  )
}

function Kpi({ label, value, Icon }: { label: string; value: string; Icon: React.ComponentType<{ className?: string }> }) {
  return (
    <div className="institutional-card p-4">
      <div className="flex items-center justify-between">
        <p className="label-mono-md uppercase text-muted-foreground">{label}</p>
        <Icon className="h-5 w-5 text-[var(--on-secondary-container)]" />
      </div>
      <p className="mt-2 font-display text-2xl font-semibold">{value}</p>
    </div>
  )
}
