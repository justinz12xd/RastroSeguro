# Arquitectura — RastroSeguro

Plataforma híbrida de detección de **posible fraude** en siniestros de seguros. Genera alertas explicables para revisión humana; no acusa ni rechaza reclamos automáticamente.

## Diagrama de flujo

```txt
Dataset sintético (CSV)
        │
        ▼
Validación de esquema ──► Feature engineering
        │
        ▼
Reglas auditables (RF/RB/RV) ──► Modelo supervisado
        │                              │
        ▼                              ▼
Detector de anomalías ◄──── NLP (similitud textual)
        │
        ▼
Análisis de grafo (relaciones)
        │
        ▼
Score final compuesto (0–100) + semáforo Verde/Amarillo/Rojo
        │
        ▼
Explicación por siniestro
        │
        ├── FastAPI (api/main.py) ──► Next.js frontend
        ├── Agente antifraude (src/agent/)
        └── Reportes ejecutivos / auditoría
```

## Módulos del repositorio

| Módulo | Ruta | Responsabilidad |
|--------|------|-----------------|
| Datos | `src/data/` | Generación sintética, señales PDF, exportación |
| Features | `src/data/feature_engineering.py` | Variables para ML y scoring |
| Modelos | `src/models/` | Clasificador supervisado, detector de anomalías |
| Reglas | `src/rules/` | RF-01…RF-07, RB, RV por ramo |
| NLP | `src/nlp/` | Similitud TF-IDF de narrativas |
| Grafo | `src/graph/` | Relaciones asegurado–proveedor–caso |
| Scoring | `src/scoring/` | Score final ponderado y calibración |
| Explicabilidad | `src/explainability/` | Explicación por siniestro |
| Agente | `src/agent/` | Herramientas determinísticas + LLM opcional |
| Reportes | `src/reports/` | Resumen ejecutivo, ahorro estimado, auditoría |
| API | `api/` | Puente REST para Next.js |
| UI | `frontend/` | Dashboard Next.js |
| Base de datos | `db/supabase/`, `db/oracle/` | Esquemas Postgres y Oracle de referencia |
| Análisis R | `r/` | Validación reproducible de métricas |

## Interfaces de despliegue

### API FastAPI + Next.js

```bash
uvicorn api.main:app --reload --port 8000
cd frontend && npm run dev
```

Variable: `NEXT_PUBLIC_API_URL=http://localhost:8000`

### Oracle XE (referencia enterprise)

Ver [`docker/oracle-xe/README.md`](../docker/oracle-xe/README.md).

## Principios de diseño

1. **Trazabilidad**: cada score incluye `rule_trace`, componentes y explicación textual.
2. **Modularidad**: reglas, ML, NLP y grafo son independientes y combinables.
3. **Ética**: lenguaje de “posible fraude” / “requiere revisión”; sin decisiones automáticas.
4. **Escalabilidad**: CSV en prototipo; esquemas SQL listos para Postgres/Oracle en producción.

## Referencias

- Pipeline detallado: [`03-arquitectura-pipeline.md`](./03-arquitectura-pipeline.md)
- Modelo de datos: [`modelo_datos.md`](./modelo_datos.md)
- Uso de IA: [`uso_ia.md`](./uso_ia.md)
