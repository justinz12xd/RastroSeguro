# Landing Editorial Ejecutiva Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rediseñar desde la sección de magnitud hacia abajo en la landing para que se sienta ejecutiva premium, con más color, contraste y ritmo visual, manteniendo coherencia con el hero actual.

**Architecture:** La implementación se concentra en dos capas: estructura semántica y composición visual en `frontend/app/landing/page.tsx`, y sistema de bandas, superficies y acentos en `frontend/app/globals.css`. Los componentes reutilizados de la landing se mantienen, ajustando solo clases y contenedores para que hereden el nuevo lenguaje editorial.

**Tech Stack:** Next.js App Router, React, Tailwind utility classes, CSS global con custom properties

---

## File Map

- Modify: `frontend/app/landing/page.tsx`
  - Reorganizar clases y wrappers de las secciones `Magnitud`, `Problema`, `Solución` y `Cierre`
  - Añadir contenedores editoriales, acentos visuales y una mejor jerarquía de composición
- Modify: `frontend/app/globals.css`
  - Crear clases para bandas editoriales, superficies premium, fondos tintados, cifras protagonistas y cierre ejecutivo
  - Ajustar responsive para mantener el look en móvil
- Verify: `frontend/components/landing/solution-pillars.tsx`
  - Confirmar que las clases nuevas no rompan la animación ni la lectura
- Verify: `frontend/components/landing/live-demo.tsx`
  - Confirmar que el nuevo contenedor visual no afecte la demo ya corregida

### Task 1: Reestructurar la sección de Magnitud

**Files:**
- Modify: `frontend/app/landing/page.tsx`
- Modify: `frontend/app/globals.css`
- Test: `frontend/app/landing/page.tsx`

- [ ] **Step 1: Actualizar el markup de la sección Magnitud**

```tsx
<section className="landing-band-ivory border-b border-border">
  <div className="mx-auto max-w-7xl px-4 py-16 lg:px-8 lg:py-20">
    <div className="landing-editorial-lead">
      <p className="label-mono-md uppercase text-[var(--editorial-kicker)]">La magnitud del problema</p>
    </div>

    <div className="mt-8 grid items-start gap-8 lg:grid-cols-[1.05fr_.95fr] lg:gap-14">
      <div className="landing-stat-stage">
        <div className="landing-stat-ribbon" aria-hidden="true" />
        <p className="landing-stat-hero text-[var(--editorial-ink)]">
          ~10<span className="align-top text-[0.45em] font-semibold">%</span>
        </p>
        <p className="landing-stat-copy">
          de cada dólar pagado en siniestros se estima ligado a fraude.
        </p>
        <p className="landing-stat-support">
          Es la cifra que el sector asegurador maneja a nivel global y en América Latina.
        </p>
      </div>

      <dl className="landing-fact-stack">
        {magnitudeFacts.map(({ label, detail }) => (
          <div key={label} className="landing-fact-row">
            <dt className="label-mono uppercase text-[var(--editorial-ink)]">{label}</dt>
            <dd className="mt-2 text-sm leading-7 text-muted-foreground">{detail}</dd>
          </div>
        ))}
      </dl>
    </div>
  </div>
</section>
```

- [ ] **Step 2: Añadir estilos editoriales para Magnitud**

```css
.landing-band-ivory {
  background:
    radial-gradient(circle at top left, color-mix(in oklch, var(--primary) 10%, transparent), transparent 30%),
    linear-gradient(180deg, var(--editorial-ivory), color-mix(in oklch, var(--editorial-ivory) 88%, white));
}

.landing-stat-stage {
  position: relative;
  overflow: hidden;
  border: 1px solid color-mix(in oklch, var(--editorial-ink) 10%, var(--border));
  border-radius: 1.5rem;
  padding: 1.5rem;
  background: color-mix(in oklch, white 82%, var(--editorial-ivory));
}

.landing-stat-ribbon {
  position: absolute;
  inset: 0 auto 0 0;
  width: 0.75rem;
  background: linear-gradient(180deg, var(--editorial-ink), color-mix(in oklch, var(--primary) 55%, var(--editorial-ink)));
}

.landing-stat-copy {
  margin-top: 1.25rem;
  max-width: 32rem;
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: clamp(1.6rem, 2.5vw, 2.4rem);
  font-weight: 600;
  line-height: 1.05;
  color: var(--editorial-ink);
}

.landing-fact-stack {
  border-top: 1px solid color-mix(in oklch, var(--editorial-ink) 12%, var(--border));
}

.landing-fact-row {
  border-bottom: 1px solid color-mix(in oklch, var(--editorial-ink) 12%, var(--border));
  padding: 1.2rem 0;
}
```

- [ ] **Step 3: Verificar visualmente la sección en móvil y desktop**

Run: `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -Command npm run build`
Expected: build exit code `0` y la sección mantiene contraste sin depender de hover

- [ ] **Step 4: Commit**

```bash
git add frontend/app/landing/page.tsx frontend/app/globals.css
git commit -m "feat: redesign landing magnitude section"
```

### Task 2: Rediseñar la sección Problema con más tensión visual

**Files:**
- Modify: `frontend/app/landing/page.tsx`
- Modify: `frontend/app/globals.css`
- Test: `frontend/app/landing/page.tsx`

- [ ] **Step 1: Reemplazar las cards blancas por una banda editorial entintada**

```tsx
<section id="problema" className="landing-band-ink scroll-mt-24 border-b border-border">
  <div className="mx-auto max-w-7xl px-4 py-16 lg:px-8">
    <div className="max-w-3xl">
      <p className="label-mono-md uppercase text-[var(--editorial-soft-kicker)]">La fricción diaria</p>
      <h2 className="display-heading max-w-3xl text-balance text-3xl text-white lg:text-4xl">
        Saber que el fraude existe es fácil. Cada mañana, la pregunta es otra:
      </h2>
      <p className="mt-4 max-w-2xl text-sm leading-7 text-[var(--editorial-soft-copy)]">
        Tres preguntas que un analista enfrenta con cada cartera, sin una guía clara.
      </p>
    </div>

    <div className="mt-10 grid gap-4 lg:grid-cols-3">
      {problemQuestions.map(({ question, consequence }, index) => (
        <article key={question} className="landing-problem-card">
          <span className="landing-problem-index label-mono-md">0{index + 1}</span>
          <h3 className="font-display text-lg font-semibold leading-snug text-balance text-white">
            {question}
          </h3>
          <p className="text-sm leading-6 text-[var(--editorial-soft-copy)]">{consequence}</p>
        </article>
      ))}
    </div>
  </div>
</section>
```

- [ ] **Step 2: Añadir clases de fondo y módulos para Problema**

```css
.landing-band-ink {
  background:
    radial-gradient(circle at 15% 15%, color-mix(in oklch, var(--tertiary-fixed-dim) 16%, transparent), transparent 20%),
    linear-gradient(180deg, var(--editorial-ink), color-mix(in oklch, var(--editorial-ink) 88%, black));
}

.landing-problem-card {
  display: flex;
  min-height: 15rem;
  flex-direction: column;
  gap: 1rem;
  border: 1px solid color-mix(in oklch, white 10%, transparent);
  border-radius: 1.25rem;
  padding: 1.5rem;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.03));
  box-shadow: 0 18px 40px rgba(2, 6, 23, 0.18);
}

.landing-problem-index {
  color: color-mix(in oklch, var(--primary-fixed) 80%, white);
}
```

- [ ] **Step 3: Ejecutar build para validar clases y JSX**

Run: `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -Command npm run build`
Expected: build exit code `0` y `Route (app)` incluye `/landing`

- [ ] **Step 4: Commit**

```bash
git add frontend/app/landing/page.tsx frontend/app/globals.css
git commit -m "feat: redesign landing problem section"
```

### Task 3: Convertir Solución en una banda premium de alivio

**Files:**
- Modify: `frontend/app/landing/page.tsx`
- Modify: `frontend/app/globals.css`
- Verify: `frontend/components/landing/solution-pillars.tsx`
- Verify: `frontend/components/landing/live-demo.tsx`

- [ ] **Step 1: Reestructurar la sección Solución para alojar mejor el flujo**

```tsx
<section className="landing-band-solution border-b border-border">
  <div className="mx-auto max-w-7xl px-4 py-16 lg:px-8">
    <div className="grid gap-10 lg:grid-cols-[.92fr_1.08fr] lg:items-start">
      <div className="max-w-2xl">
        <p className="label-mono-md uppercase text-[var(--editorial-soft-kicker)]">La solución</p>
        <h2 className="display-heading mt-4 text-balance text-3xl text-white lg:text-4xl">
          Convierte esa cartera en una bandeja ordenada por riesgo.
        </h2>
        <p className="mt-4 text-sm leading-7 text-[var(--editorial-soft-copy)]">
          RastroSeguro toma los miles de reclamos, detecta señales de alerta y los ordena para que el analista empiece por donde más importa.
        </p>
      </div>

      <div className="landing-solution-frame">
        <SolutionPillars pillars={solutionPillars} />
      </div>
    </div>
  </div>
</section>
```

- [ ] **Step 2: Añadir superficie premium y contraste para Solución**

```css
.landing-band-solution {
  background:
    radial-gradient(circle at 80% 10%, color-mix(in oklch, var(--primary) 16%, transparent), transparent 24%),
    linear-gradient(180deg, color-mix(in oklch, var(--editorial-ink) 96%, black), color-mix(in oklch, var(--editorial-ink) 88%, var(--primary)));
}

.landing-solution-frame {
  border: 1px solid color-mix(in oklch, white 12%, transparent);
  border-radius: 1.5rem;
  padding: 1.25rem;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.11), rgba(255, 255, 255, 0.05)),
    color-mix(in oklch, var(--editorial-ink) 88%, white 12%);
  box-shadow: 0 22px 48px rgba(2, 6, 23, 0.24);
}
```

- [ ] **Step 3: Confirmar que `SolutionPillars` siga legible y animado**

Run: `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -Command npm run build`
Expected: build exit code `0` y sin errores de TypeScript en `solution-pillars.tsx`

- [ ] **Step 4: Commit**

```bash
git add frontend/app/landing/page.tsx frontend/app/globals.css frontend/components/landing/solution-pillars.tsx frontend/components/landing/live-demo.tsx
git commit -m "feat: redesign landing solution section"
```

### Task 4: Replantear el cierre como bloque de decisión ejecutiva

**Files:**
- Modify: `frontend/app/landing/page.tsx`
- Modify: `frontend/app/globals.css`
- Test: `frontend/app/landing/page.tsx`

- [ ] **Step 1: Cambiar el cierre a una composición de decisión**

```tsx
<section className="landing-band-closing mx-auto max-w-7xl px-4 py-16 lg:px-8">
  <article className="landing-closing-panel overflow-hidden">
    <div className="section-header">Lista para ver cómo funciona</div>
    <div className="grid gap-8 p-6 lg:grid-cols-[1.2fr_.8fr] lg:p-8">
      <div>
        <h2 className="display-heading text-balance text-3xl lg:text-4xl">
          La inteligencia alerta y explica. La decisión es tuya.
        </h2>
        <p className="mt-4 max-w-3xl text-sm leading-7 text-[var(--editorial-closing-copy)]">
          RastroSeguro no reemplaza al analista: le da una ventaja operativa para priorizar, justificar y sostener decisiones.
        </p>
        <div className="mt-6 space-y-3">
          {items.map((item) => (
            <div key={item} className="landing-closing-proof">
              <BadgeCheck aria-hidden className="mt-0.5 h-4 w-4 shrink-0 text-[var(--tertiary-fixed-dim)]" />
              <p className="text-sm leading-6">{item}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-4">
        <div className="landing-ethics-card p-6">
          ...
        </div>
        <div className="flex flex-col gap-3">
          ...
        </div>
      </div>
    </div>
  </article>
</section>
```

- [ ] **Step 2: Crear estilos del panel final**

```css
.landing-band-closing {
  background: linear-gradient(180deg, var(--editorial-ivory), color-mix(in oklch, var(--editorial-ivory) 76%, white));
}

.landing-closing-panel {
  border: 1px solid color-mix(in oklch, var(--editorial-ink) 12%, var(--border));
  border-radius: 1.75rem;
  background:
    radial-gradient(circle at top right, color-mix(in oklch, var(--primary) 12%, transparent), transparent 24%),
    linear-gradient(180deg, white, color-mix(in oklch, var(--editorial-ivory) 84%, white));
  box-shadow: 0 24px 50px rgba(15, 23, 42, 0.08);
}

.landing-closing-proof {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  border: 1px solid color-mix(in oklch, var(--editorial-ink) 8%, var(--border));
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.72);
  padding: 0.9rem 1rem;
}
```

- [ ] **Step 3: Validar el cierre con build**

Run: `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -Command npm run build`
Expected: build exit code `0` y el cierre conserva CTA principal y nota ética

- [ ] **Step 4: Commit**

```bash
git add frontend/app/landing/page.tsx frontend/app/globals.css
git commit -m "feat: redesign landing closing section"
```

### Task 5: Ajuste responsive y verificación final

**Files:**
- Modify: `frontend/app/globals.css`
- Test: `frontend/app/landing/page.tsx`

- [ ] **Step 1: Añadir responsive para que las bandas mantengan intención en móvil**

```css
@media (max-width: 767px) {
  .landing-stat-stage,
  .landing-solution-frame,
  .landing-closing-panel {
    border-radius: 1.25rem;
  }

  .landing-problem-card {
    min-height: auto;
  }

  .landing-stat-copy {
    font-size: 1.75rem;
  }
}
```

- [ ] **Step 2: Ejecutar build final**

Run: `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -Command npm run build`
Expected: build exit code `0`

- [ ] **Step 3: Revisar cobertura contra el spec**

Expected:
- `Magnitud` usa banda editorial y protagonista numérico
- `Problema` ya no usa tarjetas blancas planas
- `Solución` contrasta claramente con `Problema`
- `Cierre` se siente bloque ejecutivo y no caja genérica
- móvil conserva legibilidad y ritmo visual

- [ ] **Step 4: Commit**

```bash
git add frontend/app/globals.css frontend/app/landing/page.tsx
git commit -m "chore: finalize editorial landing polish"
```
