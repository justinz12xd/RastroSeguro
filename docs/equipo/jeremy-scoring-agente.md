# Jeremy — Scoring, reglas, explicación, agente y simulador

Jeremy construye el núcleo lógico de RastroSeguro. Convierte datos y modelos en riesgo explicable para la app.

## Objetivo

Entregar un pipeline que tome el dataset de Carlos y genere scores, niveles de riesgo, alertas, explicaciones y herramientas para el agente.

## Responsabilidades

Consulta también el plan de migración Next.js + puente API: [justin-nextjs-puente-api.md](./justin-nextjs-puente-api.md).

- Motor de reglas base y por ramo.
- Score final compuesto.
- Explicación por siniestro.
- Integración de modelos de Carlos.
- Herramientas del agente.
- Router de intención básico.
- RAG documental liviano.
- Simulador de nuevo siniestro.

## Módulos

```txt
src/rules/base_rules.py
src/rules/vehicle_rules.py
src/rules/health_rules.py
src/rules/home_rules.py
src/rules/life_rules.py
src/rules/general_rules.py
src/rules/rule_registry.py
src/scoring/final_score.py
src/explainability/explain_claim.py
src/agent/tools.py
src/agent/router.py
src/agent/rag.py
src/agent/llm/base.py
src/agent/llm/disabled_provider.py
src/agent/llm/openai_provider.py
src/agent/llm/prompts.py
src/agent/llm/settings.py
src/agent/antifraud_agent.py
```

## Entrada

```txt
data/synthetic/siniestros.csv
models/fraud_classifier.joblib
models/anomaly_detector.joblib
```

## Salida

```txt
data/processed/siniestros_scored.csv
```

Columnas clave:

```txt
score_reglas, score_modelo, score_anomalia, score_nlp, score_grafo,
score_categorico, score_final, nivel_riesgo, alertas_activadas,
explicacion, accion_sugerida
```

## Score final

```txt
score_final =
  30% score_reglas
+ 25% score_modelo
+ 15% score_anomalia
+ 15% score_nlp
+ 10% score_grafo
+ 5% score_categorico
```

Si un componente aún no existe, usar valor neutro o documentado para no romper el pipeline.

## Guardrail por reglas críticas

Para que reglas críticas no se diluyan cuando los componentes de Carlos o módulos avanzados aún estén neutrales:

```txt
score_reglas >= 90 → score_final mínimo 80
score_reglas >= 75 → score_final mínimo 76
```

Nota de calibración: con las reglas críticas RF integradas, `score_reglas` se normaliza sobre 100 puntos acumulados para evitar que señales duplicadas o frecuentes conviertan casi todo el portafolio en Rojo.

## Semáforo

| Score | Nivel | Acción |
|---:|---|---|
| 0–40 | Verde | Continuar flujo normal |
| 41–75 | Amarillo | Revisión documental |
| 76–100 | Rojo | Revisión especializada |

## Funciones que Justin necesita

```python
explain_claim(id_siniestro)
simulate_new_claim(claim_data)
get_top_risky_claims(limit=10)
get_provider_risk_ranking()
get_city_risk_distribution()
generate_executive_summary()
```

## Regla para el agente

El agente no inventa. Para datos tabulares llama herramientas; para reglas, metodología y limitaciones puede usar RAG documental.

La redacción con OpenAI es opcional: solo sintetiza respuestas desde salidas verificadas del pipeline. Si no está configurado, el agente sigue funcionando de forma determinística.

## Prioridad

1. Reglas + score + CSV procesado.
2. Explicación por siniestro.
3. Integración de modelos.
4. Herramientas del agente.
5. Simulador.
6. RAG documental.


## Reglas multi-ramo implementadas

El motor ya contempla paquetes iniciales para:

| Ramo | Archivo | Señales principales |
|---|---|---|
| Vehículos | `src/rules/vehicle_rules.py` | robo temprano, vehículo recurrente, noche sin testigos, reporte policial, tercero no identificado |
| Salud | `src/rules/health_rules.py` | monto médico atípico, frecuencia de atenciones, proveedor médico recurrente, fechas de factura |
| Hogar | `src/rules/home_rules.py` | falta de inspección, proveedor recurrente, daños repetidos, falta de evidencia |
| Vida | `src/rules/life_rules.py` | beneficiario recurrente, cambios recientes, notificación tardía, soporte faltante |
| Generales | `src/rules/general_rules.py` | monto atípico, intermediario recurrente, inconsistencia de cobertura |

Todas las reglas devuelven código, puntos, severidad, mensaje y evidencia para trazabilidad.


## NLP de narrativas

El módulo NLP está separado del scoring para mantener el código pequeño y extensible:

```txt
src/nlp/text_normalization.py
src/nlp/similarity_engine.py
src/nlp/narrative_signals.py
src/nlp/scoring.py
```

La primera versión usa TF-IDF cuando `scikit-learn` está disponible y fallback por tokens cuando no. Esto permite avanzar sin romper el pipeline y deja lista la estructura para reemplazar o ampliar con embeddings después.


## Grafo de relaciones

El módulo de relaciones está separado para mantener la arquitectura limpia:

```txt
src/graph/entity_extraction.py
src/graph/relationship_metrics.py
src/graph/scoring.py
```

Este módulo calcula recurrencia de entidades críticas y genera `score_grafo`, `entidades_recurrentes`, `conexiones_grafo` y `explicacion_grafo`. Además, deriva `proveedor_recurrente` y `beneficiario_recurrente` para que las reglas base puedan explicar esas señales.


## Scoring categórico

El módulo categórico está separado para que las variables cualitativas tengan una explicación propia:

```txt
src/categorical/normalization.py
src/categorical/profiles.py
src/categorical/scoring.py
```

Genera `score_categorico`, `senales_categoricas` y `explicacion_categorica`. Esto permite defender ante el jurado cómo categorías como canal de venta, estado de póliza, tipo de impacto o ausencia de reporte policial aportan al score sin depender de una caja negra.


## Estructura de reglas comunes

Para mantener el núcleo limpio, `src/rules/base_rules.py` es solo un orquestador. Las reglas comunes viven en:

```txt
src/rules/common/temporal_rules.py
src/rules/common/amount_rules.py
src/rules/common/document_rules.py
src/rules/common/recurrence_rules.py
```

Así se evita que un solo archivo concentre todas las reglas y se facilita extender el motor sin perder trazabilidad.


## Integración con modelos de Carlos

El módulo `src/model_integration/` carga de forma segura:

```txt
models/fraud_classifier.joblib
models/anomaly_detector.joblib
```

Si no existen, usa `score_modelo = 50` y `score_anomalia = 50`, marcando `modelo_disponible = False` y `anomalia_disponible = False`. Esto evita bloquear el dashboard y mantiene trazabilidad.


## Agente antifraude robusto

El agente ahora devuelve respuestas consistentes para Justin:

```json
{
  "ok": true,
  "intent": "ranking_proveedores",
  "message": "Ranking de proveedores por concentración de riesgo.",
  "data": [],
  "source": "tools"
}
```

También expone preguntas rápidas con `get_quick_questions()` para la vista de agente/simulador. Si falta el CSV procesado, responde con un mensaje accionable en lugar de romper la UI.






## Simulador de nuevo siniestro

`simulate_new_claim(claim_data)` permite que Justin reciba datos desde un formulario y evalúe el caso sin guardarlo en el dataset. El simulador:

1. Normaliza aliases de UI (`vehiculo`, `proveedor`, `narrativa`, `documentos_presentes`).
2. Carga contexto histórico si existe `data/processed/siniestros_scored.csv`.
3. Ejecuta grafo, categórico, modelos de Carlos, NLP y reglas.
4. Devuelve la explicación tradicional y secciones listas para UI: `risk`, `signals`, `ui` y `context`.

Campos clave para Justin:

```txt
ok, simulated, source
risk.score_final, risk.nivel_riesgo, risk.accion_sugerida
signals.rules, signals.nlp, signals.graph, signals.categorical, signals.model
ui.priority_badge, ui.summary_cards, ui.recommended_next_steps
context.historical_claims_loaded, context.historical_claims_count
```

## Capa LLM opcional con OpenAI

El paquete `src/agent/llm/` separa la síntesis conversacional del router principal:

```txt
src/agent/llm/
├── base.py
├── disabled_provider.py
├── openai_provider.py
├── prompts.py
└── settings.py
```

El LLM no calcula riesgo ni modifica datos. Recibe la intención, la pregunta y la salida estructurada de herramientas/RAG para redactar una respuesta más clara. Se activa solo con:

```env
OPENAI_API_KEY=...
RASTRO_LLM_ENABLED=true
```

Por defecto queda deshabilitado para evitar costos accidentales y mantener tests/demo local sin red. El default de demo es `gpt-4o` para priorizar calidad en respuestas del agente. Si luego queremos reducir costo/latencia, basta cambiar `RASTRO_LLM_MODEL` a `gpt-4o-mini` en `.env`.

El agente devuelve metadata `llm` en respuestas exitosas:

```json
{
  "enabled": true,
  "provider": "openai",
  "model": "gpt-4o",
  "status": "ok"
}
```

## Reporte ejecutivo

El módulo `src/reports/` genera reportes desde `data/processed/siniestros_scored.csv`.

Funciones principales:

```python
generate_report_dict()
generate_report_markdown()
```

También `tools.generate_executive_summary()` usa el mismo contrato de reporte estructurado para que el agente y la UI respondan de forma consistente.
