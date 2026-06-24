'use client'

import { useEffect, useMemo, useState } from 'react'
import { Bell, CircleUserRound, MessageCircle, Search } from 'lucide-react'
import { useAppState } from '@/lib/app-context'
import { ThemeToggle } from '@/components/theme-toggle'
import { HelpPanel } from '@/components/help-panel'
import { cn } from '@/lib/utils'

export function Header() {
  const { currentStep, setCurrentStep, isDataLoaded, selectedClaimId, setSelectedClaimId, setIsDataLoaded, claims, setShowCommandBar, setShowChat, showChat, userRole, resetUserRole } = useAppState()
  const isAnalyst = userRole === 'analyst'
  const roleLabel = isAnalyst ? 'Analista' : 'Ejecutivo'
  const flowReady = isDataLoaded && selectedClaimId !== null
  const executiveReportReady = flowReady || (!isAnalyst && claims.length > 0)
  const [shortcutLabel, setShortcutLabel] = useState('Ctrl K')

  const tabs = useMemo(() => {
    if (isAnalyst) {
      return [
        { step: 1, label: 'Carga', enabled: true },
        { step: 2, label: 'Resumen', enabled: flowReady },
        { step: 3, label: 'Riesgo', enabled: flowReady },
        { step: 4, label: 'Relaciones', enabled: flowReady },
      ]
    }
    return [
      { step: 0, label: 'Panel', enabled: true },
      { step: 6, label: 'Impacto', enabled: true },
      { step: 5, label: 'Reporte', enabled: executiveReportReady },
    ]
  }, [executiveReportReady, flowReady, isAnalyst])

  const openTab = (step: number) => {
    if (!isAnalyst && step === 5 && !selectedClaimId && claims.length > 0) {
      setSelectedClaimId(claims[0].id_siniestro)
      setIsDataLoaded(true)
    }
    setCurrentStep(step)
  }

  useEffect(() => {
    if (typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform)) {
      setShortcutLabel('Cmd K')
    }
  }, [])

  return (
    <header className="sticky top-0 z-40 flex min-h-12 w-full items-center justify-between border-b border-border bg-background/92 px-3 pt-[env(safe-area-inset-top,0px)] backdrop-blur-xl lg:px-6">
      <div className="flex min-w-0 items-center gap-4">
        <span className="font-display text-lg font-bold tracking-tight text-primary lg:hidden">RastroSeguro</span>
        <div className="hidden items-center gap-2 xl:flex">
          <span className="label-mono-md uppercase text-muted-foreground">
            {isAnalyst ? 'Flujo analista' : 'Vista ejecutiva'}
          </span>
          <span className="h-1.5 w-1.5 rounded-full bg-[var(--tertiary-fixed-dim)]" />
          <span className="label-mono text-muted-foreground">
            {isAnalyst ? 'Carga, revisión y expediente' : 'Indicadores, impacto y caso foco'}
          </span>
        </div>
        <nav className="hidden items-center gap-4 md:flex" aria-label="Navegacion superior por perfil">
          {tabs.map((tab) => (
            <button
              key={tab.step}
              disabled={!tab.enabled}
              aria-current={currentStep === tab.step ? 'page' : undefined}
              onClick={() => tab.enabled && openTab(tab.step)}
              title={tab.enabled ? tab.label : 'Carga o sincroniza datos para habilitar este paso'}
              className={cn(
                'focus-ring rounded-sm pb-1 font-display text-[13px] font-semibold transition-colors',
                currentStep === tab.step ? 'border-b-2 border-primary text-primary' : 'text-foreground hover:text-primary',
                !tab.enabled && 'cursor-not-allowed text-muted-foreground hover:text-muted-foreground',
              )}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <div className="flex items-center gap-2">
        <HelpPanel />
        <button
          type="button"
          onClick={() => setShowChat(!showChat)}
          aria-pressed={showChat}
          aria-label={showChat ? 'Cerrar chat lateral' : 'Abrir chat lateral'}
          title={showChat ? 'Cerrar asistente' : 'Abrir asistente lateral'}
          className={cn(
            'focus-ring flex items-center gap-2 rounded-md border px-2.5 py-1.5 text-xs font-semibold transition-colors',
            showChat
              ? 'border-primary bg-primary/10 text-primary'
              : 'border-primary bg-primary text-primary-foreground shadow-sm hover:opacity-95',
          )}
        >
          <MessageCircle className="h-4 w-4 shrink-0" />
          <span className="hidden sm:inline">{showChat ? 'Cerrar chat' : 'Abrir chat'}</span>
        </button>
        <button
          type="button"
          onClick={() => setShowCommandBar(true)}
          className="focus-ring hidden items-center gap-2 rounded-md border border-border bg-[var(--surface-low)] px-2.5 py-1 text-xs text-muted-foreground transition-colors hover:border-primary hover:text-foreground sm:flex"
          aria-label="Preguntar al agente antifraude"
        >
          <Search className="h-4 w-4" />
          <span className="hidden md:inline">Preguntar al asistente</span>
          <kbd className="label-mono rounded border border-border bg-background px-1.5 py-0.5 text-[10px] text-muted-foreground">
            {shortcutLabel}
          </kbd>
        </button>
        <button
          type="button"
          onClick={() => setShowCommandBar(true)}
          className="focus-ring rounded-md p-1.5 text-foreground hover:bg-[var(--surface-container)] sm:hidden"
          aria-label="Preguntar al agente antifraude"
        >
          <Search className="h-5 w-5" />
        </button>
        <ThemeToggle />
        <button type="button" disabled aria-label="Notificaciones" title="Sin notificaciones pendientes" className="rounded-md p-1.5 text-muted-foreground opacity-60">
          <Bell className="h-5 w-5" />
        </button>
        <button
          type="button"
          onClick={resetUserRole}
          className="focus-ring flex items-center gap-2 rounded-md px-2 py-1 hover:bg-[var(--surface-container)]"
          title="Cambiar perfil de usuario"
        >
          <CircleUserRound className="h-5 w-5 text-foreground" aria-hidden />
          <span className="font-display hidden text-xs font-semibold text-foreground sm:inline">{roleLabel}</span>
        </button>
      </div>
    </header>
  )
}
