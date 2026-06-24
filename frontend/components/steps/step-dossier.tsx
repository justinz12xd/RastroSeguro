'use client'

import { useEffect, useMemo, useState } from 'react'
import type { ComponentType } from 'react'
import {
  ArrowLeft,
  Bot,
  CalendarClock,
  CheckCircle2,
  FileSearch,
  Fingerprint,
  Loader2,
  Network,
  Radar,
  Scale,
  ShieldCheck,
  Sparkles,
  Workflow,
} from 'lucide-react'
import { useAppState } from '@/lib/app-context'
import { ClaimDossier, getClaimDossier } from '@/lib/api'
import { formatCurrency } from '@/lib/claims-data'
import { RiskBadge } from '@/components/ui/risk-badge'
import { cn, sanitizeAiText } from '@/lib/utils'
import { humanizeComponentKey } from '@/lib/human-labels'

const num = (value: unknown) => Number(value ?? 0)

function normalizeClaimCode(raw: string) {
  const text = String(raw || '').trim().toUpperCase().replace(/_/g, '-')
  const match = text.match(/^SIN-?(\d+)$/)
  if (match) return `SIN-${String(Number(match[1]))}`
  return text
}

function normalizeRisk(level?: string | null) {
  const value = String(level || '').toLowerCase()
  if (['critico', 'crítico', 'rojo'].includes(value)) return 'critico'
  if (['alto', 'high'].includes(value)) return 'alto'
  if (['medio', 'amarillo', 'medium'].includes(value)) return 'medio'
  if (['bajo', 'verde', 'low'].includes(value)) return 'bajo'
  return 'medio'
}

function toneClass(tone?: string | null) {
  if (tone === 'critical') return 'border-destructive bg-[var(--error-container)] text-[var(--on-error-container)]'
  if (tone === 'warning') return 'border-amber-500/40 bg-[var(--warning-container)] text-[var(--on-warning-container)]'
  if (tone === 'success') return 'border-emerald-500/40 bg-[var(--success-container)] text-[var(--on-success-container)]'
  return 'border-border bg-[var(--surface-low)] text-foreground'
}

function componentTone(score: number) {
  if (score >= 75) return 'bg-destructive'
  if (score >= 55) return 'bg-amber-500'
  if (score > 0) return 'bg-primary'
  return 'bg-muted-foreground'
}

function compactUnknown(value?: string | null) {
  return value && String(value).trim() ? value : 'No informado'
}

const COMPONENT_LABELS: Record<string, string> = {
  nlp: 'Narrativa del relato',
  'modelo ml': 'Patrones históricos',
  modelo: 'Patrones históricos',
  reglas: 'Reglas de negocio',
  anomalia: 'Comportamiento inusual',
  grafo: 'Relaciones',
  categorico: 'Contexto del caso',
}

function labelComponent(key?: string | null): string {
  if (!key) return 'N/D'
  return humanizeComponentKey(key)
}

function SignalRadar({ dossier }: { dossier: ClaimDossier }) {
  const rows = dossier.signal_radar?.length
    ? dossier.signal_radar
    : Object.entries(dossier.score_components || {}).map(([component, value]) => ({
        component,
        score: num(value),
        label: num(value) >= 55 ? 'Señal relevante' : 'Señal de apoyo',
        description: 'Factor usado para explicar este resultado.',
      }))

  return (
    <div className="institutional-card overflow-hidden">
      <div className="section-header flex items-center gap-2"><Radar className="h-4 w-4" />Señales principales</div>
      <div className="space-y-2.5 p-4">
        {rows.map((item) => {
          const score = Math.min(100, Math.max(0, num(item.score)))
          return (
            <div key={item.component} className="rounded-md border border-border bg-[var(--surface-low)] p-3">
              <div className="mb-2 flex items-start justify-between gap-3">
                <div>
                  <p className="label-mono-md font-bold uppercase text-foreground">{labelComponent(item.component)}</p>
                  <p className="mt-1 text-xs text-muted-foreground">{sanitizeAiText(item.description) || 'Factor del resultado.'}</p>
                </div>
                <div className="text-right">
                  <p className="font-display text-2xl font-semibold">{Math.round(score)}</p>
                  <p className="label-mono text-muted-foreground">{item.label || 'Señal'}</p>
                </div>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-background">
                <div className={cn('h-full rounded-full', componentTone(score))} style={{ width: `${score}%` }} />
              </div>
            </div>
          )
        })}
        <p className="text-xs text-muted-foreground">
          Señal principal: {labelComponent(dossier.main_driver?.componente)} ({Math.round(num(dossier.main_driver?.valor))})
        </p>
      </div>
    </div>
  )
}

function Timeline({ dossier }: { dossier: ClaimDossier }) {
  const fallback = [
    { title: 'Ocurrencia', date: dossier.claim.fecha_ocurrencia || 'Fecha no informada', detail: 'Evento base del caso.', tone: 'info' },
    { title: 'Reporte', date: dossier.claim.fecha_reporte || 'Fecha no informada', detail: 'Registro recibido para revisión.', tone: 'info' },
    { title: 'Resultado', date: `Puntaje ${Math.round(num(dossier.risk.score_final))}/100`, detail: dossier.risk.accion_sugerida || 'Revisión humana sugerida.', tone: 'warning' },
  ]
  const timeline = dossier.timeline?.length ? dossier.timeline : fallback

  return (
    <section className="institutional-card overflow-hidden">
      <div className="section-header flex items-center gap-2"><CalendarClock className="h-4 w-4" />Línea de tiempo del caso</div>
      <div className="p-4">
        <ol className="relative space-y-3 before:absolute before:left-4 before:top-2 before:h-[calc(100%-1rem)] before:w-px before:bg-border">
          {timeline.map((item, index) => (
            <li key={`${item.title}-${index}`} className="relative grid gap-3 pl-10 md:grid-cols-[180px_1fr]">
              <span className={cn('absolute left-0 top-1 flex h-8 w-8 items-center justify-center rounded-full border text-xs font-bold', toneClass(item.tone))}>{index + 1}</span>
              <div>
                <p className="label-mono text-muted-foreground">{item.date || 'Sin fecha'}</p>
                <p className="font-display text-lg font-semibold">{item.title}</p>
              </div>
              <p className="rounded-md border border-border bg-[var(--surface-low)] p-3 text-sm text-muted-foreground">{item.detail || 'Evento registrado en el caso.'}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  )
}

function SimilarityPanel({ dossier }: { dossier: ClaimDossier }) {
  const summary = dossier.similar_cases_summary
  const similarCases = summary?.similar_cases || []
  const recurringEntities = summary?.recurring_entities || []
  const rawConnections = dossier.advanced_evidence?.grafo?.conexiones || []

  return (
    <section className="institutional-card col-span-12 overflow-hidden">
      <div className="section-header flex items-center gap-2"><Network className="h-4 w-4" />Coincidencias y relaciones</div>
      <div className="grid gap-3 p-4 lg:grid-cols-3">
        <div className="rounded-md border border-border bg-[var(--surface-low)] p-4 lg:col-span-3">
          <p className="font-display text-xl font-semibold">{summary?.headline || 'No se encontraron coincidencias fuertes con la información actual.'}</p>
          <p className="mt-2 text-sm text-muted-foreground">
            {sanitizeAiText(dossier.advanced_evidence?.nlp?.explicacion || dossier.advanced_evidence?.grafo?.explicacion) || 'No hay evidencia suficiente para afirmar un patrón repetido.'}
          </p>
        </div>

        <div className="space-y-2">
          <p className="label-mono-md font-bold uppercase text-muted-foreground">Casos parecidos</p>
          {similarCases.length ? similarCases.map((item) => (
            <div key={`${item.id_siniestro}-${item.similarity}`} className="border border-border bg-[var(--surface-low)] p-3">
              <div className="flex items-center justify-between gap-3">
                <p className="font-mono text-sm font-semibold">{item.id_siniestro || 'Caso relacionado'}</p>
                <span className="label-mono-md font-bold text-primary">{Math.round(num(item.similarity))}%</span>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">{item.reason || 'Coincidencia comparable.'}</p>
            </div>
          )) : <EmptyMini text="No hay casos parecidos registrados para este caso." />}
        </div>

        <div className="space-y-2">
          <p className="label-mono-md font-bold uppercase text-muted-foreground">Elementos repetidos</p>
          {recurringEntities.length ? recurringEntities.map((item) => (
            <div key={`${item.entity}-${item.type}`} className="border border-border bg-[var(--surface-low)] p-3">
              <p className="font-mono text-sm font-semibold">{item.entity || 'Elemento'}</p>
              <p className="mt-1 text-xs text-muted-foreground">{item.type || 'relación'} · {num(item.count) || 'N'} aparición(es)</p>
            </div>
          )) : <EmptyMini text="Sin elementos repetidos relevantes." />}
        </div>

        <div className="space-y-2">
          <p className="label-mono-md font-bold uppercase text-muted-foreground">Conexiones detectadas</p>
          <div className="border border-border bg-[var(--surface-low)] p-4">
            <p className="font-display text-3xl font-semibold">{num(summary?.connections_count) || rawConnections.length}</p>
            <p className="mt-1 text-xs text-muted-foreground">Estas conexiones sirven como contexto, no como decisión automática.</p>
          </div>
        </div>
      </div>
    </section>
  )
}

function EmptyMini({ text }: { text: string }) {
  return <div className="border border-dashed border-border bg-[var(--surface-low)] p-3 text-xs text-muted-foreground">{text}</div>
}

export function StepDossier({ embedded = false }: { embedded?: boolean }) {
  const { selectedClaimId, selectedClaim, setCurrentStep, setShowChat, claims, setSelectedClaimId, setIsDataLoaded, userRole } = useAppState()
  const [dossier, setDossier] = useState<ClaimDossier | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchCode, setSearchCode] = useState('')
  const [searchError, setSearchError] = useState<string | null>(null)

  const isExecutive = userRole === 'executive'

  useEffect(() => {
    if (!selectedClaimId) return
    setLoading(true)
    setError(null)
    getClaimDossier(selectedClaimId)
      .then(setDossier)
      .catch((err) => setError(err instanceof Error ? err.message : 'No se pudo cargar el detalle del caso.'))
      .finally(() => setLoading(false))
  }, [selectedClaimId])

  const searchInDossier = () => {
    const query = normalizeClaimCode(searchCode)
    if (!query) return
    const found = claims.find((c) => normalizeClaimCode(String(c.id_siniestro || '')) === query)
    if (!found) {
      setSearchError(`No se encontró ${query}`)
      return
    }
    setSearchError(null)
    setSelectedClaimId(found.id_siniestro)
    setIsDataLoaded(true)
    setCurrentStep(5)
  }

  const evidence = useMemo(() => (
    dossier?.evidence.length
      ? dossier.evidence
      : [{ senal: 'Sin señales principales', mensaje: 'Completar la revisión documental y de relaciones para cerrar este caso.', puntos: 0, severidad: 'baja' }]
  ), [dossier])

  if (!selectedClaimId) {
    return (
      <section className="flex min-h-[50vh] flex-col items-center justify-center gap-4 px-4 text-center text-muted-foreground">
        <FileSearch className="h-12 w-12" />
        <p>No hay caso seleccionado para mostrar el detalle.</p>
        <button onClick={() => setCurrentStep(0)} className="bg-primary px-4 py-2 label-mono-md text-white">Ir al panel principal</button>
      </section>
    )
  }

  const risk = normalizeRisk(dossier?.risk?.nivel_riesgo || selectedClaim?.nivel_riesgo)
  const score = num(dossier?.risk?.score_final ?? selectedClaim?.score_final)

  const content = (
    <>
        {!embedded && (
        <header className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div>
            <span className="label-mono uppercase tracking-widest text-muted-foreground">Detalle del caso</span>
            <h1 className="display-heading text-2xl lg:text-4xl">Sala de revisión del caso</h1>
            <p className="mt-1 max-w-3xl text-muted-foreground">
              {isExecutive
                ? 'Una lectura general del caso: por qué importa, qué monto concentra y por qué requiere criterio humano.'
                : 'Un recorrido completo del caso: señales, fechas, relaciones, relato y próximos pasos para revisión.'}
            </p>
            <div className="mt-3 flex flex-col gap-2 md:flex-row md:items-center">
              <input
                value={searchCode}
                onChange={(e) => setSearchCode(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && searchInDossier()}
                placeholder="Buscar por código (SIN-046)"
                className="w-full border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary md:max-w-sm"
              />
              <button onClick={searchInDossier} className="border border-border px-3 py-2 label-mono-md text-muted-foreground hover:text-primary">Buscar</button>
            </div>
            {searchError && <p className="mt-2 text-xs text-destructive">{searchError}</p>}
          </div>
          <button onClick={() => setCurrentStep(isExecutive ? 0 : 3)} className="self-start border border-border px-4 py-2 label-mono-md text-muted-foreground hover:text-primary md:self-auto">
            <ArrowLeft className="mr-2 inline h-4 w-4" />{isExecutive ? 'Volver al panel principal' : 'Volver al resultado'}
          </button>
        </header>
        )}

        {embedded && (
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <input
              value={searchCode}
              onChange={(e) => setSearchCode(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && searchInDossier()}
              placeholder="Buscar por código (SIN-046)"
              className="w-full border border-border bg-background px-3 py-2 text-sm outline-none focus:border-primary sm:max-w-sm"
            />
            <button onClick={searchInDossier} className="border border-border px-3 py-2 label-mono-md text-muted-foreground hover:text-primary">Buscar caso</button>
            {searchError && <p className="text-xs text-destructive">{searchError}</p>}
          </div>
        )}

        {loading && <div className="institutional-card flex items-center gap-2 p-5 text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" /> Preparando el detalle del caso...</div>}
        {error && <div className="border border-destructive bg-[var(--error-container)] p-4 text-[var(--on-error-container)]">{error}</div>}

        {dossier && (
          <>
            <section className="dark-panel dark-panel-border relative overflow-hidden border p-5 lg:p-6">
              <div className="absolute right-0 top-0 h-48 w-48 rounded-full bg-white/10 blur-3xl" aria-hidden />
              <div className="relative grid gap-4 lg:grid-cols-[1.2fr_.8fr]">
                <div className="space-y-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="landing-tag border-white/20 bg-white/10 text-white">Caso {dossier.id_siniestro}</span>
                    <RiskBadge level={risk} className="border-white/20" />
                    <span className="label-mono-md rounded-full border border-white/20 px-3 py-1 text-white/80">Sin decisión automática</span>
                  </div>
                  <h2 className="dark-panel-heading display-heading text-3xl text-white lg:text-4xl">{dossier.headline}</h2>
                  <p className="dark-panel-muted max-w-3xl text-sm leading-7">
                    {sanitizeAiText(isExecutive
                      ? dossier.executive_takeaway || dossier.investigation_summary || dossier.explanation
                      : dossier.investigation_summary || dossier.explanation || 'Resumen preparado para revisión humana.')}
                  </p>
                  <p className="dark-panel-card rounded-md p-3 text-sm italic text-white/80">{dossier.ethical_guardrail}</p>
                </div>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
                  <HeroMetric label="Puntaje" value={`${Math.round(score)}/100`} Icon={Fingerprint} />
                  <HeroMetric label="Monto reclamado" value={formatCurrency(dossier.claim.monto_reclamado)} Icon={Scale} />
                  <HeroMetric label="Señal principal" value={labelComponent(dossier.main_driver?.componente)} Icon={Sparkles} />
                </div>
              </div>
            </section>

            <div className="grid grid-cols-12 gap-4">
              <section className="institutional-card col-span-12 overflow-hidden xl:col-span-7">
                <div className="section-header flex items-center gap-2"><Workflow className="h-4 w-4" />Resumen general</div>
                <div className="grid gap-3 p-4 md:grid-cols-3">
                  <InfoTile label="Ramo" value={compactUnknown(dossier.claim.ramo)} />
                  <InfoTile label="Ciudad" value={compactUnknown(dossier.claim.ciudad)} />
                  <InfoTile label="Proveedor" value={compactUnknown(dossier.claim.id_proveedor || dossier.claim.beneficiario)} />
                  <InfoTile label="Cobertura" value={compactUnknown(dossier.claim.cobertura)} />
                  <InfoTile label="Suma asegurada" value={formatCurrency(dossier.claim.suma_asegurada)} />
                  <InfoTile label="Proporción del reclamo" value={`${Math.round(num(dossier.claim.ratio_monto_suma) * 100)}%`} />
                </div>
              </section>
              <aside className="col-span-12 xl:col-span-5">
                <SignalRadar dossier={dossier} />
              </aside>

              <section className="col-span-12 xl:col-span-7">
                <Timeline dossier={dossier} />
              </section>

              <aside className="col-span-12 space-y-4 xl:col-span-5">
                <div className="institutional-card overflow-hidden">
                  <div className="section-header flex items-center gap-2"><ShieldCheck className="h-4 w-4" />Siguientes pasos</div>
                  <div className="space-y-2 p-4">
                    {dossier.recommended_review.map((step) => (
                      <div key={step} className="flex items-start gap-2 rounded-md border border-border bg-[var(--surface-low)] p-3 text-sm">
                        <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-[var(--risk-verde)]" />{step}
                      </div>
                    ))}
                  </div>
                </div>
              </aside>

              <section className="institutional-card col-span-12 overflow-hidden">
                <div className="section-header flex items-center gap-2"><FileSearch className="h-4 w-4" />Puntos que conviene revisar</div>
                <div className="grid gap-3 p-4 md:grid-cols-2 xl:grid-cols-3">
                  {evidence.slice(0, 6).map((item, index) => (
                    <div key={`${item.codigo || item.senal}-${index}`} className="rounded-md border border-border bg-[var(--surface-low)] p-4">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <p className="label-mono-md font-bold uppercase">{index + 1}. {item.senal || item.codigo || 'Señal detectada'}</p>
                          <p className="mt-2 text-sm text-muted-foreground">{item.mensaje || 'Punto pendiente de revisión humana.'}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-display text-2xl font-semibold text-destructive">+{Math.round(num(item.puntos))}</p>
                          <p className="label-mono text-muted-foreground">{item.severidad || 'media'}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              <SimilarityPanel dossier={dossier} />
            </div>

            {!embedded && (
              <footer className="flex flex-col gap-3 border-t border-border pt-6 sm:flex-row sm:items-center sm:justify-between">
                <button onClick={() => setCurrentStep(isExecutive ? 6 : 4)} className="px-4 py-2 label-mono-md text-muted-foreground hover:text-primary">
                  {isExecutive ? 'Ver vista ejecutiva' : 'Ver relaciones completas'}
                </button>
                <button onClick={() => setShowChat(true)} className="flex items-center justify-center gap-2 bg-primary px-6 py-2 label-mono-md text-white"><Bot className="h-4 w-4" />Preguntar al asistente</button>
              </footer>
            )}
          </>
        )}
    </>
  )

  if (embedded) {
    return <div className="space-y-4">{content}</div>
  }

  return (
    <section className="px-3 py-5 lg:px-6">
      <div className="mx-auto max-w-7xl space-y-4">
        {content}
      </div>
    </section>
  )
}

function HeroMetric({ label, value, Icon }: { label: string; value: string; Icon: ComponentType<{ className?: string }> }) {
  return (
    <div className="rounded-md border border-white/15 bg-white/10 p-3">
      <div className="flex items-center justify-between gap-3">
        <p className="label-mono-md uppercase text-white/70">{label}</p>
        <Icon className="h-5 w-5 text-white/70" />
      </div>
      <p className="mt-2 font-display text-2xl font-semibold text-white">{value}</p>
    </div>
  )
}

function InfoTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-[var(--surface-low)] p-3">
      <p className="label-mono text-muted-foreground">{label}</p>
      <p className="mt-2 truncate font-display text-xl font-semibold">{value}</p>
    </div>
  )
}
