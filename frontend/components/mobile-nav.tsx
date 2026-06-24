'use client'

import { BarChart3, FileSearch, FileText, GitBranch, LayoutDashboard, UploadCloud } from 'lucide-react'
import { useAppState } from '@/lib/app-context'
import { cn } from '@/lib/utils'

const analystItems = [
  { step: 0, label: 'Bandeja', Icon: LayoutDashboard, needsCase: false },
  { step: 1, label: 'Carga', Icon: UploadCloud, needsCase: false },
  { step: 3, label: 'Riesgo', Icon: BarChart3, needsCase: true },
  { step: 4, label: 'Conexiones', Icon: GitBranch, needsCase: true },
  { step: 5, label: 'Reporte', Icon: FileText, needsCase: true },
]

const executiveItems = [
  { step: 0, label: 'Panel', Icon: LayoutDashboard, needsCase: false },
  { step: 6, label: 'Impacto', Icon: BarChart3, needsCase: false },
  { step: 5, label: 'Reporte', Icon: FileSearch, needsCase: true },
]

export function MobileNav() {
  const { currentStep, setCurrentStep, isDataLoaded, selectedClaimId, userRole } = useAppState()
  const flowReady = isDataLoaded && selectedClaimId !== null
  const items = userRole === 'analyst' ? analystItems : executiveItems

  return (
    <nav
      aria-label="Navegacion movil principal"
      className="fixed inset-x-0 bottom-0 z-50 border-t border-border bg-background/95 px-3 pt-2 pb-[calc(0.5rem+env(safe-area-inset-bottom,0px))] shadow-[0_-10px_30px_rgba(15,23,42,0.08)] backdrop-blur-xl lg:hidden"
    >
      <div className={cn('mx-auto grid max-w-lg gap-1', items.length > 4 ? 'grid-cols-5' : 'grid-cols-4')}>
        {items.map(({ step, label, Icon, needsCase }) => {
          const disabled = needsCase && !flowReady
          const active = currentStep === step
          return (
            <button
              key={step}
              type="button"
              disabled={disabled}
              onClick={() => setCurrentStep(step)}
              aria-current={active ? 'page' : undefined}
              title={disabled ? 'Carga o sincroniza datos para habilitar este paso' : label}
              className={cn(
                'focus-ring flex min-h-12 flex-col items-center justify-center gap-1 rounded-md px-2 text-xs font-semibold transition-colors',
                active
                  ? 'bg-[var(--secondary-container)] text-[var(--on-secondary-container)]'
                  : 'text-muted-foreground hover:bg-[var(--surface-container)] hover:text-foreground',
                disabled && 'cursor-not-allowed opacity-40 hover:bg-transparent hover:text-muted-foreground',
              )}
            >
              <Icon className="h-4 w-4" aria-hidden />
              <span>{label}</span>
            </button>
          )
        })}
      </div>
    </nav>
  )
}
