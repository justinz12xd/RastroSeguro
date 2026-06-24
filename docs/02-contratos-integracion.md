# Contratos de integración

Este documento define lo que cada integrante entrega y consume. Si algo cambia aquí, debe comunicarse al equipo.

## Resumen

```txt
Carlos entrega dataset y modelos.
Jeremy entrega scoring, explicaciones y herramientas.
Justin consume resultados para la app y demo.
```

## 1. Entrada desde Carlos

Archivo principal:

```txt
data/synthetic/siniestros.csv
```

Columnas mínimas obligatorias:

| Columna | Uso |
|---|---|
| `id_siniestro` | Identificador único |
| `id_poliza` | Relación con póliza |
| `id_asegurado` | Relación con asegurado |
| `ramo` | Selección de reglas por ramo |
| `cobertura` | Análisis por tipo de cobertura |
| `ciudad` | Ranking geográfico |
| `id_proveedor` | Ranking/proveedor recurrente |
| `beneficiario` | Relaciones y recurrencia |
| `fecha_inicio_poliza` | Regla de borde de vigencia |
| `fecha_fin_poliza` | Regla de borde de vigencia |
| `fecha_ocurrencia` | Cálculo de fechas |
| `fecha_reporte` | Reporte tardío |
| `monto_reclamado` | Score por monto |
| `monto_estimado` | Comparación estimado/reclamado |
| `suma_asegurada` | Ratio contra cobertura |
| `descripcion` | NLP de narrativas |
| `documentos_completos` | Regla documental |
| `documentos_inconsistentes` | Regla documental crítica |
| `historial_siniestros_asegurado` | Frecuencia de reclamos |
| `etiqueta_fraude_simulada` | Entrenamiento/evaluación |

Columnas vehiculares deseables:

```txt
id_vehiculo, placa_hash, marca, modelo, anio, tipo_evento, tipo_impacto,
tercero_identificado, reporte_policial, hay_testigos, ocurrio_noche,
ocurrio_fin_semana, zona_alta_siniestralidad, historial_siniestros_vehiculo,
taller, conductor_recurrente
```

Modelos esperados cuando estén listos:

```txt
models/fraud_classifier.joblib
models/anomaly_detector.joblib
```

## 2. Salida de Jeremy hacia Justin

Archivo principal:

```txt
data/processed/siniestros_scored.csv
```

Columnas mínimas:

| Columna | Uso en UI |
|---|---|
| `id_siniestro` | Selección de caso |
| `ramo` | Filtros y comparación |
| `cobertura` | Filtros |
| `ciudad` | Rankings |
| `id_proveedor` | Rankings y relaciones |
| `beneficiario` | Relaciones |
| `monto_reclamado` | Impacto económico |
| `suma_asegurada` | Contexto del reclamo |
| `score_reglas` | Componente explicable |
| `score_modelo` | Componente ML |
| `score_anomalia` | Componente anomalías |
| `score_nlp` | Componente narrativas |
| `score_grafo` | Componente relaciones |
| `score_categorico` | Componente categórico |
| `score_final` | Ordenamiento principal |
| `nivel_riesgo` | Verde, Amarillo, Rojo |
| `alertas_activadas` | Explicación resumida |
| `explicacion` | Texto para analista |
| `accion_sugerida` | Próximo paso recomendado |

## 3. Contrato de `explain_claim`

Función:

```python
explain_claim(id_siniestro: str) -> dict
```

Salida esperada:

```json
{
  "id_siniestro": "SIN-0045",
  "score_final": 87,
  "nivel_riesgo": "Rojo",
  "alertas": ["Siniestro cerca del inicio de póliza"],
  "explicacion": "El caso requiere revisión especializada por acumulación de señales de riesgo.",
  "accion_sugerida": "Escalar a revisión antifraude especializada.",
  "componentes_score": {
    "reglas": 80,
    "modelo": 90,
    "anomalia": 75,
    "nlp": 85,
    "grafo": 70,
    "categorico": 60
  }
}
```

## 4. Contrato del simulador

Función:

```python
simulate_new_claim(claim_data: dict) -> dict
```

Entrada mínima desde el formulario de Justin:

```json
{
  "ramo": "vehiculo",
  "tipo_evento": "choque",
  "fecha_inicio_poliza": "2026-01-01",
  "fecha_ocurrencia": "2026-01-03",
  "fecha_reporte": "2026-01-10",
  "monto_reclamado": 18000,
  "suma_asegurada": 20000,
  "proveedor": "PROV-001",
  "narrativa": "Vehículo impactado por tercero no identificado.",
  "documentos_presentes": false
}
```

El simulador acepta aliases de UI como `vehiculo`, `proveedor`, `narrativa` y `documentos_presentes`, los normaliza al contrato interno y evalúa el caso sin persistirlo.

Salida compatible y enriquecida:

```json
{
  "ok": true,
  "simulated": true,
  "source": "simulator",
  "id_siniestro": "SIMULADO",
  "score_final": 84,
  "nivel_riesgo": "Rojo",
  "alertas": [],
  "explicacion": "...",
  "accion_sugerida": "Revisión especializada",
  "risk": {
    "score_final": 84,
    "nivel_riesgo": "Rojo",
    "accion_sugerida": "Revisión especializada"
  },
  "signals": {
    "rules": [],
    "nlp": {},
    "graph": {},
    "categorical": {},
    "model": {}
  },
  "ui": {
    "priority_badge": "Rojo",
    "summary_cards": [],
    "recommended_next_steps": []
  },
  "context": {
    "historical_claims_loaded": false,
    "historical_claims_count": 0
  }
}
```

## 5. Herramientas mínimas del agente

```python
get_top_risky_claims(limit=10)
explain_claim(id_siniestro)
get_risk_by_branch()
get_provider_risk_ranking()
get_city_risk_distribution()
get_similar_narratives(id_siniestro)
get_graph_connections(id_siniestro)
get_missing_documents()
generate_executive_summary()
recommend_review_order()
simulate_new_claim(claim_data)
compare_branches()
```


## 6. Guardrail de scoring

Mientras algunos componentes avanzados estén pendientes, Jeremy usará valores neutros para no romper el pipeline. Para que los casos críticos no queden subestimados:

```txt
Si score_reglas >= 90 → score_final mínimo 80
Si score_reglas >= 75 → score_final mínimo 76
```

Este ajuste es trazable y se basa únicamente en reglas auditables.


## 7. Campos adicionales por ramo para reglas

Además de las columnas mínimas, Jeremy puede aprovechar estos campos si Carlos los incluye en el dataset:

| Ramo | Campos útiles |
|---|---|
| Vehículos | `tipo_evento`, `historial_siniestros_vehiculo`, `ocurrio_noche`, `hay_testigos`, `reporte_policial`, `tercero_identificado`, `conductor_recurrente`, `zona_alta_siniestralidad` |
| Salud | `monto_promedio_procedimiento`, `frecuencia_atenciones`, `proveedor_medico_recurrente`, `clinica_recurrente`, `fecha_atencion`, `fecha_factura` |
| Hogar | `inspeccion_realizada`, `proveedor_reparacion_recurrente`, `danios_repetidos_periodo`, `causa_reportada`, `evidencia_fotografica` |
| Vida | `beneficiario_recurrente`, `cambios_recientes_poliza`, `fecha_evento`, `fecha_notificacion`, `documento_soporte` |
| Generales | `monto_promedio_cobertura`, `intermediario_recurrente`, `inconsistencia_cobertura` |

Estos campos no bloquean el pipeline si faltan; las reglas se activan solo cuando hay evidencia suficiente.


## 8. Columnas generadas por NLP

Jeremy genera estas columnas cuando el dataset incluye `descripcion`:

| Columna | Descripción |
|---|---|
| `score_nlp` | Riesgo 0-100 derivado de similitud narrativa |
| `alerta_narrativa` | Indica si se detectó narrativa similar por encima del umbral |
| `nivel_alerta_nlp` | Baja, media o alta según similitud |
| `siniestros_similares` | Lista JSON con ids y porcentajes de similitud |
| `explicacion_nlp` | Texto explicable para Justin/agente/reporte |

Estas columnas son consumidas por la vista de inteligencia antifraude y por `get_similar_narratives(id_siniestro)`.


## 9. Columnas generadas por grafo/relaciones

Jeremy genera estas columnas para análisis de relaciones cuando existen entidades suficientes en el dataset:

| Columna | Descripción |
|---|---|
| `score_grafo` | Riesgo 0-100 derivado de recurrencia de entidades críticas |
| `alerta_red` | Indica si el caso tiene entidades recurrentes relevantes |
| `entidades_recurrentes` | Lista JSON con entidades, conteos y siniestros relacionados |
| `conexiones_grafo` | Lista JSON de conexiones del siniestro para visualización |
| `explicacion_grafo` | Texto explicable del hallazgo de red |
| `proveedor_recurrente` | Flag derivado para reglas base |
| `beneficiario_recurrente` | Flag derivado para reglas base |

Estas columnas alimentan la vista de inteligencia antifraude, `get_graph_connections(id_siniestro)` y el score final.


## 10. Columnas generadas por scoring categórico

Jeremy genera estas columnas para convertir variables cualitativas en señales auditables:

| Columna | Descripción |
|---|---|
| `score_categorico` | Riesgo 0-100 derivado de variables categóricas configuradas |
| `alerta_categorica` | Indica si una categoría aportó riesgo adicional |
| `senales_categoricas` | Lista JSON con campo, valor, puntos, severidad y mensaje |
| `explicacion_categorica` | Texto explicable de la señal categórica más importante |

Campos actualmente considerados si existen: `canal_venta`, `estado_poliza`, `tipo_impacto`, `zona_inmueble`, `relacion_beneficiario`, `documentos_inconsistentes`, `zona_alta_siniestralidad`, `tercero_identificado`, `hay_testigos`, `reporte_policial`.


## 11. Contrato de modelos de Carlos

Carlos puede entregar modelos como archivos joblib:

```txt
models/fraud_classifier.joblib
models/anomaly_detector.joblib
```

Formato recomendado del artefacto:

```python
{
    "model": trained_model,
    "feature_columns": ["monto_reclamado", "suma_asegurada", "score_reglas"],
    "metrics": {"f1": 0.0, "auc": 0.0}
}
```

También se soporta guardar directamente un modelo sklearn. Si el modelo tiene `feature_names_in_`, Jeremy lo usa para alinear columnas.

Columnas generadas por integración ML:

| Columna | Descripción |
|---|---|
| `score_modelo` | Score 0-100 del modelo supervisado |
| `score_anomalia` | Score 0-100 del detector de anomalías |
| `modelo_disponible` | Indica si se cargó el clasificador |
| `anomalia_disponible` | Indica si se cargó el detector de anomalías |
| `modelo_features` | Lista JSON de features usadas por el clasificador |
| `anomalia_features` | Lista JSON de features usadas por anomalías |

Si los modelos no existen, Jeremy usa `50` como valor neutro para no romper el pipeline.


## 12. Contrato de respuesta del agente

La función `answer_question(question)` devuelve una respuesta consistente:

```json
{
  "ok": true,
  "intent": "top_riesgo",
  "message": "Casos priorizados por mayor score de riesgo.",
  "data": [],
  "source": "tools"
}
```

Si hay error:

```json
{
  "ok": false,
  "intent": "explicar_siniestro",
  "message": "Necesito el id del siniestro para responder esa pregunta.",
  "data": null,
  "source": "agent",
  "hint": "Ejemplo: Explícame el siniestro SIN-0045."
}
```

Justin puede usar `get_quick_questions()` para mostrar botones de preguntas rápidas en la UI.

La respuesta exitosa incluye metadata `llm` para que Justin pueda mostrar o depurar si hubo síntesis generativa:

```json
{
  "llm": {
    "enabled": false,
    "provider": "openai",
    "model": "gpt-4o",
    "status": "disabled_by_config"
  }
}
```

Valores esperados de `source`:

| Valor | Significado |
|---|---|
| `tools` | Respuesta local desde herramientas determinísticas |
| `rag` | Respuesta local basada en documentación interna |
| `llm` | Síntesis conversacional opcional sobre datos verificados |
| `agent` | Error o validación de la fachada del agente |

La fuente `llm` solo aparece si `OPENAI_API_KEY` y `RASTRO_LLM_ENABLED=true` están configurados.


## 13. Contrato de reporte ejecutivo

Jeremy expone dos formas de reporte:

```python
generate_report_dict()
generate_report_markdown()
```

El dict contiene:

```txt
generated_at
summary
top_casos
riesgo_por_ramo
top_proveedores
top_ciudades
ethics_note
```

Justin puede usar el dict para componentes visuales o el Markdown para una vista/exportación rápida.

Nota de calibración: con las reglas críticas RF integradas, `score_reglas` se normaliza sobre 100 puntos acumulados para evitar que señales duplicadas o frecuentes conviertan casi todo el portafolio en Rojo.
