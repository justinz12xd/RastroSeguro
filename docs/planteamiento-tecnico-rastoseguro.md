# Actualización operativa — alcance de producto

La estrategia sigue siendo construir una solución avanzada y diferenciada. La actualización es de organización, no de ambición:

```txt
Funcionalidades avanzadas: sí.
Demasiadas vistas independientes: no.
```

La app se organizará en cinco secciones principales: Dashboard, Revisión de siniestros, Inteligencia antifraude, Agente y simulador, Reporte/demo. Grafo, NLP, rankings, simulador y agente se mantienen como diferenciadores, pero agrupados para reducir carga visual y acelerar integración.

Ver:

- [`03-arquitectura-pipeline.md`](./03-arquitectura-pipeline.md)
- [`04-demo-y-vistas.md`](./04-demo-y-vistas.md)
- [`02-contratos-integracion.md`](./02-contratos-integracion.md)

---

# RastroSeguro — Planteamiento técnico y estratégico actualizado

## 1. Concepto principal

**RastroSeguro** es una plataforma de inteligencia artificial explicable para priorizar siniestros con señales de posible fraude en seguros.

La solución está diseñada como un **motor multi-ramo configurable**, capaz de analizar siniestros de distintos ramos como vehículos, hogar, salud, vida y seguros generales. Para la demo se trabajará con una especialización más profunda en el ramo vehicular, sin limitar la arquitectura únicamente a ese caso.

> RastroSeguro no acusa fraude ni rechaza automáticamente un reclamo. Genera alertas explicables para que un analista humano revise primero los casos con mayor riesgo.

---

## 2. Posicionamiento del proyecto

La idea no es construir un dashboard genérico ni un chatbot con prompts. RastroSeguro debe presentarse como un **copiloto antifraude explicable**, basado en datos, modelos, reglas auditables, análisis de relaciones y agente consultivo.

### Frase corta

> RastroSeguro es un motor multi-ramo de priorización antifraude que combina IA, reglas de negocio, análisis de anomalías, NLP y grafos de relación para apoyar la revisión humana de siniestros.

### Frase para pitch

> RastroSeguro ayuda a las aseguradoras a priorizar siniestros con señales de posible fraude mediante un score explicable, combinando modelos entrenados, reglas auditables, análisis de texto, detección de anomalías, grafos de relación y un agente de IA conectado a herramientas verificables.

---

## 3. Decisión estratégica: multi-ramo configurable + foco fuerte en vehículos

La estrategia final será:

```txt
Motor antifraude multi-ramo configurable
+ demo profunda en vehículos
+ extensibilidad visible hacia salud, hogar, vida y generales
```

Esto permite tener:

- **Alcance:** la solución no queda limitada a un solo tipo de seguro.
- **Profundidad:** la demo vehicular permite mostrar patrones más ricos.
- **Diferenciación:** no es solo un detector aislado, sino una arquitectura extensible.
- **Claridad técnica:** cada ramo puede tener sus propias reglas, variables, pesos y explicaciones.
- **Mejor historia para el jurado:** se demuestra una solución aplicable a negocio real, no solo a un CSV preparado.

---

## 4. Problema que resuelve

En una aseguradora, los siniestros pueden presentar señales de riesgo que no son evidentes en una revisión individual. El analista debe cruzar información de pólizas, fechas, montos, documentos, asegurados, proveedores, beneficiarios, vehículos, historiales y narrativas.

El problema principal es que este análisis puede ser lento, manual y disperso.

RastroSeguro busca:

- Reducir el tiempo de priorización inicial.
- Ordenar los casos por nivel de riesgo.
- Explicar por qué un caso requiere revisión.
- Detectar patrones no evidentes entre siniestros.
- Evitar decisiones automáticas injustas.
- Facilitar el trabajo de analistas, auditoría, riesgos y gerencia.

---

## 5. Usuarios beneficiarios

| Usuario | Beneficio |
|---|---|
| Analista de siniestros | Revisión priorizada y explicación de alertas. |
| Analista antifraude | Identificación temprana de patrones sospechosos. |
| Jefatura de siniestros | Visión consolidada de riesgo operativo. |
| Auditoría interna | Trazabilidad de reglas, score y evidencia. |
| Riesgos | Monitoreo de exposición por ramo, ciudad o proveedor. |
| Tecnología | Base modular para integración futura. |
| Gerencia | Indicadores de impacto, ahorro potencial y control. |

---

## 6. Diferenciador frente a otros equipos

Muchos equipos probablemente construirán:

```txt
Dataset sintético + reglas IF/ELSE + dashboard + ChatGPT
```

RastroSeguro debe diferenciarse con:

```txt
Motor multi-ramo configurable
+ reglas base y reglas por ramo
+ modelo ML entrenado
+ detector de anomalías
+ NLP de narrativas similares
+ grafo de relaciones
+ agente con herramientas
+ RAG documental liviano
+ simulador de nuevo siniestro
+ modo jurado
+ feedback humano
+ reporte ejecutivo
```

La idea central:

> RastroSeguro no es un chatbot antifraude. Es una plataforma explicable de priorización de siniestros, diseñada para operar por ramos y justificar cada alerta con evidencia trazable.

---

## 7. Enfoque multi-ramo

RastroSeguro tendrá un **core común** para todos los ramos y **paquetes especializados** para cada tipo de seguro.

### 7.1 Core común

Variables comunes a todos los ramos:

```txt
id_siniestro
id_poliza
id_asegurado
ramo
cobertura
fecha_inicio_poliza
fecha_fin_poliza
fecha_ocurrencia
fecha_reporte
dias_desde_inicio_poliza
dias_desde_fin_poliza
dias_entre_ocurrencia_reporte
monto_reclamado
monto_estimado
monto_pagado
suma_asegurada
ratio_monto_suma_asegurada
ciudad
sucursal
descripcion
documentos_completos
documentos_inconsistentes
historial_siniestros_asegurado
id_proveedor
beneficiario
proveedor_recurrente
etiqueta_fraude_simulada
```

Señales comunes:

```txt
Reporte tardío
Monto atípico
Documentos incompletos
Documentos inconsistentes
Proveedor recurrente
Beneficiario recurrente
Asegurado con alta frecuencia de reclamos
Narrativa similar
Siniestro cerca del inicio o fin de póliza
Monto cercano a suma asegurada
```

### 7.2 Paquete especializado: vehículos

Variables adicionales:

```txt
id_vehiculo
placa_hash
chasis_hash
motor_hash
marca
modelo
anio
tipo_evento
tipo_impacto
tercero_identificado
reporte_policial
hay_testigos
ocurrio_noche
ocurrio_fin_semana
zona_alta_siniestralidad
historial_siniestros_vehiculo
taller
conductor_recurrente
```

Señales específicas:

```txt
Vehículo con múltiples siniestros
Conductor recurrente
Accidente nocturno sin testigos
Ausencia de reporte policial
Tercero no identificado
Dinámica sospechosa
Robo total cercano al inicio de póliza
Taller recurrente con alta concentración de alertas
Narrativas clonadas sobre choque, robo o fuga de tercero
```

### 7.3 Paquete básico: salud

Variables adicionales:

```txt
clinica
especialidad
procedimiento
diagnostico_general
fecha_atencion
fecha_factura
frecuencia_atenciones
proveedor_medico_recurrente
```

Señales específicas:

```txt
Clínica recurrente con alta concentración de alertas
Procedimiento con monto superior al promedio
Documentos médicos incompletos
Facturas emitidas fuera de secuencia lógica
Frecuencia atípica de atenciones
Narrativas repetidas en reclamos médicos
```

### 7.4 Paquete básico: hogar

Variables adicionales:

```txt
tipo_inmueble
tipo_danio
causa_reportada
proveedor_reparacion
inspeccion_realizada
zona_inmueble
```

Señales específicas:

```txt
Daño reportado tarde
Monto cercano a suma asegurada
Proveedor de reparación recurrente
Daños repetidos en corto periodo
Documentos inconsistentes
Narrativas similares sobre incendio, inundación o robo
```

### 7.5 Paquete básico: vida y generales

Variables adicionales:

```txt
tipo_cobertura
beneficiario
relacion_beneficiario
documento_soporte
fecha_evento
fecha_notificacion
```

Señales específicas:

```txt
Beneficiario recurrente
Documentación incompleta
Cambios recientes antes del evento
Reporte tardío
Monto atípico
Inconsistencias entre fechas y documentos
```

---

## 8. Arquitectura de reglas configurables

El motor debe estar organizado por paquetes de reglas.

```txt
src/rules/
├── base_rules.py
├── vehicle_rules.py
├── health_rules.py
├── home_rules.py
├── life_rules.py
├── general_rules.py
└── rule_registry.py
```

Ejemplo conceptual:

```python
RULE_PACKS = {
    "vehiculos": vehicle_rules,
    "salud": health_rules,
    "hogar": home_rules,
    "vida": life_rules,
    "generales": general_rules,
}
```

Flujo:

```txt
Siniestro entra
      ↓
Se identifica el ramo
      ↓
Se aplican reglas base
      ↓
Se aplican reglas específicas del ramo
      ↓
Se calculan alertas
      ↓
Se genera explicación
```

Mensaje para defensa técnica:

> RastroSeguro no tiene reglas quemadas para un único escenario. Usa un motor configurable por ramo, lo que permite adaptar variables, reglas y pesos según la naturaleza del siniestro.

---

## 9. Dataset sintético

### Decisión

Usar dataset sintético creado por el equipo.

Razones:

- Evita datos personales reales.
- Permite controlar patrones para la demo.
- Permite generar casos normales, amarillos y rojos.
- Permite entrenar y evaluar modelos.
- Permite simular siniestros multi-ramo sin depender de datos externos.

### Tamaño recomendado

```txt
3000 siniestros sintéticos
```

Distribución sugerida por ramo:

```txt
70% vehículos
10% hogar
10% salud
5% vida
5% generales
```

Distribución sugerida por riesgo:

```txt
70% casos normales
20% casos de riesgo medio
10% casos de riesgo alto
```

### Archivos sugeridos

```txt
data/
├── raw/
│   ├── siniestros.csv
│   ├── polizas.csv
│   ├── asegurados.csv
│   ├── vehiculos.csv
│   ├── proveedores.csv
│   └── documentos.csv
├── processed/
│   └── siniestros_scored.csv
└── synthetic/
    └── synthetic_claims_dataset.csv
```

---

## 10. Escenarios sintéticos inyectados

El dataset no debe ser aleatorio sin sentido. Debe incluir escenarios preparados.

### Escenarios comunes

```txt
Siniestro cerca del inicio de póliza
Siniestro cerca del fin de póliza
Reporte tardío
Monto reclamado atípico
Monto cercano a suma asegurada
Documentos incompletos
Documentos inconsistentes
Proveedor recurrente
Beneficiario recurrente
Narrativa similar
Asegurado con múltiples reclamos
Cambios recientes en datos antes del siniestro
```

### Escenarios vehiculares

```txt
Robo total pocos días después de contratar la póliza
Choque nocturno sin testigos ni reporte policial
Tercero no identificado
Taller con alta concentración de alertas
Vehículo con múltiples siniestros
Conductor recurrente en varios reclamos
Narrativas clonadas sobre choque y fuga
```

### Escenarios salud

```txt
Clínica recurrente con múltiples casos observados
Procedimiento con monto superior al promedio
Documentos médicos incompletos
Facturas con fechas inconsistentes
Atenciones repetidas en periodos cortos
```

### Escenarios hogar

```txt
Daño por incendio reportado tarde
Reparaciones repetidas con el mismo proveedor
Monto cercano a suma asegurada
Documentos de inspección incompletos
Narrativas repetidas sobre robo o inundación
```

---

## 11. Modelos de IA

RastroSeguro no dependerá de un único modelo. Usará un enfoque híbrido.

### 11.1 Modelo supervisado

Modelo sugerido:

```txt
RandomForestClassifier
```

Objetivo:

```txt
Predecir probabilidad de riesgo de posible fraude.
```

Variable objetivo:

```txt
etiqueta_fraude_simulada
```

Features comunes:

```txt
dias_desde_inicio_poliza
dias_desde_fin_poliza
dias_entre_ocurrencia_reporte
monto_reclamado
monto_estimado
ratio_monto_suma_asegurada
historial_siniestros_asegurado
reclamos_proveedor_ultimos_12m
documentos_completos
documentos_inconsistentes
proveedor_recurrente
beneficiario_recurrente
ramo
cobertura
ciudad
```

Features vehiculares adicionales:

```txt
historial_siniestros_vehiculo
reporte_policial
hay_testigos
ocurrio_noche
ocurrio_fin_semana
tercero_identificado
zona_alta_siniestralidad
conductor_recurrente
```

Métricas:

```txt
Precision
Recall
F1-score
Matriz de confusión
AUC-ROC
Importancia de variables
```

### 11.2 Detector de anomalías

Modelo sugerido:

```txt
IsolationForest
```

Objetivo:

```txt
Detectar siniestros atípicos frente al comportamiento general.
```

Valor diferencial:

> Permite detectar casos raros que tal vez no activan muchas reglas manuales, pero cuya combinación de variables no se parece al comportamiento normal.

### 11.3 NLP de narrativas

Versión segura:

```txt
TfidfVectorizer + cosine_similarity
```

Versión avanzada si hay tiempo:

```txt
Embeddings semánticos
```

Objetivo:

```txt
Detectar relatos similares, repetidos o clonados entre siniestros.
```

Salida esperada:

```txt
score_nlp
siniestros_similares
porcentaje_similitud
fragmentos relevantes
alerta_narrativa
```

Ejemplo:

```txt
Narrativa con 91% de similitud con SIN-0381 y SIN-0912.
Patrón detectado: "vehículo desconocido impacta y huye".
```

### 11.4 Grafo de relaciones

Herramientas sugeridas:

```txt
NetworkX
PyVis
Plotly
```

Nodos:

```txt
Asegurado
Siniestro
Proveedor
Beneficiario
Vehículo
Ciudad
Ramo
Cobertura
```

Relaciones:

```txt
Asegurado -> Siniestro
Siniestro -> Proveedor
Siniestro -> Beneficiario
Siniestro -> Vehículo
Siniestro -> Ciudad
Siniestro -> Ramo
```

Métricas:

```txt
Degree centrality
Número de casos rojos por proveedor
Número de conexiones por beneficiario
Comunidades de riesgo
Concentración de alertas por red
```

Salida:

```txt
score_grafo
nodos_relacionados
alerta_red
explicacion_red
```

### 11.5 Scoring categórico inspirado en RIDIT/PRIDIT

Se usará como inspiración metodológica para variables categóricas.

Idea:

```txt
Variables tipo Sí/No o categorías pueden transformarse en señales cuantificables de anormalidad.
```

Ejemplos:

```txt
documentos_inconsistentes
hay_testigos
reporte_policial
proveedor_recurrente
zona_alta_siniestralidad
tercero_identificado
beneficiario_recurrente
```

Valor para el pitch:

> Además del ML, usamos una lógica estadística interpretable para tratar variables categóricas como señales de riesgo cuantificables.

---

## 12. Score final

El score final será compuesto, explicable y trazable.

```txt
score_final =
  30% score_reglas
+ 25% score_modelo_supervisado
+ 15% score_anomalias
+ 15% score_nlp
+ 10% score_grafo
+ 5% score_categorico
```

### Clasificación

| Rango | Nivel | Acción sugerida |
|---:|---|---|
| 0 - 40 | Verde | Continuar flujo normal |
| 41 - 75 | Amarillo | Revisión documental |
| 76 - 100 | Rojo | Revisión especializada |

### Salida por siniestro

```txt
score_reglas
score_modelo
score_anomalia
score_nlp
score_grafo
score_categorico
score_final
nivel_riesgo
alertas_activadas
explicacion_textual
accion_sugerida
```

---

## 13. Agente de IA

El agente será un **copiloto antifraude**, no un chatbot libre.

### Principio

```txt
El agente no inventa respuestas.
El agente consulta herramientas conectadas al pipeline.
```

### Herramientas internas

```txt
get_top_risky_claims()
explain_claim(id_siniestro)
get_risk_by_branch()
get_provider_risk_ranking()
get_city_risk_distribution()
get_similar_narratives(id_siniestro)
get_graph_connections(id_siniestro)
get_missing_documents()
generate_executive_summary()
recommend_review_order()
simulate_new_claim()
compare_branches()
```

### Preguntas que debe responder

```txt
¿Cuáles son los 10 siniestros con mayor riesgo?
¿Qué ramo concentra más alertas rojas?
¿Por qué este siniestro fue marcado como rojo?
¿Qué proveedores concentran más alertas?
¿Qué ciudades tienen mayor concentración de riesgo?
¿Qué documentos faltan en los casos críticos?
¿Qué casos tienen montos atípicos?
¿Qué siniestros ocurrieron cerca del inicio de la póliza?
¿Qué narrativas son similares?
¿Qué patrones se repiten en los reclamos sospechosos?
Genera un resumen ejecutivo de los casos críticos.
Recomienda qué casos debería revisar primero el analista.
```

---

## 14. RAG y LangChain

### Decisión

Usar **RAG liviano para documentación**, pero no depender obligatoriamente de LangChain.

### Uso correcto de RAG

RAG servirá para consultar:

```txt
Reglas de negocio
Documentación del modelo
Limitaciones éticas
Diccionario de datos
Manual del sistema
Criterios de evaluación
Metodología interna
```

Ejemplos:

```txt
¿Qué significa un caso amarillo?
¿Qué limitaciones tiene el modelo?
¿Qué reglas se usan para documentos inconsistentes?
¿Qué variables usa el score?
```

### No usar RAG para datos tabulares

Para preguntas sobre siniestros, proveedores, rankings o scores, el agente debe llamar herramientas reales.

Correcto:

```txt
Pregunta: ¿Qué proveedores concentran más alertas?
Respuesta: get_provider_risk_ranking()
```

No recomendado:

```txt
Meter todo el CSV en un vector database y esperar que el LLM calcule rankings.
```

### LangChain

LangChain puede usarse si ayuda, pero no debe ser una dependencia crítica.

Ruta recomendada:

```txt
Primero: tools propias + router de intención
Después: RAG liviano
Finalmente: LangChain o LlamaIndex si ya está estable
```

Mensaje para jurado:

> Usamos RAG para documentación y herramientas verificables para análisis estructurado. Así evitamos que el agente invente resultados o calcule incorrectamente sobre datos tabulares.

---

## 15. Fine-tuning

### Decisión

No usar fine-tuning del LLM como base.

Razones:

```txt
El LLM no debe memorizar siniestros.
Los datos cambian.
La trazabilidad es más importante que el estilo.
Preparar un fine-tuning robusto toma tiempo.
El agente debe consultar herramientas verificables.
```

### Extra recomendado: router de intención entrenado

En lugar de fine-tuning completo, entrenar un clasificador ligero para decidir qué herramienta usar.

Intenciones:

```txt
top_riesgo
explicar_siniestro
ranking_proveedores
ranking_ciudades
riesgo_por_ramo
documentos_faltantes
narrativas_similares
resumen_ejecutivo
simular_siniestro
comparar_ramos
```

Datos necesarios:

```txt
100 a 300 preguntas sintéticas etiquetadas
```

Modelos:

```txt
LogisticRegression
LinearSVC
RandomForestClassifier
```

Valor para pitch:

> Además de los modelos de riesgo, entrenamos una capa de intención para que el agente seleccione herramientas analíticas sin depender únicamente de prompts.

---

## 16. Aplicación web

Stack recomendado:

```txt
Python
Next.js
Pandas
Scikit-learn
Plotly
NetworkX
PyVis
Joblib
SQLite o CSV
```

### Vistas principales

```txt
Dashboard ejecutivo
Carga de dataset
Bandeja de revisión
Detalle del siniestro
Vista multi-ramo
Grafo de relaciones
Simulador de nuevo siniestro
Agente antifraude
Reporte de auditoría
Feedback humano
Modo jurado
```

---

## 17. Dashboard ejecutivo

Métricas:

```txt
Total de siniestros analizados
Total por ramo
Casos verdes
Casos amarillos
Casos rojos
Monto total reclamado
Monto en casos rojos
Porcentaje de casos de alto riesgo
Top ciudades con alertas
Top proveedores con alertas
Ramo con mayor concentración de riesgo
```

Gráficos:

```txt
Distribución de riesgo por ramo
Distribución por nivel de riesgo
Riesgo por ciudad
Riesgo por proveedor
Riesgo por cobertura
Evolución temporal de siniestros
Monto reclamado vs score
```

---

## 18. Carga de dataset

Funcionalidades:

```txt
Cargar CSV propio
Usar dataset sintético de demo
Validar columnas requeridas
Detectar ramo
Aplicar reglas base
Aplicar reglas específicas
Procesar dataset
Generar score
Exportar dataset procesado
```

Valor:

> Esta vista demuestra que RastroSeguro no está amarrado a un archivo preparado. Puede recibir nuevos datos, validarlos y analizarlos.

---

## 19. Bandeja de revisión

Tabla ordenada por score.

Columnas:

```txt
id_siniestro
ramo
ciudad
proveedor
cobertura
monto_reclamado
score_final
nivel_riesgo
alertas_activadas
accion_sugerida
```

Filtros:

```txt
ramo
nivel de riesgo
ciudad
proveedor
cobertura
documentos inconsistentes
rango de score
```

---

## 20. Detalle del siniestro

Debe mostrar:

```txt
Score final
Nivel de riesgo
Ramo
Datos del siniestro
Reglas base activadas
Reglas específicas activadas
Score por componente
Narrativas similares
Relaciones del caso
Documentos faltantes
Recomendación
```

Ejemplo:

```txt
El siniestro SIN-0045 fue marcado como riesgo rojo porque ocurrió 2 días después del inicio de la póliza, el monto reclamado representa el 97% de la suma asegurada, el proveedor aparece en 8 casos observados y la narrativa tiene 91% de similitud con otros reclamos. Se recomienda revisión especializada antes de continuar el flujo.
```

---

## 21. Vista multi-ramo

Objetivo:

```txt
Mostrar que RastroSeguro puede comparar riesgo entre distintos tipos de seguros.
```

Debe incluir:

```txt
Riesgo promedio por ramo
Cantidad de casos rojos por ramo
Monto expuesto por ramo
Reglas más activadas por ramo
Proveedores críticos por ramo
Evolución por ramo
```

Pregunta de demo:

```txt
¿Qué ramo concentra más alertas rojas y por qué?
```

---

## 22. Grafo de relaciones

Visualización:

```txt
Asegurado -> Siniestro -> Proveedor
Siniestro -> Beneficiario
Siniestro -> Vehículo
Siniestro -> Ramo
Siniestro -> Ciudad
```

Objetivo:

```txt
Detectar concentración de riesgo y relaciones no evidentes.
```

Diferenciador:

> Permite mostrar que un caso puede parecer normal de forma aislada, pero volverse sospechoso al observar sus conexiones.

---

## 23. Simulador de nuevo siniestro

Formulario con selector de ramo:

```txt
Vehículos
Salud
Hogar
Vida
Generales
```

Campos comunes:

```txt
fecha_inicio_poliza
fecha_fin_poliza
fecha_ocurrencia
fecha_reporte
monto_reclamado
monto_estimado
suma_asegurada
ciudad
proveedor
descripcion
documentos_completos
documentos_inconsistentes
```

Campos dinámicos por ramo:

```txt
Vehículos: reporte_policial, hay_testigos, tercero_identificado, tipo_impacto, ocurrió_noche.
Salud: clínica, procedimiento, fecha_atención, fecha_factura.
Hogar: tipo_inmueble, tipo_daño, inspección_realizada.
Vida: beneficiario, relación_beneficiario, documento_soporte.
```

Salida:

```txt
score_final
nivel_riesgo
alertas_activadas
explicacion
accion_sugerida
siniestros similares
relaciones relevantes
```

Valor para demo:

> El jurado puede pedir un caso nuevo y el sistema lo evalúa en vivo.

---

## 24. Reporte para auditoría

Debe generar un reporte en Markdown, HTML o PDF.

Contenido:

```txt
Resumen ejecutivo
Top 10 casos críticos
Riesgo por ramo
Proveedores con más alertas
Ciudades con mayor concentración
Monto total expuesto
Principales reglas activadas
Casos con narrativas similares
Limitaciones del modelo
Recordatorio de revisión humana
```

---

## 25. Feedback humano

Flujo simple:

```txt
Analista marca el caso como:
- Requiere más documentos
- Revisado sin novedad
- Posible fraude confirmado
- Falso positivo
```

Guardar en:

```txt
feedback_analista.csv
```

Valor para pitch:

> En producción, la retroalimentación del analista permitiría reentrenar y mejorar el modelo con evidencia real.

---

## 26. Modo jurado

Vista especial para demo rápida.

Botones:

```txt
Caso rojo evidente
Caso rojo no evidente
Caso amarillo ético
Proveedor recurrente
Narrativa clonada
Riesgo por ramo
Simulación en vivo
Resumen ejecutivo automático
```

Objetivo:

```txt
Evitar perder tiempo buscando casos durante la presentación.
```

---

## 27. Estructura del repositorio

```txt
rastroseguro/
├── README.md
├── requirements.txt
├── .env.example
├── data/
│   ├── raw/
│   ├── processed/
│   └── synthetic/
├── notebooks/
│   ├── 01_exploracion_datos.ipynb
│   ├── 02_modelo_riesgo.ipynb
│   └── 03_evaluacion_modelo.ipynb
├── src/
│   ├── data/
│   │   ├── generate_synthetic_data.py
│   │   ├── load_data.py
│   │   └── validate_schema.py
│   ├── features/
│   │   └── build_features.py
│   ├── rules/
│   │   ├── base_rules.py
│   │   ├── vehicle_rules.py
│   │   ├── health_rules.py
│   │   ├── home_rules.py
│   │   ├── life_rules.py
│   │   ├── general_rules.py
│   │   └── rule_registry.py
│   ├── models/
│   │   ├── train_classifier.py
│   │   ├── train_anomaly.py
│   │   └── predict.py
│   ├── nlp/
│   │   └── narrative_similarity.py
│   ├── graph/
│   │   └── relationship_graph.py
│   ├── scoring/
│   │   └── final_score.py
│   ├── explainability/
│   │   └── explain_claim.py
│   ├── agent/
│   │   ├── tools.py
│   │   ├── router.py
│   │   ├── rag.py
│   │   └── antifraud_agent.py
│   └── reports/
│       └── generate_report.py
├── app/
│   └── main.py
├── docs/
│   ├── arquitectura.md
│   ├── modelo_datos.md
│   ├── reglas_negocio.md
│   ├── uso_ia.md
│   ├── etica_limitaciones.md
│   └── pitch.md
├── tests/
│   ├── test_rules.py
│   ├── test_scoring.py
│   ├── test_data_validation.py
│   └── test_agent_tools.py
└── presentation/
    └── pitch.pdf
```

---

## 28. Entregables

### Obligatorios

```txt
Prototipo funcional
Código fuente
Dataset sintético
README
Arquitectura
Modelo de datos
Explicación del modelo IA
Rúbrica de alertas
Demo funcional
Presentación ejecutiva
```

### Extras diferenciales

```txt
Motor multi-ramo configurable
Simulador de nuevo siniestro
Vista multi-ramo
Grafo de relaciones
Agente con herramientas
RAG documental liviano
Reporte de auditoría
Feedback humano
Modo jurado
Router de intención entrenado
Documentación ética
```

---

## 29. Plan de trabajo de 72 horas

### Fase 1: 0 a 12 horas

Objetivo:

```txt
Base funcional.
```

Tareas:

```txt
Crear repositorio
Definir estructura
Crear dataset sintético multi-ramo
Crear motor de reglas base
Crear reglas vehiculares iniciales
Crear score inicial
Crear dashboard básico
Mostrar tabla con semáforo
```

Resultado:

```txt
Ya existe una demo mínima funcional.
```

### Fase 2: 12 a 24 horas

Objetivo:

```txt
IA inicial.
```

Tareas:

```txt
Feature engineering
Entrenar RandomForestClassifier
Entrenar IsolationForest
Guardar modelos con joblib
Calcular score_modelo
Calcular score_anomalia
Unificar score final
Mostrar métricas
```

Resultado:

```txt
Sistema ya usa modelos entrenados.
```

### Fase 3: 24 a 40 horas

Objetivo:

```txt
Diferenciadores técnicos.
```

Tareas:

```txt
Implementar NLP de narrativas
Calcular similitud textual
Agregar score_nlp
Crear grafo de relaciones
Crear ranking de proveedores
Crear ranking de ciudades
Crear vista multi-ramo
Mejorar detalle del siniestro
```

Resultado:

```txt
Sistema muestra patrones complejos y comparación por ramo.
```

### Fase 4: 40 a 56 horas

Objetivo:

```txt
Agente, simulador y documentación viva.
```

Tareas:

```txt
Crear herramientas del agente
Crear router de intención
Crear agente consultivo
Agregar preguntas predefinidas
Implementar RAG documental liviano
Implementar simulador de nuevo siniestro
Agregar reporte ejecutivo
Agregar feedback humano
```

Resultado:

```txt
Sistema ya tiene demo avanzada.
```

### Fase 5: 56 a 72 horas

Objetivo:

```txt
Pulido y presentación.
```

Tareas:

```txt
Pulir UI
Preparar casos estrella
Crear modo jurado
Finalizar README
Finalizar documentación
Preparar pitch
Ensayar demo
Probar instalación desde cero
Preparar respuestas del jurado
```

Resultado:

```txt
Proyecto listo para competir.
```

---

## 30. Repartición del equipo

### Persona 1: Datos + modelos

Responsable de:

```txt
Dataset sintético multi-ramo
Feature engineering
RandomForest
IsolationForest
Métricas
Exportación de datos procesados
```

### Persona 2: Scoring + reglas + agente

Responsable de:

```txt
Motor de reglas base
Reglas por ramo
Score final
Explicaciones
Herramientas del agente
Router de intención
RAG documental
Simulador de nuevo siniestro
```

### Persona 3: Dashboard + grafo + documentación

Responsable de:

```txt
Next.js
Dashboard
Vista multi-ramo
Gráficos
Detalle de siniestro
Grafo de relaciones
README
Documentación
Pitch visual
```

---

## 31. Casos estrella para la demo

### Caso 1: rojo evidente

Características:

```txt
Siniestro ocurre 1 día después de iniciar póliza.
Monto reclamado es 98% de la suma asegurada.
Documentos inconsistentes.
Proveedor en lista restrictiva.
```

Mensaje:

> Este caso demuestra que el sistema identifica señales críticas claras.

### Caso 2: rojo no evidente

Características:

```txt
No activa muchas reglas simples.
Pero el modelo de anomalías lo marca.
El grafo muestra proveedor recurrente.
La narrativa es similar a otros reclamos.
```

Mensaje:

> Este caso demuestra que RastroSeguro detecta patrones que una revisión individual podría pasar por alto.

### Caso 3: amarillo ético

Características:

```txt
Tiene algunas señales de riesgo.
No hay evidencia suficiente para escalar a rojo.
Se recomienda revisión documental.
```

Mensaje:

> Este caso demuestra que el sistema no acusa automáticamente. Prioriza revisión humana.

### Caso 4: comparación multi-ramo

Características:

```txt
Dashboard compara vehículos, salud, hogar, vida y generales.
Muestra qué ramo concentra más alertas rojas.
Muestra monto expuesto por ramo.
Muestra reglas más activadas por ramo.
```

Mensaje:

> Este caso demuestra que RastroSeguro no es un detector aislado, sino una arquitectura configurable por ramo.

### Caso 5: simulación en vivo

El jurado puede pedir:

```txt
Crear un siniestro con monto alto, reporte tardío y documentos inconsistentes.
```

El sistema debe responder:

```txt
Score alto
Nivel de riesgo
Explicación por reglas
Comparación con casos similares
Relaciones relevantes
Acción sugerida
```

---

## 32. Pitch técnico sugerido

> RastroSeguro es un copiloto antifraude explicable para la priorización de siniestros. La plataforma analiza datos sintéticos de pólizas, asegurados, proveedores, beneficiarios, documentos y reclamos, y calcula un score de riesgo mediante un enfoque híbrido: reglas de negocio, machine learning supervisado, detección de anomalías, análisis de narrativas, scoring categórico y grafos de relación. Su arquitectura es multi-ramo y configurable, permitiendo adaptar reglas, variables y pesos según el tipo de seguro. El agente de IA no responde únicamente con prompts: consulta herramientas auditables conectadas al pipeline de datos y usa RAG documental para explicar reglas, metodología y limitaciones. RastroSeguro no acusa fraude ni rechaza reclamos; prioriza casos para revisión humana.

---

## 33. Respuestas preparadas para jurado

### ¿Qué modelo de IA usaron?

> Usamos un enfoque híbrido. Entrenamos un Random Forest con datos sintéticos etiquetados para estimar probabilidad de riesgo, usamos Isolation Forest para detectar anomalías, NLP para similitud de narrativas, un grafo de relaciones para encontrar concentración de riesgo y un score categórico para variables cualitativas. El agente consulta herramientas sobre estos resultados.

### ¿Es un sistema solo para vehículos?

> No. RastroSeguro está diseñado como un motor multi-ramo configurable. Tiene reglas base para todos los siniestros y paquetes especializados por ramo. En la demo mostramos mayor profundidad en un ramo, pero el sistema permite extender reglas y variables para salud, hogar, vida y generales.

### ¿Por qué no usaron fine-tuning del LLM?

> Porque el objetivo no es que el LLM memorice casos, sino que consulte datos verificables. En fraude, la trazabilidad y la explicabilidad son más importantes que el estilo conversacional. Por eso entrenamos modelos específicos y usamos el agente como capa consultiva conectada a herramientas.

### ¿Usaron RAG?

> Sí, pero de forma controlada. RAG se usa para documentación, reglas, metodología y limitaciones. Para datos tabulares, rankings y explicaciones de siniestros usamos herramientas conectadas directamente al pipeline, evitando respuestas inventadas.

### ¿Cómo evitan acusar injustamente?

> El sistema habla de riesgo o posible fraude, nunca de fraude confirmado. No rechaza reclamos ni toma decisiones automáticas. Toda alerta requiere revisión humana.

### ¿Qué pasa si el modelo se equivoca?

> El sistema muestra las razones del score y permite feedback del analista. Esa retroalimentación puede usarse para mejorar el modelo en futuras iteraciones.

### ¿Cómo validaron el modelo?

> Usamos datos sintéticos etiquetados con patrones controlados, separamos datos de entrenamiento y prueba, y medimos precision, recall, F1-score, matriz de confusión y AUC-ROC. Además, contrastamos el score con reglas explicables.

### ¿Cómo ayuda al negocio?

> Reduce el tiempo de priorización, permite revisar primero los casos más riesgosos, mejora la trazabilidad del análisis y ayuda a monitorear exposición por ramo, ciudad, proveedor y patrón de riesgo.

---

## 34. Principios éticos

RastroSeguro debe cumplir:

```txt
No usar datos personales reales.
No usar información confidencial.
Usar datos sintéticos o públicos.
Anonimizar identificadores.
No subir credenciales.
No exponer llaves de API.
No acusar fraude automáticamente.
No rechazar reclamos automáticamente.
Mantener revisión humana.
Explicar limitaciones.
Documentar posibles falsos positivos.
```

Mensaje final:

> La IA no decide. La IA alerta, explica y recomienda revisión.

---

## 35. Prioridad de implementación

### Debe estar sí o sí

```txt
Dataset sintético multi-ramo
Carga de dataset
Score de riesgo
Semáforo
Motor de reglas base
Reglas vehiculares
Modelo ML
Dashboard
Bandeja de revisión
Detalle con explicación
README
Pitch
```

### Muy importante para destacar

```txt
Vista multi-ramo
NLP de narrativas similares
Grafo de relaciones
Agente con herramientas
Simulador de nuevo siniestro
Reporte ejecutivo
Modo jurado
```

### Extra si sobra tiempo

```txt
Router de intención entrenado
RAG documental liviano
Feedback humano
SHAP o importancia de variables
Exportación PDF
API con FastAPI
```

---

## 36. Roadmap futuro

Para una versión real en producción:

```txt
Integración con core de seguros.
Conexión a bases de datos internas.
Configuración avanzada de reglas por ramo.
Validación con analistas antifraude.
Reentrenamiento con feedback humano.
Monitoreo de drift del modelo.
Auditoría de decisiones.
Control de sesgos.
API para integración con sistemas existentes.
Alertas automáticas para unidades antifraude.
Panel de administración de reglas.
```

---

## 37. Resumen ejecutivo

RastroSeguro es una solución de IA explicable para priorizar siniestros con señales de posible fraude. Su arquitectura multi-ramo permite configurar reglas, variables y pesos según el tipo de seguro, mientras que su demo profundiza en un caso de uso con mayor riqueza operativa. La solución combina reglas de negocio, modelos entrenados, detección de anomalías, NLP, scoring categórico, grafos de relación y un agente consultivo conectado a herramientas. El sistema genera un score de riesgo, clasifica casos por semáforo, explica alertas, permite simular nuevos siniestros y mantiene siempre la revisión humana como principio central.
