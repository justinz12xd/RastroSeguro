# Guía técnica — RastroSeguro

Documentación para **desarrolladores, integradores y operación**. Para el enfoque de negocio y el pitch del proyecto, ver el [README principal](../README.md) y [`presentation/RastroSeguro-Pitch.md`](../presentation/RastroSeguro-Pitch.md).

---

## Instalación

### Requisitos

- Python **3.11+**
- Node.js **18+**

### Dependencias

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Opcional: pipelines offline (scrapers, Excel) y tooling de calidad
pip install -e ".[pipelines,dev]"

cd frontend && npm install && cd ..
cp .env.example .env
```

---

## Levantar la plataforma

```bash
# Terminal A — API
uvicorn api.main:app --reload --port 8000

# Terminal B — Dashboard
cd frontend && npm run dev
```

- Frontend: http://localhost:3000
- API health: http://localhost:8000/api/health

Producción (Azure App Service): [`startup.sh`](../startup.sh) con gunicorn + uvicorn worker.

---

## Pipeline de datos (offline)

El repo incluye datos procesados listos para demo. Regenerar solo si cambias el pipeline:

```bash
python -m pipelines.models.run_carlos_pipeline --rows 25000 --seed 42 --scoring-rows 2000
python -m pipelines.models.validate_deliverables
python -m src.scoring.final_score
```

Alternativa paso a paso: [`05-instrucciones-ejecucion.md`](./05-instrucciones-ejecucion.md)

### Dataset sintético

| Archivo | Descripción |
|---------|-------------|
| `data/synthetic/siniestros.csv` | 25 000 siniestros multi-ramo |
| `data/synthetic/polizas.csv` | Pólizas vinculadas |
| `data/synthetic/asegurados.csv` | Asegurados |
| `data/synthetic/proveedores.csv` | Proveedores/talleres |
| `data/synthetic/documentos.csv` | Documentos adjuntos |
| `data/processed/siniestros_scored.csv` | Score final y nivel de riesgo |

Regenerar sintéticos:

```bash
python -m pipelines.data.generate_synthetic_data
python -m src.scoring.final_score
```

### Datos públicos Ecuador

| Fuente | Archivo |
|--------|---------|
| SERCOP | `data/curated/ecuador/sercop_sanciones_curated.csv` |
| OCDS | `data/curated/ecuador/ocds_contratos_curated.csv` |
| Señales proveedor | `data/curated/ecuador/supplier_risk_features.csv` |

Inventario: [`inventario-fuentes-ecuador.md`](./inventario-fuentes-ecuador.md)

---

## Arquitectura

```txt
Datos + documentos → Features → Reglas + ML + Anomalías + NLP + Grafo
    → Score (0–100) → API FastAPI → Dashboard Next.js
                              ↘ Agente multiagente + Reportes
```

| Capa | Ubicación |
|------|-----------|
| Frontend | `frontend/` (Next.js, React, Tailwind) |
| API | `api/` (FastAPI) |
| Aplicación | `src/application/` (casos de uso, queries) |
| Dominio | `src/` (scoring, reglas, NLP, grafo) |
| Infraestructura | `src/infrastructure/` (repos, LLM, chat) |
| Pipelines offline | `pipelines/` (datos, modelos, scraping) |

Detalle:

- [Arquitectura general](./arquitectura.md)
- [Clean architecture backend](./architecture/backend-clean-architecture.md)
- [Contratos de integración](./02-contratos-integracion.md)

### Estructura del repositorio

```txt
RastroSeguro_hackIAthon/
├── api/                  # FastAPI
├── frontend/             # Dashboard Next.js
├── src/
│   ├── application/      # Casos de uso
│   ├── infrastructure/   # Config, repos, LLM, chat
│   ├── agent/            # Router, intents, LangGraph, RAG
│   ├── scoring/          # Pipeline de score
│   ├── rules/            # Reglas RF-01…RF-07
│   ├── nlp/              # Similitud de narrativas
│   ├── graph/            # Redes y anillos
│   └── reports/          # Reportes y ahorro
├── pipelines/            # Tooling offline
├── data/                 # Sintéticos, processed, Ecuador
├── notebooks/            # Notebooks ejecutables
├── presentation/         # Pitch
├── entregables/          # Paquete de entrega
├── docs/                 # Documentación
├── models/               # Artefactos ML (.joblib)
└── tests/                # Tests
```

---

## Agente multiagente

Runtime por defecto: **LangGraph** (supervisor + especialistas).

| Agente | Dominio |
|--------|---------|
| Supervisor | Clasifica y delega |
| Analista de portafolio | Rankings, top riesgo, ciudades, ramos… |
| Investigador de caso | Explicación, expediente, narrativas, grafo |
| Analista de red | Redes/anillos de fraude |
| Especialista en documentación | Metodología y ética (RAG) |
| Sintetizador | Cierra el turno |

Kill-switch: `RASTRO_AGENT_RUNTIME=classic`. Si LangGraph no está disponible, fallback automático a classic.

Implementación: [`src/agent/langgraph_runtime.py`](../src/agent/langgraph_runtime.py)

---

## Variables de entorno

Ver [`.env.example`](../.env.example).

| Variable | Default | Uso |
|----------|---------|-----|
| `OPENAI_API_KEY` | — | Síntesis conversacional (opcional) |
| `RASTRO_LLM_ENABLED` | `false` | Activar capa LLM |
| `RASTRO_LLM_MODEL` | `gpt-4o` | Modelo OpenAI |
| `RASTRO_API_CORS_ORIGINS` | localhost:3000 | CORS para el frontend |
| `RASTRO_AGENT_RUNTIME` | `langgraph` | `langgraph` o `classic` |
| `RASTRO_MAX_SCORING_ROWS` | `5000` | Límite re-scoring en línea |
| `RASTRO_SAVINGS_PREVENTION_RATE` | `0.20` | Simulación de ahorro |

El scoring y el agente **funcionan sin OpenAI**.

---

## Validación y calidad

```bash
python -m pipelines.models.validate_deliverables
python -m pytest -q
lint-imports
```

---

## Despliegue (Azure)

```bash
bash startup.sh
```

Recomendaciones:

- Health check: `/api/health`
- `WEBSITES_CONTAINER_START_TIME_LIMIT` si el arranque es lento
- `RASTRO_API_CORS_ORIGINS` con URL del frontend
- Respetar `RASTRO_MAX_SCORING_ROWS` y límite de subida (5 MB en frontend)

---

## Notebooks

```bash
jupyter notebook notebooks/
```

| Notebook | Contenido |
|----------|-----------|
| `01_exploracion_datos.ipynb` | Exploración del dataset |
| `02_modelo_fraude.ipynb` | Entrenamiento del clasificador |
| `03_evaluacion_modelo.ipynb` | Métricas y casos estrella |

---

## Presentación (PDF)

```bash
pip install fpdf2
python scripts/export_pitch_pdf.py
```

Salida: `presentation/pitch.pdf`

---

## Herramientas adicionales

| Herramienta | Ruta |
|-------------|------|
| Análisis R | `r/` + `renv.lock` |
| Oracle XE (Docker) | `docker/oracle-xe/` |
| Esquema Oracle | `db/oracle/schema.sql` |

---

## Más documentación

| Documento | Contenido |
|-----------|-----------|
| [Uso de IA](./uso_ia.md) | Algoritmos, métricas, limitaciones |
| [Reglas de negocio](./reglas_negocio.md) | RF-01…RF-07 |
| [Modelo de datos](./modelo_datos.md) | Tablas y relaciones |
| [Limitaciones](./limitaciones.md) | Ética y alcance |
| [Reto PDF](./reto-aseguradora-del-sur.md) | Especificación completa |
