'use client'

import Link from 'next/link'
import { ArrowRight, BadgeCheck, ShieldCheck } from 'lucide-react'
import { motion } from 'framer-motion'
import { LiveDemo } from '@/components/landing/live-demo'
import { SolutionPillars } from '@/components/landing/solution-pillars'

const EASE_OUT: [number, number, number, number] = [0.22, 1, 0.36, 1]

const problemQuestions = [
  {
    question: '¿Por dónde empiezo?',
    consequence: 'Llegan muchos reclamos y no siempre queda claro cuál conviene revisar primero.',
  },
  {
    question: '¿Qué miro en este reclamo?',
    consequence: 'Hay que cruzar póliza, historial, montos y documentos. Hacerlo a mano, uno por uno, consume el día.',
  },
  {
    question: '¿Cómo explico por qué revisé este caso?',
    consequence: 'Sin un resumen claro, cuesta contarle al equipo o en una auditoría el criterio que se usó.',
  },
]

const solutionPillars = [
  {
    title: 'Ordena los casos por nivel de riesgo',
    detail: 'Los casos con más señales aparecen primero.',
  },
  {
    title: 'Explica por que un caso genera alerta',
    detail: 'Cada prioridad llega con razones visibles y auditables.',
  },
  {
    title: 'La decisión siempre la toma una persona',
    detail: 'El sistema orienta; la decisión final sigue en manos del equipo.',
  },
]

const closingBenefits = [
  'Los casos de mayor riesgo aparecen primero, con sus razones.',
  'Cada alerta tiene evidencia revisable, no es una caja negra.',
  'El analista mantiene el control y toma la decisión final.',
]

const sectionVariants = {
  hidden: { opacity: 0, y: 32 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.55, ease: EASE_OUT },
  },
}

const staggerVariants = {
  hidden: {},
  show: {
    transition: {
      staggerChildren: 0.12,
      delayChildren: 0.08,
    },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.45, ease: EASE_OUT },
  },
}

export function LandingPageContent() {
  return (
    <main id="top" className="min-h-screen bg-background text-foreground">
      <a
        href="#contenido"
        className="focus-ring absolute left-4 top-4 z-50 -translate-y-20 bg-background px-4 py-2 label-mono-md font-bold uppercase text-foreground transition-transform focus:translate-y-0"
      >
        Ir al Contenido
      </a>

      <header className="sticky top-0 z-40 border-b border-border bg-background/88 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 lg:px-8">
          <Link href="/" className="min-w-0">
            <div className="flex items-center gap-3">
              <span aria-hidden="true" className="landing-grid-chip text-primary">RS</span>
              <div className="min-w-0">
                <p translate="no" className="font-display text-lg font-bold tracking-tight text-primary">
                  RastroSeguro
                </p>
                <p className="label-mono text-muted-foreground">Inteligencia antifraude</p>
              </div>
            </div>
          </Link>

          <Link
            href="/platform"
            className="focus-ring inline-flex shrink-0 items-center gap-2 bg-primary px-4 py-2.5 label-mono-md font-bold uppercase text-primary-foreground transition-opacity hover:opacity-95"
          >
            Abrir Plataforma <ArrowRight aria-hidden="true" className="h-4 w-4" />
          </Link>
        </div>
      </header>

      <div id="contenido">
        <section className="dark-panel landing-hero-shell landing-section-shell relative overflow-hidden border-b border-border">
          <div aria-hidden="true" className="landing-mesh absolute inset-0" />
          <div aria-hidden="true" className="landing-noise absolute inset-0 opacity-[0.14]" />
          <div aria-hidden="true" className="landing-orb landing-orb-primary" />
          <div aria-hidden="true" className="landing-orb landing-orb-secondary" />

          <div className="relative mx-auto grid min-h-[92vh] max-w-7xl items-center gap-10 px-4 py-12 lg:grid-cols-[1.05fr_.95fr] lg:px-8 lg:py-16">
            <motion.div
              className="landing-reveal landing-copy-stack space-y-8"
              initial="hidden"
              animate="show"
              variants={sectionVariants}
            >
              <div className="max-w-3xl">
                <motion.h1
                  className="landing-hero-title mt-4 select-none text-balance text-4xl lg:text-6xl xl:text-[4.75rem]"
                >
                  ¿Cuáles reclamos hay que revisar primero? RastroSeguro lo dice y explica por qué.
                </motion.h1>
                <p className="dark-panel-muted mt-5 max-w-xl text-lg leading-8 lg:text-xl">
                  Carga tu cartera de siniestros y en segundos tienes una bandeja ordenada por nivel de riesgo, con las razones detrás de cada alerta y una recomendación de revisión clara para el analista.
                </p>
              </div>
            </motion.div>

            <motion.div
              className="landing-reveal landing-demo-wrap lg:pl-4"
              initial={{ opacity: 0, x: 42, rotateY: -10 }}
              animate={{ opacity: 1, x: 0, rotateY: 0 }}
              transition={{ duration: 0.8, ease: EASE_OUT, delay: 0.15 }}
            >
              <LiveDemo />
            </motion.div>
          </div>
        </section>

        <motion.section
          id="problema"
          className="landing-band-ivory landing-section-shell scroll-mt-24 border-b border-border"
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, amount: 0.28, margin: '0px 0px -12% 0px' }}
          variants={sectionVariants}
        >
          <motion.div
            className="mx-auto max-w-7xl px-4 py-20 lg:px-8 lg:py-28"
            variants={staggerVariants}
          >
            <motion.div className="grid gap-5 lg:grid-cols-3 lg:gap-6" variants={staggerVariants}>
              {problemQuestions.map(({ question, consequence }, index) => (
                <motion.article
                  key={question}
                  variants={itemVariants}
                  className="landing-problem-card-light"
                >
                  <span className="landing-problem-index-light label-mono-md">0{index + 1}</span>
                  <h3 className="font-display text-lg font-semibold leading-snug text-balance text-[var(--editorial-ink)] lg:text-xl">
                    {question}
                  </h3>
                  <p className="text-sm leading-7 text-muted-foreground">{consequence}</p>
                </motion.article>
              ))}
            </motion.div>
          </motion.div>
        </motion.section>

        <motion.section
          className="landing-band-solution landing-section-shell border-b border-border"
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, amount: 0.35, margin: '0px 0px -18% 0px' }}
          variants={sectionVariants}
        >
          <div className="mx-auto max-w-7xl px-4 py-20 lg:px-8 lg:py-28">
            <div className="grid gap-10 lg:grid-cols-[.92fr_1.08fr] lg:items-start">
              <motion.div className="max-w-2xl" variants={itemVariants}>
                <p className="label-mono-md uppercase text-[var(--editorial-soft-kicker)]">La solución</p>
                <h2 className="landing-section-display-on-dark display-heading mt-4 text-balance text-4xl lg:text-6xl">
                  Un sistema que prioriza antes, explica mejor y escala con la operación.
                </h2>
                <p className="mt-5 max-w-xl text-base leading-7 text-[var(--editorial-soft-copy)] lg:text-lg">
                  No es solo un panel. Es una forma más inteligente de decidir qué revisar, por qué y con qué evidencia.
                </p>
                <motion.div
                  className="mt-6 flex flex-wrap gap-3"
                  variants={staggerVariants}
                >
                  {['Priorización visible', 'Razones explicables', 'Decisión humana'].map((chip) => (
                    <motion.span key={chip} variants={itemVariants} className="landing-solution-chip">
                      {chip}
                    </motion.span>
                  ))}
                </motion.div>
              </motion.div>

              <motion.div
                className="landing-solution-frame"
                variants={itemVariants}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.32, margin: '0px 0px -16% 0px' }}
                transition={{ duration: 0.5, ease: EASE_OUT, delay: 0.06 }}
              >
                <SolutionPillars pillars={solutionPillars} />
              </motion.div>
            </div>
          </div>
        </motion.section>

        <motion.section
          className="landing-band-closing landing-section-shell flex min-h-[78vh] items-center px-4 py-24 lg:min-h-[88vh] lg:px-8 lg:py-32"
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, amount: 0.24, margin: '0px 0px -10% 0px' }}
          variants={sectionVariants}
        >
          <motion.article className="landing-closing-panel mx-auto max-w-7xl overflow-hidden" variants={itemVariants}>
            <div className="section-header">¿Lista para ver cómo funciona?</div>
            <div className="grid gap-8 p-6 lg:grid-cols-[1.2fr_.8fr] lg:p-8">
              <div>
                <h2 className="display-heading max-w-3xl text-balance text-3xl lg:text-4xl">
                  La inteligencia alerta y explica. La decisión es tuya.
                </h2>
                <p className="landing-closing-copy mt-4 max-w-3xl text-sm leading-7">
                  RastroSeguro no reemplaza al analista: le da una ventaja operativa. Sabe qué revisar primero, por qué importa y cómo sustentarlo ante riesgos, auditoría y gerencia.
                </p>
                <motion.div className="mt-6 space-y-3" variants={staggerVariants}>
                  {closingBenefits.map((item) => (
                    <motion.div key={item} variants={itemVariants} className="landing-closing-proof landing-proof-card">
                      <BadgeCheck aria-hidden className="mt-0.5 h-4 w-4 shrink-0 text-[var(--tertiary-fixed-dim)]" />
                      <p className="text-sm leading-6 text-foreground">{item}</p>
                    </motion.div>
                  ))}
                </motion.div>
              </div>

              <motion.div className="flex flex-col gap-4" variants={staggerVariants}>
                <motion.div variants={itemVariants} className="landing-ethics-card p-6">
                  <div className="flex items-start gap-3">
                    <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-[var(--tertiary-fixed-dim)]" aria-hidden />
                    <div>
                      <p className="font-display font-semibold">Criterio ético integrado</p>
                      <p className="mt-2 text-sm leading-7 text-muted-foreground">
                        Cada pantalla deja claro que <span translate="no">RastroSeguro</span> genera alertas de revisión. No acusa fraude, no rechaza reclamos y no sustituye al analista.
                      </p>
                    </div>
                  </div>
                </motion.div>

                <motion.div variants={itemVariants} className="flex flex-col gap-3">
                  <Link
                    href="/platform"
                    className="landing-closing-cta focus-ring inline-flex items-center justify-center gap-2 px-4 py-3 label-mono-md font-bold uppercase transition-opacity hover:opacity-95"
                  >
                    Abrir Plataforma <ArrowRight aria-hidden className="h-4 w-4" />
                  </Link>
                  <a
                    href="#top"
                    className="landing-closing-secondary focus-ring inline-flex items-center justify-center gap-2 px-4 py-3 label-mono-md font-bold uppercase transition-colors"
                  >
                    Volver arriba
                  </a>
                </motion.div>
              </motion.div>
            </div>
          </motion.article>
        </motion.section>
      </div>
    </main>
  )
}
