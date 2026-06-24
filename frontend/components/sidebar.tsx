'use client'

import Link from 'next/link'
import {
  ArrowRight,
  BarChart3,
  ClipboardList,
  FileSearch,
  GitBranch,
  LayoutDashboard,
  LockKeyhole,
  RotateCcw,
  Shield,
  Star,
  Terminal,
  UploadCloud,
} from 'lucide-react'
import { useAppState } from '@/lib/app-context'
import { cn } from '@/lib/utils'

function NavButton({
  active,
  disabled,
  icon: Icon,
  label,
  onClick,
  disabledReason,
}: {
  active: boolean
  disabled?: boolean
  icon: typeof LayoutDashboard
  label: string
  onClick: () => void
  disabledReason?: string
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={() => !disabled && onClick()}
      title={disabled ? disabledReason || 'Carga o sincroniza datos para habilitar este paso' : label}
      className={cn(
        'font-display flex w-full items-center gap-2.5 rounded-md px-2.5 py-2.5 text-left text-[13px] font-semibold transition-colors',
        active
          ? 'bg-[var(--accent)] font-bold text-[var(--accent-foreground)] ring-1 ring-inset ring-border'
          : 'text-muted-foreground opacity-80 hover:bg-[var(--surface-high)] hover:text-foreground hover:opacity-100',
        disabled && 'cursor-not-allowed opacity-40 hover:bg-transparent hover:text-muted-foreground',
      )}
    >
      <Icon className="h-4 w-4 shrink-0" aria-hidden />
      {label}
    </button>
  )
}

export function Sidebar() {
  const { currentStep, setCurrentStep, isDataLoaded, selectedClaimId, setSelectedClaimId, setIsDataLoaded, claims, userRole, resetUserRole } = useAppState()
  const inFlow = currentStep > 0 && currentStep < 5
  const flowReady = isDataLoaded && selectedClaimId !== null
  const isAnalyst = userRole === 'analyst'
  const executiveReportReady = flowReady || (!isAnalyst && claims.length > 0)
  const roleLabel = isAnalyst ? 'Analista antifraude' : 'Vista ejecutiva'

  const openExecutiveReport = () => {
    if (!selectedClaimId && claims.length > 0) {
      setSelectedClaimId(claims[0].id_siniestro)
      setIsDataLoaded(true)
    }
    setCurrentStep(5)
  }

  return (
    <aside className="fixed left-0 top-0 hidden h-screen w-64 flex-col border-r border-border bg-[var(--surface-low)] p-3 lg:flex">
      <div className="mb-6 flex flex-col gap-1">
        <Link href="/platform" onClick={() => setCurrentStep(0)} className="font-display text-xl font-bold tracking-tight text-primary">
          RastroSeguro
        </Link>
        <span className="font-display text-xs font-semibold uppercase tracking-[0.08em] text-muted-foreground">
          Unidad de inteligencia de riesgo
        </span>
        <button
          type="button"
          onClick={resetUserRole}
          className="mt-2 inline-flex items-center gap-2 self-start rounded-full border border-border bg-[var(--surface-high)] px-2.5 py-1 text-[11px] font-semibold text-muted-foreground hover:text-foreground"
        >
          <RotateCcw className="h-3.5 w-3.5" aria-hidden />
          {roleLabel}
        </button>
      </div>

      <nav className="flex-1 space-y-4" aria-label="Navegacion principal">
        <NavButton
          active={currentStep === 0}
          icon={LayoutDashboard}
          label={isAnalyst ? 'Bandeja operativa' : 'Centro de Control'}
          onClick={() => setCurrentStep(0)}
        />

        {isAnalyst ? (
          <>
            <div className="rounded-md border border-border bg-[var(--surface-high)] p-3">
              <p className="label-mono-md font-bold uppercase text-foreground">Flujo del analista</p>
              <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                Carga datos, valida casos y revisa siniestros con explicabilidad completa.
              </p>
              <button
                type="button"
                onClick={() => setCurrentStep(1)}
                className="focus-ring mt-3 flex w-full items-center justify-center gap-2 bg-primary px-3 py-2 label-mono-md font-bold uppercase text-primary-foreground hover:opacity-95"
              >
                {inFlow ? 'Volver al flujo' : 'Cargar datos'}
                <ArrowRight className="h-4 w-4" aria-hidden />
              </button>
              <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
                <span className={cn('h-2 w-2 shrink-0 rounded-full', flowReady ? 'bg-[var(--tertiary-fixed-dim)]' : 'bg-border')} />
                {flowReady ? `Caso activo: ${selectedClaimId}` : 'Sin caso activo aun'}
              </div>
            </div>

            <div className="space-y-2">
              <p className="label-mono-md px-3 font-bold uppercase text-muted-foreground">Revision tecnica</p>
              <NavButton active={currentStep === 1} icon={UploadCloud} label="Carga de datos" onClick={() => setCurrentStep(1)} />
              <NavButton active={currentStep === 2} disabled={!flowReady} icon={ClipboardList} label="Resumen del caso" onClick={() => setCurrentStep(2)} />
              <NavButton active={currentStep === 3} disabled={!flowReady} icon={BarChart3} label="Resultado y motivos" onClick={() => setCurrentStep(3)} />
              <NavButton active={currentStep === 4} disabled={!flowReady} icon={GitBranch} label="Conexiones del caso" onClick={() => setCurrentStep(4)} />
              <NavButton active={currentStep === 5} disabled={!flowReady} icon={FileSearch} label="Reporte y cierre" onClick={() => setCurrentStep(5)} />
            </div>
          </>
        ) : (
          <>
            <div className="rounded-md border border-border bg-[var(--surface-high)] p-3">
              <p className="label-mono-md font-bold uppercase text-foreground">Vista ejecutiva</p>
              <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                Revisa indicadores, impacto de negocio, casos criticos y narrativa para decidir.
              </p>
              <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
                <span className={cn('h-2 w-2 shrink-0 rounded-full', flowReady ? 'bg-[var(--tertiary-fixed-dim)]' : 'bg-border')} />
                {flowReady ? `Caso seleccionado: ${selectedClaimId}` : 'Esperando datos del analista'}
              </div>
            </div>

            <div className="space-y-2">
              <p className="label-mono-md px-3 font-bold uppercase text-muted-foreground">Vista ejecutiva</p>
              <NavButton active={currentStep === 6} icon={Star} label="Impacto ejecutivo" onClick={() => setCurrentStep(6)} />
              <NavButton active={currentStep === 5} disabled={!executiveReportReady} icon={FileSearch} label="Reporte / Caso" onClick={openExecutiveReport} disabledReason="Selecciona un caso o espera datos del analista para abrir el reporte" />
            </div>
          </>
        )}
      </nav>

      <div className="mt-auto space-y-2 border-t border-border pt-4">
        <button type="button" disabled title="Disponible en una siguiente versión" className="font-display flex w-full cursor-not-allowed items-center gap-3 rounded-md px-2.5 py-2 text-[13px] font-semibold text-muted-foreground opacity-55">
          <Shield className="h-4 w-4" aria-hidden /> Registros de seguridad
        </button>
        <button type="button" disabled title="Disponible en una siguiente versión" className="font-display flex w-full cursor-not-allowed items-center gap-3 rounded-md px-2.5 py-2 text-[13px] font-semibold text-muted-foreground opacity-55">
          <Terminal className="h-4 w-4" aria-hidden /> Documentación
        </button>
        <div className="mt-3 rounded-md border border-border bg-[var(--surface-high)] p-2.5">
          <div className="mb-2 flex items-center gap-2 text-foreground">
            <LockKeyhole className="h-3.5 w-3.5 shrink-0" aria-hidden />
            <span className="label-mono-md font-bold">Aviso ético</span>
          </div>
          <p className="text-xs leading-snug text-muted-foreground">El asistente alerta y explica. No acusa ni rechaza reclamos.</p>
        </div>
      </div>
    </aside>
  )
}
