# RastroSeguro

### Inteligencia artificial explicable para priorizar siniestros con señales de posible fraude

Proyecto del equipo para el **hackIAthon 2026 — Reto Aseguradora del Sur**.

> **No acusa. No rechaza pagos. No reemplaza al analista.**
> Ordena el trabajo: pone primero los casos que más lo necesitan y explica por qué.

**Índice:** [El problema](#el-problema) · [Qué es](#qué-es-rastroseguro) · [En qué se basa](#en-qué-se-basa) · [Cómo funciona](#cómo-funciona-en-concepto) · [Qué resuelve](#qué-resuelve) · [Valor por actor](#valor-para-cada-actor) · [Demo rápida](#demo-rápida) · [Entregables](#entregables-del-reto) · [Documentación](#documentación) · [Equipo](#equipo)

---

## El problema

Cada día llegan miles de siniestros. La mayoría son legítimos, pero un porcentaje esconde señales de fraude: pólizas que reclaman a los pocos días de emitirse, proveedores que aparecen una y otra vez, documentos incompletos o inconsistentes, relatos sospechosamente parecidos entre casos distintos.

Hoy esas señales se revisan **una por una, a mano**, y el resultado depende de la carga de trabajo, de la experiencia de cada revisor y de la falta de contexto cuando una alerta aislada no muestra si el caso forma parte de un patrón mayor.

El costo no es solo el fraude que se paga: es también el **tiempo perdido** revisando casos limpios y la **inconsistencia** en cómo se decide qué se investiga.

---

## Qué es RastroSeguro

RastroSeguro es una **plataforma de priorización de siniestros**. Recibe un caso, analiza sus señales de riesgo y entrega:

- Un **puntaje de riesgo de 0 a 100**
- Un **semáforo claro**: 🟢 Verde · 🟡 Amarillo · 🔴 Rojo
- Una **explicación en lenguaje claro** de qué disparó la alerta y con qué evidencia
- Una **acción sugerida** para el analista

Todo enmarcado en un principio: **es una priorización para revisión humana, no una acusación de fraude.**

---

## En qué se basa

1. **IA explicable, no veredictos opacos.** Cada puntaje viene con las razones concretas que lo elevaron.
2. **El humano al centro.** El sistema recomienda y ordena; la decisión siempre es de la persona.
3. **Trazabilidad total.** Toda alerta queda registrada con evidencia y regla de origen, lista para auditoría.
4. **Mirada de conjunto.** El riesgo se evalúa en contexto del portafolio: relaciones, patrones y concentraciones.

---

## Cómo funciona (en concepto)

```
Recepción del caso  →  Lectura de señales  →  Puntaje + semáforo  →  Priorización
        ↓                      ↓                      ↓                    ↓
  con verificación      equipo de analistas    explicación clara     el analista
  humana del documento  especializados         y evidencia por dato   decide y actúa
```

1. **Recepción con verificación.** El caso entra por archivo o documento (PDF/texto). Si es documento, el sistema extrae campos y alerta inconsistencias, pero **exige confirmación humana** antes de procesar.
2. **Lectura de señales.** Un coordinador reparte el análisis entre especialistas: reglas de negocio, comportamiento atípico, similitud entre relatos y relaciones entre actores.
3. **Puntaje y semáforo.** Las señales se integran en un puntaje 0–100 y un nivel Verde/Amarillo/Rojo.
4. **Explicación y acción.** El caso llega al analista ya explicado: qué se activó, con qué evidencia y qué se recomienda hacer.

---

## Qué resuelve

RastroSeguro detecta y prioriza patrones difíciles de ver a mano:

- Siniestros cerca del **inicio de la póliza**
- **Proveedores recurrentes** con concentración anómala de alertas
- **Narrativas clonadas** entre casos distintos
- **Montos atípicos** frente a la suma asegurada o al histórico
- **Documentación inconsistente** o incompleta
- **Redes de fraude**: casos conectados por actores compartidos

Y responde preguntas de negocio en lenguaje natural, por ejemplo:
*"¿Qué proveedores concentran el 80% de las alertas rojas?"* o
*"Muéstrame los casos prioritarios y por qué."*

---

## Valor para cada actor

| Actor | Qué gana |
|-------|----------|
| **Analista de siniestros** | Una bandeja priorizada y explicada: empieza por lo importante |
| **Equipo antifraude** | Detección temprana de patrones y redes |
| **Gerencia** | Visión del riesgo del portafolio e impacto de priorizar bien |
| **Auditoría / Cumplimiento** | Trazabilidad completa de cada alerta y decisión |
| **Cliente honesto** | Reclamos legítimos fluyen más rápido |

---

## Demo rápida

Requisitos: Python 3.11+, Node.js 18+.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd frontend && npm install && cd ..

# Terminal A
uvicorn api.main:app --reload --port 8000

# Terminal B
cd frontend && npm run dev
```

Abrir **http://localhost:3000** → **Entrar a la plataforma**.

**Flujo sugerido (~4 min):** Command Center → carga de datos → análisis de caso → agente IA → simulador → reporte de auditoría.

Instrucciones completas: [`docs/05-instrucciones-ejecucion.md`](docs/05-instrucciones-ejecucion.md)

---

## Entregables del reto

| # | Entregable | Ubicación |
|---|------------|-----------|
| 1 | Prototipo funcional | `frontend/` + `api/` + `notebooks/` |
| 2 | Código fuente + README | Este repositorio |
| 3 | Dataset sintético + datos Ecuador | `data/` · [`entregables/03-dataset/`](entregables/03-dataset/) |
| 4 | Presentación ejecutiva (PDF) | [`presentation/pitch.pdf`](presentation/pitch.pdf) |

Paquete de entrega: [`entregables/`](entregables/)

Pitch en Markdown: [`presentation/RastroSeguro-Pitch.md`](presentation/RastroSeguro-Pitch.md)

---

## Documentación

| Para… | Ver |
|-------|-----|
| Entender el proyecto (negocio) | [`presentation/RastroSeguro-Pitch.md`](presentation/RastroSeguro-Pitch.md) |
| Desarrollar / desplegar / operar | [`docs/guia-tecnica.md`](docs/guia-tecnica.md) |
| Índice completo del equipo | [`docs/README.md`](docs/README.md) |
| Especificación del reto | [`docs/reto-aseguradora-del-sur.md`](docs/reto-aseguradora-del-sur.md) |

---

## Equipo

**Carlos** (datos/modelos) · **Jeremy** (scoring/agente) · **Justin** (dashboard/demo)

*hackIAthon 2026 — Reto Aseguradora del Sur*
