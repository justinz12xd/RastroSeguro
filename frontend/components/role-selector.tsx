'use client'

import { ArrowRight, BarChart3, CheckCircle2, ShieldCheck, UploadCloud, UsersRound } from 'lucide-react'
import { useAppState, type UserRole } from '@/lib/app-context'

const roles: Array<{
  id: UserRole
  title: string
  eyebrow: string
  description: string
  bullets: string[]
  cta: string
  icon: typeof ShieldCheck
}> = [
  {
    id: 'analyst',
    title: 'Analista Antifraude',
    eyebrow: 'Perfil operativo',
    description: 'Prepara datos, selecciona casos y revisa explicaciones con trazabilidad por siniestro.',
    bullets: ['Cargar la cartera de siniestros', 'Validar datos y seleccionar caso foco', 'Investigar puntaje, documentos y red de relaciones'],
    cta: 'Entrar al flujo operativo',
    icon: UploadCloud,
  },
  {
    id: 'executive',
    title: 'Vista Ejecutiva',
    eyebrow: 'Perfil ejecutivo',
    description: 'Entra directo al panorama consolidado para revisar exposicion, concentraciones y casos prioritarios.',
    bullets: ['Ver indicadores y concentracion de alertas', 'Revisar impacto y casos principales', 'Consultar resumen para gerencia o auditoria'],
    cta: 'Entrar al panel ejecutivo',
    icon: BarChart3,
  },
]

export function RoleSelector() {
  const { selectUserRole } = useAppState()

  return (
    <main className="min-h-screen bg-background px-4 py-10 text-foreground lg:px-8">
      <div className="mx-auto grid min-h-[calc(100vh-5rem)] max-w-6xl items-center gap-10 lg:grid-cols-[.82fr_1.18fr]">
        <header className="space-y-5">
          <div className="inline-flex items-center gap-2 rounded-full border border-border bg-[var(--surface-low)] px-3 py-1 label-mono-md font-bold uppercase text-muted-foreground">
            <UsersRound className="h-4 w-4" aria-hidden /> Experiencia por rol
          </div>
          <div>
            <h1 className="display-heading text-balance text-4xl lg:text-6xl">Elige cómo quieres revisar el riesgo.</h1>
            <p className="mt-4 max-w-2xl text-base leading-relaxed text-muted-foreground lg:text-lg">
              RastroSeguro adapta la navegación según la tarea: análisis operativo para preparar casos o vista ejecutiva para entender impacto y prioridades.
            </p>
          </div>
          <div className="institutional-card border-primary/30 bg-[var(--secondary-container)] p-4">
            <p className="flex items-center gap-2 font-display text-base font-semibold text-[var(--on-secondary-container)]">
              <CheckCircle2 className="h-5 w-5" aria-hidden />
              Si no sabes por donde empezar
            </p>
            <p className="mt-2 text-sm leading-relaxed text-[var(--on-secondary-container)]">
              Usa Analista Antifraude para cargar datos y revisar un caso. Usa Vista Ejecutiva para presentar resultados, impacto y prioridades.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
            {['Alerta explicable', 'Revision humana', 'Trazabilidad por caso'].map((item) => (
              <div key={item} className="border border-border bg-[var(--surface-low)] px-4 py-3 label-mono-md uppercase text-muted-foreground">
                {item}
              </div>
            ))}
          </div>
        </header>

        <section className="grid gap-4" aria-label="Seleccionar perfil de usuario">
          {roles.map((role) => {
            const Icon = role.icon
            return (
              <button
                key={role.id}
                type="button"
                onClick={() => selectUserRole(role.id)}
                className="group institutional-card grid gap-5 p-5 text-left transition-colors hover:border-primary hover:bg-[var(--surface-low)] md:grid-cols-[auto_1fr_auto] md:items-center"
              >
                <div className="flex h-14 w-14 items-center justify-center rounded-md bg-[var(--primary-container)] text-white transition-transform group-hover:-translate-y-1">
                  <Icon className="h-7 w-7" aria-hidden />
                </div>
                <div>
                  <p className="label-mono-md font-bold uppercase text-muted-foreground">{role.eyebrow}</p>
                  <h2 className="mt-1 font-display text-2xl font-semibold text-foreground">{role.title}</h2>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{role.description}</p>
                  <ul className="mt-4 grid gap-2 text-sm text-foreground sm:grid-cols-3">
                    {role.bullets.map((bullet) => (
                      <li key={bullet} className="flex gap-2">
                        <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-[var(--tertiary-fixed-dim)]" aria-hidden />
                        <span>{bullet}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <span className="inline-flex items-center justify-center gap-2 bg-primary px-4 py-3 label-mono-md font-bold uppercase text-primary-foreground group-hover:opacity-90">
                  {role.cta}
                  <ArrowRight className="h-4 w-4" aria-hidden />
                </span>
              </button>
            )
          })}
        </section>
      </div>
    </main>
  )
}
