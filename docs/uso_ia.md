# Uso de Inteligencia Artificial — RastroSeguro

Enfoque **híbrido** recomendado por el reto Aseguradora del Sur: reglas de negocio + ML + anomalías + NLP + grafo + agente explicativo.

## Componentes de IA

| Componente | Algoritmo | Archivo | Peso en score |
|------------|-----------|---------|---------------|
| Reglas | Motor determinístico RF/RB/RV | `src/rules/` | 30% |
| Clasificador | RandomForest (supervisado) | `src/models/train_classifier.py` | 25% |
| Anomalías | IsolationForest | `src/models/train_anomaly.py` | 15% |
| NLP | TF-IDF + coseno (similitud narrativa) | `src/nlp/similarity_engine.py` | 15% |
| Grafo | Métricas de recurrencia entre entidades | `src/graph/scoring.py` | 10% |
| Categórico | Perfiles por ramo/cobertura | `src/categorical/scoring.py` | 5% |

Pesos definidos en [`src/scoring/final_score.py`](../src/scoring/final_score.py).

## Variables de entrada

Generadas en [`src/data/feature_engineering.py`](../src/data/feature_engineering.py):

- Temporales: `dias_desde_inicio_poliza`, `dias_desde_fin_poliza`, `dias_entre_ocurrencia_reporte`
- Montos: `monto_reclamado`, `suma_asegurada`, ratios
- Historial: `historial_siniestros_asegurado`, `historial_siniestros_vehiculo`
- Documentos: `documentos_completos`, `documentos_inconsistentes`
- Vehículos: `placa_hash`, `chasis_hash`, `motor_hash`, `marca`, `modelo`, `anio`
- Ecuador: `lista_restrictiva_sercop`, `supplier_ruc`, contexto geográfico
- Etiqueta simulada: `etiqueta_fraude_simulada` (solo entrenamiento/evaluación)

## NLP — narrativas similares (PDF §7)

- Umbral de detección: **≥70%** similitud textual
- Puntuación PDF:
  - **≥85%** → 8 pts (alta)
  - **70–84%** → 4 pts (media)
- Implementación: [`src/nlp/narrative_signals.py`](../src/nlp/narrative_signals.py)

## Semáforo de riesgo

| Rango | Nivel | Acción |
|-------|-------|--------|
| 0–40 | Verde | Flujo normal |
| 41–75 | Amarillo | Revisión documental |
| 76–100 | Rojo | Revisión antifraude especializada |

Implementación: [`src/utils/risk_levels.py`](../src/utils/risk_levels.py)

## Métricas del modelo (datos sintéticos)

Archivo: [`reports/model_metrics.json`](../reports/model_metrics.json)

| Métrica | Clasificador | Anomalías |
|---------|--------------|-----------|
| F1 | ~0.99 | — |
| AUC-ROC | ~1.0 | — |
| Tasa anomalías | — | ~26% |
| Overlap fraude simulado | — | ~58% |

> Métricas altas reflejan señales inyectadas en datos sintéticos. No garantizan performance en producción.

## Agente de IA

- **Determinístico por defecto**: 12 preguntas del PDF + herramientas en `src/agent/tools.py`
- **LLM opcional**: OpenAI vía `RASTRO_LLM_ENABLED=true` en `.env`
- El LLM **no calcula scores**; sintetiza respuestas sobre datos ya puntuados

## Simulación de ahorro potencial

Estimación: `monto_expuesto_casos_rojos × tasa_prevencion` (configurable, default 20%).

Variable: `RASTRO_SAVINGS_PREVENTION_RATE=0.20`

Módulo: [`src/reports/savings_simulation.py`](../src/reports/savings_simulation.py)

## Bases de datos

| Motor | Uso | Ruta |
|-------|-----|------|
| CSV | Runtime del prototipo | `data/synthetic/`, `data/processed/` |
| Postgres/Supabase | Analítica y despliegue cloud | `db/supabase/` |
| Oracle XE | Referencia enterprise | `db/oracle/`, `docker/oracle-xe/` |

## Limitaciones y ética

- Datos 100% sintéticos; no PII real
- Resultado = **alerta de revisión**, no acusación legal
- Revisión humana obligatoria antes de cualquier decisión de pago
- Posibles falsos positivos documentados en [`limitaciones.md`](./limitaciones.md)

## Reproducibilidad

```bash
py -3 -m pipelines.models.run_carlos_pipeline --rows 25000 --seed 42 --scoring-rows 2000
py -3 -m pipelines.models.validate_deliverables
```

Validación R: [`r/01_validacion_metricas.R`](../r/01_validacion_metricas.R)
