# Migración Next.js + puente API Python

Este documento define cómo consolidamos la interfaz en Next.js sin romper el cerebro de RastroSeguro.

## Estado actual

> **Pendientes actuales para Justin:** ver `docs/equipo/justin-nextjs-hardening.md` antes de seguir agregando pantallas. Ahí está el checklist de estabilidad para la demo Next.js.

El puente API ya está implementado en `api/` con FastAPI y contrato estándar `{ ok, data, error }`.

Para correrlo localmente:

```bash
uv run uvicorn api.main:app --reload --port 8000
```

Healthcheck:

```bash
curl http://localhost:8000/api/health
```

---

## Decisión

- **Justin** construye el frontend en Next.js.
- **Jeremy** construye el puente API en Python.
- El núcleo existente en `src/` se mantiene como fuente de verdad.
- Next.js (`frontend/`) es el único frontend de la demo.

```txt
frontend/ Next.js
        ↓ fetch()
api/ FastAPI
        ↓ llama funciones Python
src/ scoring + reglas + agente + simulador + reportes
        ↓
data/processed/siniestros_scored.csv
```

## Regla principal

Next.js debe consumir contratos limpios desde la API, sin depender de implementaciones legacy.

El objetivo de Justin es construir una demo visual fuerte usando endpoints estables.

---

## Responsabilidades de Justin

Justin trabaja en:

```txt
frontend/
  app/
  components/
  lib/
  styles/
```

Debe construir:

1. Dashboard ejecutivo.
2. Vista de revisión de siniestro.
3. Vista de inteligencia antifraude con agente y simulador.

Justin NO debe reimplementar lógica de scoring, reglas, agente o simulador en TypeScript.

Debe llamar a la API con `fetch()`.

Ejemplo:

```ts
const response = await fetch(`${API_URL}/api/simulator/claim`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(claimData),
});

const payload = await response.json();
```

---

## Responsabilidades de Jeremy

Jeremy trabaja en:

```txt
api/
  __init__.py
  main.py
  schemas.py
  routes/
    __init__.py
    health.py
    claims.py
    agent.py
    simulator.py
    reports.py
```

Debe exponer endpoints HTTP que llamen funciones existentes:

```python
explain_claim(id_siniestro)
simulate_new_claim(claim_data)
answer_question(question)
generate_report_dict()
get_top_risky_claims(limit)
get_provider_risk_ranking(limit)
get_city_risk_distribution()
get_risk_by_branch()
```

Jeremy NO debe construir pantallas, cards, charts ni layout de Next.

---

## Formato estándar de respuesta

Todos los endpoints deben responder de forma consistente.

### Éxito

```json
{
  "ok": true,
  "data": {},
  "error": null
}
```

### Error

```json
{
  "ok": false,
  "data": null,
  "error": {
    "message": "No se encontró data/processed/siniestros_scored.csv",
    "hint": "Ejecuta primero el scoring."
  }
}
```

Esto permite que Justin maneje estados de carga, error y datos sin adivinar estructuras.

---

## Endpoints mínimos

### 1. Healthcheck

```txt
GET /api/health
```

Respuesta:

```json
{
  "ok": true,
  "data": {
    "service": "rastroseguro-api",
    "status": "ok"
  },
  "error": null
}
```

Uso en Next: validar que el backend está levantado.

---

### 2. Casos priorizados

```txt
GET /api/claims?limit=50
```

Llama a:

```python
get_top_risky_claims(limit)
```

Uso en Next:

- tabla de casos;
- tarjetas de riesgo;
- selección de caso estrella.

---

### 3. Explicación de siniestro

```txt
GET /api/claims/{id_siniestro}/explanation
```

Llama a:

```python
explain_claim(id_siniestro)
```

Uso en Next:

- vista de detalle;
- score final;
- componentes;
- alertas;
- explicación;
- acción sugerida.

---

### 4. Ranking de proveedores

```txt
GET /api/rankings/providers?limit=10
```

Llama a:

```python
get_provider_risk_ranking(limit)
```

Uso en Next:

- gráfico o tabla de proveedores con mayor concentración de riesgo.

---

### 5. Riesgo por ciudad

```txt
GET /api/risk/cities
```

Llama a:

```python
get_city_risk_distribution()
```

Uso en Next:

- mapa;
- gráfico por ciudad;
- resumen territorial.

---

### 6. Riesgo por ramo

```txt
GET /api/risk/branches
```

Llama a:

```python
get_risk_by_branch()
```

Uso en Next:

- comparación entre vehículos, salud, hogar, vida y generales.

---

### 7. Simulador de nuevo siniestro

```txt
POST /api/simulator/claim
```

Llama a:

```python
simulate_new_claim(claim_data)
```

Entrada desde Next:

```json
{
  "ramo": "vehiculo",
  "tipo_evento": "choque",
  "monto_reclamado": 8500,
  "suma_asegurada": 12000,
  "proveedor": "PROV-001",
  "narrativa": "Choque al salir del parqueadero sin testigos",
  "documentos_presentes": false
}
```

Salida esperada en `data`:

```json
{
  "ok": true,
  "simulated": true,
  "source": "simulator",
  "risk": {},
  "signals": {},
  "ui": {},
  "context": {}
}
```

Uso en Next:

- formulario de simulación;
- resultado instantáneo;
- badge de riesgo;
- señales explicables;
- pasos recomendados.

---

### 8. Agente antifraude

Preguntas rápidas:

```txt
GET /api/agent/quick-questions
```

Pregunta libre:

```txt
POST /api/agent/ask
```

Llama a:

```python
answer_question(question)
```

Entrada:

```json
{
  "question": "Explícame el siniestro SIN-0045"
}
```

Salida esperada en `data`:

```json
{
  "ok": true,
  "intent": "explicar_siniestro",
  "message": "...",
  "source": "llm",
  "llm": {
    "enabled": true,
    "provider": "openai",
    "model": "gpt-4o",
    "status": "ok"
  },
  "data": {}
}
```

Uso en Next:

- panel conversacional;
- preguntas rápidas;
- trazabilidad de si respondió `llm`, `tools` o `rag`.

---

### 9. Reporte ejecutivo

```txt
GET /api/report
```

Llama a:

```python
generate_report_dict()
```

Uso en Next:

- vista de reporte/demo;
- resumen ejecutivo;
- top casos;
- top proveedores;
- nota ética.

---

## Vistas recomendadas para Justin

Con el tiempo limitado, Justin debería hacer pocas vistas fuertes.

```txt
frontend/app/page.tsx                 Dashboard ejecutivo
frontend/app/claims/[id]/page.tsx     Revisión de siniestro
frontend/app/intelligence/page.tsx    Agente + simulador + reporte
```

También puede hacerlo todo en una sola página con tabs si quiere reducir riesgo.

---

## Estructura sugerida para frontend

```txt
frontend/
  app/
    page.tsx
    claims/[id]/page.tsx
    intelligence/page.tsx
  components/
    layout/
    cards/
    charts/
    claims/
    agent/
    simulator/
  lib/
    api.ts
    types.ts
    formatters.ts
  styles/
```

`frontend/lib/api.ts` debe centralizar llamadas a la API:

```ts
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function getClaims(limit = 50) {
  const res = await fetch(`${API_URL}/api/claims?limit=${limit}`);
  return res.json();
}
```

---

## Ejecución local con uv

Usaremos `uv` para el backend Python.

### Crear entorno e instalar dependencias

```bash
uv venv
uv pip install -r requirements.txt
uv pip install fastapi uvicorn
```

Más adelante podemos pasar dependencias a `pyproject.toml`, pero para avanzar rápido mantenemos `requirements.txt`.

### Correr backend

```bash
uv run uvicorn api.main:app --reload --port 8000
```

### Correr frontend

```bash
cd frontend
npm install
npm run dev
```

URLs locales:

```txt
Backend:  http://localhost:8000
Frontend: http://localhost:3000
```

---

## Variables de entorno

Backend Python:

```env
OPENAI_API_KEY=
RASTRO_LLM_ENABLED=true
RASTRO_LLM_PROVIDER=openai
RASTRO_LLM_MODEL=gpt-4o
```

Frontend Next:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Orden de implementación

### Paso 1, Jeremy

Crear API mínima:

```txt
GET  /api/health
GET  /api/claims
GET  /api/claims/{id_siniestro}/explanation
POST /api/simulator/claim
POST /api/agent/ask
```

Con esto Justin ya puede avanzar.

### Paso 2, Justin

Crear Next.js con mocks o consumiendo la API real.

### Paso 3, Jeremy

Agregar endpoints complementarios:

```txt
GET /api/rankings/providers
GET /api/risk/cities
GET /api/risk/branches
GET /api/report
```

### Paso 4, integración

Probar flujo completo:

```txt
Next formulario simulador → FastAPI → simulate_new_claim → JSON → UI
Next agente → FastAPI → answer_question → JSON → UI
Next detalle → FastAPI → explain_claim → JSON → UI
```

---

## Reglas para no perder tiempo

1. No meter auth ni login.
2. No crear base de datos nueva.
3. No duplicar lógica Python en TypeScript.
4. No crear más de tres vistas principales.
5. No cambiar contratos sin avisar al otro.
6. Si un endpoint falla por falta de CSV, devolver error claro con `hint`.

---

## Mensaje para Justin

Justin, el frontend puede avanzar sin tocar lógica antifraude. La API de Jeremy te va a entregar JSON listo para pintar. Prioriza una interfaz muy buena sobre tres momentos de demo:

1. Dashboard ejecutivo.
2. Revisión explicable de un siniestro rojo.
3. Inteligencia antifraude: agente + simulador.

Si algo falta, usa mocks temporales con la misma forma del JSON de este documento. Luego solo cambias el mock por `fetch()`.
