'use client'

import { BookOpen, CheckCircle2, FileSearch, HelpCircle, Route, ShieldCheck } from 'lucide-react'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { useAppState } from '@/lib/app-context'
import { cn } from '@/lib/utils'

const analystPath = [
  ['1', 'Cargar datos', 'Sube la base de siniestros para iniciar la revisión.'],
  ['2', 'Elegir caso', 'Selecciona un siniestro activo para revisar.'],
  ['3', 'Entender riesgo', 'Lee el puntaje, las reglas, documentos, narrativa y red de relaciones.'],
  ['4', 'Cerrar evidencia', 'Usa el expediente para dejar una recomendación trazable.'],
]

const executivePath = [
  ['1', 'Ver panorama', 'Revisa volumen, monto expuesto y casos de mayor prioridad.'],
  ['2', 'Medir impacto', 'Identifica concentraciones por proveedor, ciudad o ramo.'],
  ['3', 'Abrir caso foco', 'Entra al expediente solo cuando necesites detalle verificable.'],
]

const glossary = [
  ['Puntaje de riesgo', 'Calificación de 0 a 100. Un valor alto no significa fraude confirmado.'],
  ['Semáforo', 'Rojo, amarillo o verde para priorizar revisión humana.'],
  ['Red de relaciones', 'Mapa de conexiones entre siniestros, proveedores, ciudades y patrones.'],
  ['Expediente', 'Resumen trazable del caso con alertas y evidencia para revisar.'],
]

export function HelpPanel() {
  const { userRole, isDataLoaded, selectedClaimId, setCurrentStep } = useAppState()
  const isAnalyst = userRole === 'analyst'
  const path = isAnalyst ? analystPath : executivePath
  const hasCase = isDataLoaded && selectedClaimId !== null

  return (
    <Dialog>
      <DialogTrigger asChild>
        <button
          type="button"
          className="focus-ring flex items-center gap-2 rounded-md border border-border bg-[var(--surface-low)] px-2.5 py-1.5 text-sm font-semibold text-foreground transition-colors hover:border-primary hover:bg-[var(--surface-container)] md:px-3"
          aria-label="Abrir guía de uso"
        >
          <HelpCircle className="h-4 w-4" aria-hidden />
          <span className="hidden md:inline">Guía</span>
        </button>
      </DialogTrigger>
      <DialogContent className="max-h-[88vh] overflow-y-auto sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle className="display-heading text-2xl">Cómo usar RastroSeguro</DialogTitle>
          <DialogDescription>
            Ruta rápida para entender la plataforma sin conocer el sistema antes.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 lg:grid-cols-[1.05fr_.95fr]">
          <section className="institutional-card overflow-hidden">
            <div className="section-header flex items-center gap-2">
              <Route className="h-4 w-4" aria-hidden />
              Ruta recomendada
            </div>
            <ol className="divide-y divide-border">
              {path.map(([number, title, body]) => (
                <li key={number} className="flex gap-3 p-4">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary label-mono-md text-primary-foreground">
                    {number}
                  </span>
                  <span>
                    <span className="block font-display text-base font-semibold text-foreground">{title}</span>
                    <span className="mt-1 block text-sm leading-relaxed text-muted-foreground">{body}</span>
                  </span>
                </li>
              ))}
            </ol>
          </section>

          <section className="grid gap-4">
            <div className="institutional-card p-4">
              <div className="flex items-start gap-3">
                <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-[var(--risk-verde)]" aria-hidden />
                <div>
                  <p className="font-display font-semibold text-foreground">Regla principal</p>
                  <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                    El sistema prioriza y explica. No acusa fraude, no rechaza reclamos y no reemplaza la decisión humana.
                  </p>
                </div>
              </div>
            </div>

            <div className="institutional-card p-4">
              <div className="flex items-start gap-3">
                <FileSearch className="mt-0.5 h-5 w-5 shrink-0 text-primary" aria-hidden />
                <div>
                  <p className="font-display font-semibold text-foreground">Estado actual</p>
                  <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                    {hasCase
                      ? `Hay un caso activo: ${selectedClaimId}. Ya puedes revisar resumen, riesgo, relaciones y expediente.`
                      : isAnalyst
                        ? 'Todavía no hay caso activo. Empieza cargando los datos.'
                        : 'Todavía no hay caso activo. Puedes revisar el panel, pero el expediente se activa con datos cargados.'}
                  </p>
                </div>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => setCurrentStep(isAnalyst ? 1 : 0)}
                  className="focus-ring rounded-md bg-primary px-3 py-2 label-mono-md font-bold uppercase text-primary-foreground"
                >
                  {isAnalyst ? 'Ir A Carga' : 'Ir Al Panel'}
                </button>
                <button
                  type="button"
                  disabled={!hasCase}
                  onClick={() => setCurrentStep(5)}
                  className={cn(
                    'focus-ring rounded-md border border-border px-3 py-2 label-mono-md font-bold uppercase text-foreground',
                    !hasCase && 'cursor-not-allowed opacity-50',
                  )}
                >
                  Abrir Expediente
                </button>
              </div>
            </div>
          </section>
        </div>

        <section className="institutional-card overflow-hidden">
          <div className="section-header flex items-center gap-2">
            <BookOpen className="h-4 w-4" aria-hidden />
            Glosario simple
          </div>
          <div className="grid gap-0 divide-y divide-border md:grid-cols-2 md:divide-x md:divide-y-0">
            {glossary.map(([term, definition]) => (
              <div key={term} className="p-4">
                <p className="flex items-center gap-2 font-display font-semibold text-foreground">
                  <CheckCircle2 className="h-4 w-4 text-[var(--risk-verde)]" aria-hidden />
                  {term}
                </p>
                <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{definition}</p>
              </div>
            ))}
          </div>
        </section>
      </DialogContent>
    </Dialog>
  )
}
