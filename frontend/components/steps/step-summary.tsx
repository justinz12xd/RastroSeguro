'use client'

import { useEffect, useState } from 'react'
import { useAppState } from '@/lib/app-context'
import { formatCurrency } from '@/lib/claims-data'
import { GeographicContextCard } from '@/components/geographic-context-card'
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  Bot,
  CheckCircle2,
  FileText,
  Image as ImageIcon,
  Loader2,
  MapPin,
  Navigation,
  ShieldCheck,
  XCircle,
} from 'lucide-react'
import { cn } from '@/lib/utils'

function yes(value: unknown) {
  return ['si', 'sí', 'true', '1', 'yes', 'completo'].includes(String(value ?? '').trim().toLowerCase()) || value === true
}

function no(value: unknown) {
  return ['no', 'false', '0', 'incompleto'].includes(String(value ?? '').trim().toLowerCase()) || value === false
}

function documentBadge(status: 'completo' | 'pendiente' | 'inconsistente') {
  if (status === 'completo') {
    return { Icon: CheckCircle2, label: 'Verificado', className: 'bg-[var(--tertiary-fixed)] text-[var(--on-tertiary-fixed)]' }
  }
  if (status === 'inconsistente') {
    return { Icon: XCircle, label: 'Inconsistente', className: 'bg-[var(--error-container)] text-[var(--on-error-container)]' }
  }
  return { Icon: AlertTriangle, label: 'Pendiente', className: 'bg-[var(--warning-container)] text-[var(--on-warning-container)]' }
}

export function StepSummary() {
  const { selectedClaim, selectedClaimId, selectedExplanation, isLoadingExplanation, loadClaimExplanation, setCurrentStep, setShowChat } = useAppState()
  const [processing, setProcessing] = useState(false)

  useEffect(() => {
    if (selectedClaim && selectedClaimId && selectedExplanation?.id_siniestro !== selectedClaimId) {
      void loadClaimExplanation(selectedClaimId)
    }
  }, [loadClaimExplanation, selectedClaim, selectedClaimId, selectedExplanation?.id_siniestro])

  if (!selectedClaim) {
    return (
      <section className="flex min-h-[calc(100svh-4rem)] items-center justify-center px-4 py-10">
        <div className="institutional-card w-full max-w-lg p-8 text-center shadow-sm">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-[var(--surface-low)] text-primary ring-1 ring-border">
            <FileText className="h-7 w-7" />
          </div>
          <p className="label-mono-md mt-5 uppercase text-muted-foreground">Resumen del caso</p>
          <h2 className="mt-2 font-display text-2xl font-semibold text-foreground">No hay caso seleccionado</h2>
          <p className="mx-auto mt-3 max-w-sm text-sm leading-relaxed text-muted-foreground">
            Selecciona o carga un siniestro para activar el resumen, validar documentos y continuar con el análisis de riesgo.
          </p>
          <div className="mt-6 flex flex-col justify-center gap-2 sm:flex-row">
            <button onClick={() => setCurrentStep(1)} className="focus-ring inline-flex items-center justify-center gap-2 bg-primary px-5 py-2.5 label-mono-md text-primary-foreground">
              Volver al Paso 1
              <ArrowRight className="h-4 w-4" />
            </button>
            <button onClick={() => setCurrentStep(0)} className="focus-ring inline-flex items-center justify-center border border-border px-5 py-2.5 label-mono-md text-foreground hover:bg-[var(--surface-container)]">
              Ir a bandeja
            </button>
          </div>
          <p className="mt-5 rounded-md border border-border bg-[var(--surface-low)] px-3 py-2 text-xs text-muted-foreground">
            Si el panel lateral muestra un caso activo, vuelve al flujo y selecciónalo nuevamente para sincronizar la vista.
          </p>
        </div>
      </section>
    )
  }

  const next = () => {
    setProcessing(true)
    setTimeout(() => {
      setProcessing(false)
      setCurrentStep(3)
    }, 600)
  }

  const docIcon = (tipo: string) => (tipo === 'foto' || tipo === 'video' ? ImageIcon : tipo === 'telemetria' ? Navigation : FileText)
  const narrativa =
    selectedClaim.narrativa ||
    selectedClaim.descripcion ||
    selectedExplanation?.explicacion ||
    'RastroSeguro ya revisó este caso. Continúa para ver por qué fue priorizado y qué puntos conviene revisar.'

  const documentosCompletos = yes(selectedClaim.documentos_completos)
  const documentosIncompletos = no(selectedClaim.documentos_completos)
  const documentosInconsistentes = yes(selectedClaim.documentos_inconsistentes)
  const documentos = [
    {
      nombre: 'Documentos obligatorios',
      tipo: 'declaracion',
      estado: documentosIncompletos ? ('pendiente' as const) : ('completo' as const),
      detalle: documentosCompletos
        ? 'Documentos mínimos revisados por el sistema'
        : 'Faltan documentos importantes por revisar',
    },
    {
      nombre: 'Revisión de consistencia',
      tipo: 'informe',
      estado: documentosInconsistentes ? ('inconsistente' as const) : ('completo' as const),
      detalle: documentosInconsistentes
        ? 'Fechas, valores o soportes requieren revisión manual'
        : 'No se encontraron diferencias relevantes en la documentación',
    },
    {
      nombre: 'Explicación del resultado',
      tipo: 'telemetria',
      estado: 'completo' as const,
      detalle: 'Resumen de los factores que ayudan a entender este resultado',
    },
  ]

  return (
    <section className="px-3 py-5 lg:px-6">
      <div className="mx-auto max-w-6xl space-y-4">
        <header className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div>
            <h1 className="display-heading text-3xl lg:text-4xl">Paso 2: Resumen del caso</h1>
            <p className="mt-2 text-base text-readable text-muted-foreground">
              Revisión clara del caso antes de pasar a la explicación del resultado.
            </p>
          </div>
          <div className="bg-primary px-4 py-2 text-primary-foreground">
            <span className="label-mono-md">CASO: </span>
            <span className="label-mono-md font-bold tracking-widest">{selectedClaim.id_siniestro}</span>
          </div>
        </header>

        <div className="grid grid-cols-12 gap-4">
          <div className="col-span-12 space-y-4 lg:col-span-8">
            <div className="institutional-card overflow-hidden">
              <div className="section-header">Datos principales del caso</div>
              <table className="zebra w-full text-left">
                <thead>
                  <tr className="border-b border-border bg-[var(--surface-low)]">
                    <th className="label-mono px-4 py-2.5 text-foreground">CATEGORÍA</th>
                    <th className="label-mono px-4 py-2.5 text-foreground">DETALLE</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td className="px-4 py-2.5 text-sm font-semibold">Ramo</td>
                    <td className="px-4 py-2.5 text-sm text-muted-foreground">{selectedClaim.ramo || 'No informado'}</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2.5 text-sm font-semibold">Monto reclamado</td>
                    <td className="px-4 py-2.5 font-mono text-sm">
                      {selectedClaim.monto_reclamado != null ? formatCurrency(selectedClaim.monto_reclamado) : 'No disponible'}
                    </td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2.5 text-sm font-semibold">Cobertura</td>
                    <td className="px-4 py-2.5">
                      <span className="bg-[var(--secondary-container)] px-2 py-1 label-mono font-bold uppercase text-[var(--on-secondary-container)]">
                        {selectedClaim.cobertura || 'Cobertura no informada'}
                      </span>
                    </td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2.5 text-sm font-semibold">Ciudad</td>
                    <td className="flex items-center gap-2 px-4 py-2.5 text-sm">
                      <MapPin className="h-4 w-4" />
                      {selectedClaim.ciudad || 'N/D'}, Ecuador
                    </td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2.5 text-sm font-semibold">Proveedor</td>
                    <td className="px-4 py-2.5 font-mono text-sm">{selectedClaim.id_proveedor || 'N/D'}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="institutional-card overflow-hidden">
              <div className="section-header flex items-center justify-between">
                <span>Relato del caso</span>
                <FileText className="h-4 w-4 text-muted-foreground" />
              </div>
              <div className="p-4">
                <p className="rounded-md border border-border bg-[var(--surface-low)] p-4 text-base italic leading-relaxed text-readable">
                  &ldquo;{narrativa}&rdquo;
                </p>
              </div>
            </div>

            <div className="institutional-card overflow-hidden">
              <div className="section-header flex items-center justify-between gap-2">
                <span>Revisión de documentos</span>
                <span className="label-mono text-sm text-muted-foreground">
                  {documentosCompletos && !documentosInconsistentes ? 'Sin hallazgos clave' : 'Requiere revisión'}
                </span>
              </div>
              <div className="divide-y divide-border">
                {documentos.map((doc, i) => {
                  const Icon = docIcon(doc.tipo)
                  const Badge = documentBadge(doc.estado)
                  return (
                    <div key={i} className="flex items-center justify-between gap-4 p-3 hover:bg-[var(--surface-low)]">
                      <div className="flex items-center gap-4">
                        <Icon className="h-5 w-5 shrink-0" />
                        <div>
                          <p className="font-semibold">{doc.nombre}</p>
                          <p className="label-mono text-sm text-muted-foreground">{doc.detalle}</p>
                        </div>
                      </div>
                      <span className={cn('flex shrink-0 items-center gap-1 px-2 py-1 label-mono-md font-bold uppercase', Badge.className)}>
                        <Badge.Icon className="h-4 w-4" />
                        {Badge.label}
                      </span>
                    </div>
                  )
                })}
              </div>
              <div className="grid gap-3 border-t border-border bg-[var(--surface-low)] p-3 sm:grid-cols-2">
                <div>
                  <p className="label-mono text-muted-foreground">Documentos recibidos</p>
                  <p className="font-mono text-sm text-foreground">{String(selectedClaim.documentos_completos ?? 'No informado')}</p>
                </div>
                <div>
                  <p className="label-mono text-muted-foreground">Diferencias encontradas</p>
                  <p className="font-mono text-sm text-foreground">{String(selectedClaim.documentos_inconsistentes ?? 'No informado')}</p>
                </div>
              </div>
            </div>
          </div>

          <aside className="col-span-12 space-y-4 lg:col-span-4">
            <div className="dark-panel dark-panel-border border p-4">
              <h3 className="dark-panel-kicker label-mono-md font-bold uppercase tracking-widest">Listo para continuar</h3>
              <div className="mt-4">
                <div className="flex items-end justify-between">
                  <span className="dark-panel-heading font-display text-3xl font-semibold">
                    {isLoadingExplanation ? 'Actualizando' : 'Listo'}
                  </span>
                  <span className="label-mono-md text-[var(--tertiary-fixed)]">Información lista</span>
                </div>
                <div className="mt-2 h-2 bg-[var(--surface-high)]">
                  <div className="h-full bg-[var(--tertiary-fixed-dim)]" style={{ width: selectedExplanation ? '100%' : '75%' }} />
                </div>
              </div>
              <p className="dark-panel-muted mt-4 text-sm leading-relaxed">
                La información básica del caso ya está reunida. Ahora puedes ver por qué fue marcado para revisión.
              </p>
              <button
                onClick={next}
                className="focus-ring mt-4 flex w-full items-center justify-center gap-2 bg-primary py-2.5 label-mono-md font-bold uppercase text-primary-foreground hover:opacity-95"
              >
                {processing ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Continuar a la explicación'}
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
            <GeographicContextCard ciudad={selectedClaim.ciudad} />
          </aside>
        </div>

        <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-6">
          <button onClick={() => setCurrentStep(1)} className="focus-ring flex items-center gap-2 px-4 py-2 label-mono-md text-muted-foreground hover:text-primary">
            <ArrowLeft className="h-4 w-4" />
            Anterior
          </button>
          <div className="hidden items-center gap-2 sm:flex">
            <ShieldCheck className="h-4 w-4 text-[var(--on-tertiary-fixed)]" />
            <span className="label-mono text-sm text-muted-foreground">Apoya la revisión humana: no decide pagos ni rechazos.</span>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => setShowChat(true)}
              className="focus-ring flex items-center gap-2 border border-border px-4 py-2 label-mono-md text-foreground hover:bg-[var(--surface-container)]"
            >
              <Bot className="h-4 w-4" />
              Preguntar al asistente
            </button>
            <button onClick={next} className="focus-ring flex items-center gap-2 bg-primary px-6 py-2 label-mono-md text-primary-foreground">
              Siguiente
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </footer>
      </div>
    </section>
  )
}
