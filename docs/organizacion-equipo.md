# Actualización operativa — coordinación actual

Para trabajar mejor en paralelo, la coordinación vigente está resumida en:

- [`01-guia-general-equipo.md`](./01-guia-general-equipo.md)
- [`02-contratos-integracion.md`](./02-contratos-integracion.md)
- [`04-demo-y-vistas.md`](./04-demo-y-vistas.md)
- [`equipo/carlos-datos-modelos.md`](./equipo/carlos-datos-modelos.md)
- [`equipo/jeremy-scoring-agente.md`](./equipo/jeremy-scoring-agente.md)
- [`equipo/justin-nextjs-puente-api.md`](./equipo/justin-nextjs-puente-api.md)

Decisión actual: mantenemos funcionalidades avanzadas, pero reducimos pantallas independientes. Las capacidades de grafo, narrativas, agente, simulador y reporte se agrupan en vistas con tabs internas. “Modo jurado” deja de ser un módulo formal y pasa a cubrirse como **casos estrella / demo ejecutiva**.

---

# RastroSeguro — Organización del Equipo y Plan de Trabajo

## 1. Objetivo de esta organización

Este documento define cómo se dividirá el trabajo entre **Carlos, Justin y Jeremy** para construir **RastroSeguro**, una solución de IA explicable para priorización antifraude en siniestros.

El objetivo es evitar desorden durante el desarrollo y trabajar con módulos claros, entregables definidos y puntos de integración constantes.

La meta técnica es construir una solución que no sea solo un dashboard o un chatbot, sino una plataforma con:

```txt
Dataset sintético multi-ramo
+ motor de reglas configurable
+ modelo ML entrenado
+ detección de anomalías
+ NLP para narrativas similares
+ grafo de relaciones
+ agente con herramientas
+ RAG documental liviano
+ simulador de nuevo siniestro
+ dashboard funcional
+ modo jurado
+ reporte ejecutivo
```

---

## 2. Estrategia general del proyecto

RastroSeguro se construirá como:

```txt
Motor multi-ramo configurable
+ demo fuerte en un ramo principal
+ extensibilidad hacia otros ramos
```

La solución debe permitir analizar siniestros de distintos ramos:

```txt
Vehículos
Salud
Hogar
Vida
Generales
```

Pero la demo debe mostrar un caso de uso fuerte y profundo, con reglas específicas, narrativas, relaciones, score explicable y simulación.

---

## 3. Regla principal de trabajo

No se debe trabajar como piezas aisladas sin conexión.

El flujo base debe ser:

```txt
Dataset
   ↓
Features
   ↓
Reglas
   ↓
Modelos
   ↓
Score final
   ↓
Explicación
   ↓
Dashboard
   ↓
Agente
   ↓
Reporte / Demo
```

Cada módulo debe entregar una salida clara para que los demás puedan consumirla.

---

## 4. División principal del equipo

## Jeremy — Arquitectura, scoring, reglas, agente y RAG

Jeremy será responsable del núcleo lógico de RastroSeguro.

### Responsabilidades principales

```txt
Arquitectura general del sistema
Motor de reglas base
Motor de reglas por ramo
Score final
Explicabilidad por siniestro
Herramientas del agente
Router de intención
RAG documental liviano
Simulador de nuevo siniestro
Criterios técnicos para la demo
```

### Módulos a construir

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
src/agent/antifraud_agent.py
```

### Entregables de Jeremy

```txt
Motor de reglas funcionando
Score final 0-100
Clasificación verde / amarillo / rojo
Explicación textual por siniestro
Herramientas internas del agente
Router básico de preguntas
RAG documental sobre reglas y limitaciones
Simulador conectado al pipeline
```

### Resultado esperado de su módulo

Por cada siniestro, el sistema debe poder generar una salida como:

```json
{
  "id_siniestro": "SIN-0045",
  "ramo": "vehiculos",
  "score_final": 87,
  "nivel_riesgo": "Rojo",
  "alertas_activadas": [
    "Siniestro cerca del inicio de póliza",
    "Monto reclamado cercano a suma asegurada",
    "Proveedor recurrente",
    "Narrativa similar"
  ],
  "explicacion": "El caso requiere revisión especializada por acumulación de señales de riesgo.",
  "accion_sugerida": "Escalar a revisión antifraude especializada."
}
```

### Uso de IA para acelerar

Jeremy puede apoyarse en:

```txt
Cursor
Composer 2.0
Codex
ChatGPT
Claude
```

Para:

```txt
Generar funciones de reglas
Refactorizar módulos
Crear tests
Diseñar prompts del agente
Crear herramientas del agente
Documentar arquitectura
Crear ejemplos de preguntas y respuestas
```

---

## Carlos — Dataset, features, modelos y métricas

Carlos será responsable del componente de datos y modelos de machine learning.

### Responsabilidades principales

```txt
Generación de dataset sintético multi-ramo
Validación de columnas
Feature engineering
Entrenamiento del modelo supervisado
Entrenamiento del modelo de anomalías
Evaluación del modelo
Exportación de datasets procesados
Preparación de casos estrella
```

### Módulos a construir

```txt
src/data/generate_synthetic_data.py
src/data/load_data.py
src/data/validate_schema.py

src/features/build_features.py

src/models/train_classifier.py
src/models/train_anomaly.py
src/models/predict.py
```

### Entregables de Carlos

```txt
Dataset sintético multi-ramo
Dataset procesado
Features listas para modelos
Modelo RandomForestClassifier entrenado
Modelo IsolationForest entrenado
Métricas del modelo
Importancia de variables
Modelos guardados con joblib
Casos sintéticos preparados para demo
```

### Dataset mínimo esperado

El dataset debe incluir columnas comunes como:

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
id_proveedor
beneficiario
historial_siniestros_asegurado
etiqueta_fraude_simulada
```

### Variables específicas para vehículos

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

### Distribución sugerida del dataset

```txt
Vehículos: 70%
Hogar: 10%
Salud: 10%
Vida: 5%
Generales: 5%
```

Distribución de riesgo:

```txt
Casos normales: 70%
Casos de riesgo medio: 20%
Casos de riesgo alto: 10%
```

### Modelos a implementar

```txt
RandomForestClassifier
IsolationForest
```

### Métricas a mostrar

```txt
Precision
Recall
F1-score
Matriz de confusión
AUC-ROC
Importancia de variables
```

### Uso de IA para acelerar

Carlos puede apoyarse en IA para:

```txt
Generar datos sintéticos realistas
Crear funciones de feature engineering
Crear notebooks de evaluación
Optimizar modelos
Generar métricas
Crear scripts reproducibles
Detectar errores en pipelines
```

---

## Justin — UI, dashboard, grafo, reportes y presentación visual

Justin será responsable de que la solución sea entendible, demostrable y visualmente fuerte.

### Responsabilidades principales

```txt
Aplicación Next.js
Dashboard ejecutivo
Carga de dataset
Bandeja de revisión
Detalle del siniestro
Vista multi-ramo
Grafo de relaciones
Simulador visual
Chat del agente
Modo jurado
Reporte ejecutivo
README visual
Apoyo en pitch y demo
```

### Módulos a construir

```txt
frontend/

app/pages/dashboard.py
app/pages/upload_dataset.py
app/pages/review_queue.py
app/pages/claim_detail.py
app/pages/multibranch_view.py
app/pages/relationship_graph.py
app/pages/simulator.py
app/pages/agent_chat.py
app/pages/jury_mode.py
app/pages/report.py

src/graph/relationship_graph.py
src/reports/generate_report.py
```

### Entregables de Justin

```txt
App funcional en Next.js
Dashboard ejecutivo
Filtros por ramo, riesgo, ciudad y proveedor
Tabla de siniestros priorizados
Detalle visual de cada siniestro
Grafo de relaciones
Vista multi-ramo
Pantalla del simulador
Pantalla del agente
Modo jurado
Reporte ejecutivo exportable
README con capturas o explicación visual
```

### Dashboard debe mostrar

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

### Gráficos sugeridos

```txt
Distribución de riesgo por ramo
Distribución por nivel de riesgo
Riesgo por ciudad
Riesgo por proveedor
Riesgo por cobertura
Evolución temporal de siniestros
Monto reclamado vs score
```

### Grafo de relaciones

Debe visualizar:

```txt
Asegurado -> Siniestro
Siniestro -> Proveedor
Siniestro -> Beneficiario
Siniestro -> Vehículo
Siniestro -> Ciudad
Siniestro -> Ramo
```

### Modo jurado

Debe tener botones rápidos para:

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

### Uso de IA para acelerar

Justin puede apoyarse en IA para:

```txt
Crear componentes Next.js
Mejorar diseño visual
Crear gráficos con Plotly
Generar grafo con NetworkX o PyVis
Crear layout del dashboard
Crear textos de ayuda en la UI
Crear documentación visual
Preparar guion de demo
```

---

## 5. Contratos entre módulos

Para evitar bloqueos, cada persona debe respetar contratos de entrada y salida.

---

## 5.1 Contrato del dataset

Carlos debe entregar un archivo:

```txt
data/synthetic/siniestros.csv
```

Con columnas mínimas:

```txt
id_siniestro
ramo
cobertura
ciudad
id_proveedor
fecha_ocurrencia
fecha_reporte
monto_reclamado
suma_asegurada
descripcion
documentos_completos
documentos_inconsistentes
etiqueta_fraude_simulada
```

Este archivo será consumido por Jeremy para scoring y por Justin para pruebas iniciales de UI.

---

## 5.2 Contrato del scoring

Jeremy debe entregar un archivo:

```txt
data/processed/siniestros_scored.csv
```

Con columnas mínimas:

```txt
id_siniestro
ramo
cobertura
ciudad
id_proveedor
monto_reclamado
suma_asegurada
score_reglas
score_modelo
score_anomalia
score_nlp
score_grafo
score_categorico
score_final
nivel_riesgo
alertas_activadas
explicacion
accion_sugerida
```

Este archivo será consumido por Justin para el dashboard.

---

## 5.3 Contrato de explicación

La función:

```python
explain_claim(id_siniestro)
```

Debe devolver:

```json
{
  "id_siniestro": "SIN-0045",
  "score_final": 87,
  "nivel_riesgo": "Rojo",
  "alertas": [],
  "explicacion": "",
  "accion_sugerida": "",
  "componentes_score": {
    "reglas": 80,
    "modelo": 90,
    "anomalia": 75,
    "nlp": 85,
    "grafo": 70
  }
}
```

Esta función será usada por:

```txt
Detalle del siniestro
Agente
Reporte ejecutivo
Modo jurado
```

---

## 5.4 Contrato del agente

El agente debe llamar herramientas internas.

Herramientas mínimas:

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

El agente no debe inventar cálculos. Debe consultar funciones del sistema.

---

## 6. Estructura del repositorio

```txt
rastroseguro/
├── README.md
├── requirements.txt
├── .env.example
├── data/
│   ├── raw/
│   ├── processed/
│   └── synthetic/
├── models/
│   ├── fraud_classifier.joblib
│   └── anomaly_detector.joblib
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
│   ├── main.py
│   └── pages/
│       ├── dashboard.py
│       ├── upload_dataset.py
│       ├── review_queue.py
│       ├── claim_detail.py
│       ├── multibranch_view.py
│       ├── relationship_graph.py
│       ├── simulator.py
│       ├── agent_chat.py
│       ├── jury_mode.py
│       └── report.py
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

## 7. Flujo de integración

El proyecto debe poder ejecutarse con comandos claros.

### Generar dataset

```bash
python -m pipelines.data.generate_synthetic_data
```

Salida:

```txt
data/synthetic/siniestros.csv
```

### Entrenar modelos

```bash
python -m pipelines.models.train_classifier
python -m pipelines.models.train_anomaly
```

Salida:

```txt
models/fraud_classifier.joblib
models/anomaly_detector.joblib
```

### Calcular scoring

```bash
python -m src.scoring.final_score
```

Salida:

```txt
data/processed/siniestros_scored.csv
```

### Ejecutar API + frontend

```bash
uvicorn api.main:app --reload --port 8000
cd frontend && npm run dev
```

---

## 8. Orden de implementación recomendado

## Etapa 1 — Base funcional

Objetivo:

```txt
Tener el flujo mínimo funcionando de inicio a fin.
```

Carlos:

```txt
Crear dataset sintético multi-ramo.
Crear columnas mínimas.
Inyectar casos normales, amarillos y rojos.
Exportar CSV.
```

Jeremy:

```txt
Crear reglas base.
Crear reglas vehiculares iniciales.
Calcular score_reglas.
Calcular nivel_riesgo.
Generar explicación textual simple.
```

Justin:

```txt
Crear app Next.js.
Cargar CSV.
Mostrar métricas principales.
Mostrar tabla de siniestros.
Crear filtro por nivel de riesgo.
Crear detalle básico del siniestro.
```

Resultado esperado:

```txt
Dataset -> score -> dashboard -> detalle
```

---

## Etapa 2 — IA real

Objetivo:

```txt
Integrar modelos entrenados al pipeline.
```

Carlos:

```txt
Crear feature engineering.
Entrenar RandomForestClassifier.
Entrenar IsolationForest.
Guardar modelos con joblib.
Exportar métricas.
Calcular score_modelo y score_anomalia.
```

Jeremy:

```txt
Integrar score_modelo.
Integrar score_anomalia.
Definir score_final compuesto.
Mejorar explicaciones por componente.
Crear explain_claim(id_siniestro).
```

Justin:

```txt
Agregar score por componente a la UI.
Agregar gráficos del modelo.
Agregar visualización de métricas.
Mejorar la bandeja de revisión.
```

Resultado esperado:

```txt
El sistema ya usa modelos entrenados y explica el score.
```

---

## Etapa 3 — Diferenciadores técnicos

Objetivo:

```txt
Elevar la solución sobre un dashboard básico.
```

Carlos:

```txt
Mejorar narrativas sintéticas.
Crear casos con descripciones similares.
Ajustar distribución de riesgos.
Preparar casos estrella.
```

Jeremy:

```txt
Implementar NLP con TF-IDF + cosine similarity.
Crear score_nlp.
Crear get_similar_narratives().
Crear primeras herramientas del agente.
```

Justin:

```txt
Crear grafo de relaciones.
Crear ranking de proveedores.
Crear ranking de ciudades.
Crear vista multi-ramo.
Mejorar detalle del siniestro.
```

Resultado esperado:

```txt
NLP + grafo + rankings + vista multi-ramo.
```

---

## Etapa 4 — Agente, RAG y simulador

Objetivo:

```txt
Construir la experiencia inteligente de la demo.
```

Carlos:

```txt
Preparar datos para pruebas de fuego.
Validar casos de demo.
Apoyar simulador con datos de referencia.
Documentar métricas.
```

Jeremy:

```txt
Crear tools.py.
Crear router.py.
Crear antifraud_agent.py.
Crear rag.py.
Implementar RAG documental.
Implementar lógica del simulador.
Crear generate_executive_summary().
```

Justin:

```txt
Crear pantalla del agente.
Crear pantalla del simulador.
Crear modo jurado.
Crear pantalla de reporte ejecutivo.
Mejorar navegación de la app.
```

Resultado esperado:

```txt
Agente con herramientas + RAG documental + simulador + modo jurado.
```

---

## Etapa 5 — Pulido y entrega

Objetivo:

```txt
Dejar la solución estable, presentable y defendible.
```

Carlos:

```txt
Revisar métricas finales.
Limpiar notebooks.
Asegurar reproducibilidad.
Preparar explicación del modelo.
Verificar que los modelos carguen correctamente.
```

Jeremy:

```txt
Probar herramientas del agente.
Revisar explicaciones.
Preparar respuestas técnicas.
Revisar ética y limitaciones.
Validar que el sistema no use lenguaje acusatorio.
```

Justin:

```txt
Pulir UI.
Finalizar README.
Finalizar documentación visual.
Preparar guion de demo.
Validar modo jurado.
Probar instalación desde cero.
```

Resultado esperado:

```txt
Proyecto listo para demo, revisión del jurado y entrega final.
```

---

## 9. Uso de inteligencia artificial para desarrollo

El equipo usará herramientas de IA para acelerar, pero manteniendo revisión humana del código.

Herramientas:

```txt
Cursor
Composer 2.0
Codex
ChatGPT
Claude
```

Uso recomendado:

```txt
Generación inicial de módulos
Refactorización
Tests
Documentación
Creación de datos sintéticos
Depuración de errores
Mejora de prompts
Diseño de UI
Optimización de funciones
Preparación de README
Preparación de pitch
```

Reglas:

```txt
No aceptar código sin revisarlo.
No integrar código que no entiendan.
No subir claves API.
No dejar dependencias innecesarias.
No romper contratos entre módulos.
No cambiar columnas del dataset sin avisar.
```

---

## 10. GitHub y trabajo colaborativo

Ramas sugeridas:

```txt
main
dev
feature/carlos-data-ml
feature/jeremy-scoring-agent
feature/justin-ui-demo
```

Reglas:

```txt
main solo recibe versiones estables.
dev se usa para integración.
Cada persona trabaja en su rama feature.
Los merges se hacen hacia dev.
Antes de mergear, se verifica que la app corra.
```

Checklist antes de integrar:

```txt
¿Corre cd frontend && npm run dev?
¿Carga el dataset?
¿Existe data/processed/siniestros_scored.csv?
¿La tabla principal funciona?
¿El score_final se calcula?
¿No se rompieron las columnas esperadas?
¿No se subieron credenciales?
```

---

## 11. Prioridades del proyecto

## Debe estar sí o sí

```txt
Dataset sintético multi-ramo
Carga de dataset
Motor de reglas
Score final
Semáforo de riesgo
Modelo ML entrenado
Dashboard
Bandeja de revisión
Detalle con explicación
README
Documentación técnica básica
```

## Muy importante para destacar

```txt
Vista multi-ramo
NLP de narrativas similares
Grafo de relaciones
Agente con herramientas
Simulador de nuevo siniestro
Reporte ejecutivo
Modo jurado
```

## Extra si sobra capacidad

```txt
RAG documental liviano
Router de intención entrenado
Feedback humano
SHAP o importancia avanzada de variables
Exportación PDF
API con FastAPI
```

---

## 12. Qué evitar

No invertir tiempo al inicio en:

```txt
Login de usuarios
CRUD administrativo completo
Django
Base de datos compleja
Diseño visual demasiado personalizado
Fine-tuning de LLM
LangChain complejo
Features que no entren en la demo
```

La prioridad es:

```txt
Funcionalidad
Explicabilidad
Demo
Estabilidad
Diferenciación
```

---

## 13. Criterio para tomar decisiones

Una funcionalidad se implementa si ayuda a una de estas cosas:

```txt
Mejora la demo.
Mejora la explicación.
Mejora el uso real de IA.
Mejora la trazabilidad.
Mejora la diferenciación.
Mejora la defensa ante el jurado.
```

Si no ayuda a eso, se deja para después.

---

## 14. Casos estrella de demo

Preparar casos específicos para no improvisar.

### Caso 1: rojo evidente

```txt
Siniestro con monto alto.
Reporte tardío.
Documentos inconsistentes.
Proveedor recurrente.
Score alto.
```

### Caso 2: rojo no evidente

```txt
Pocas reglas activadas.
Modelo de anomalías lo detecta.
Grafo muestra proveedor conectado a varios casos rojos.
Narrativa similar a otros reclamos.
```

### Caso 3: amarillo ético

```txt
Tiene señales de riesgo.
No es suficiente para escalar a rojo.
Sistema recomienda revisión documental.
```

### Caso 4: comparación multi-ramo

```txt
Dashboard muestra riesgo por ramo.
Se comparan vehículos, salud, hogar, vida y generales.
Se identifica el ramo con más concentración de alertas.
```

### Caso 5: simulación en vivo

```txt
Se ingresa un siniestro nuevo.
El sistema calcula score.
Explica reglas activadas.
Muestra casos similares.
Sugiere acción.
```

---

## 15. Mensaje técnico que todos deben poder defender

Todos los integrantes deben poder explicar esto:

> RastroSeguro es una plataforma multi-ramo de priorización antifraude. Carga siniestros, calcula un score de riesgo, clasifica los casos por semáforo y explica las alertas. Combina reglas de negocio, machine learning supervisado, detección de anomalías, NLP de narrativas, grafo de relaciones y un agente conectado a herramientas. La IA no acusa fraude ni toma decisiones automáticas; solo prioriza casos para revisión humana.

---

## 16. Mensaje sobre el agente

El agente debe defenderse así:

> El agente no responde únicamente con prompts. Usa herramientas internas conectadas al pipeline de datos, modelos y scoring. Para preguntas sobre documentación, reglas y limitaciones puede usar RAG documental. Para rankings, explicaciones y datos tabulares llama funciones reales del sistema.

---

## 17. Mensaje sobre RAG

> RAG se usa para documentación y contexto del proyecto, no para calcular resultados tabulares. Los cálculos sobre siniestros se hacen con funciones verificables.

---

## 18. Mensaje sobre fine-tuning

> No se usará fine-tuning del LLM como base porque el objetivo no es memorizar casos, sino consultar datos trazables y auditables. El entrenamiento principal está en los modelos de riesgo y anomalías. Si hay capacidad, se puede entrenar un router de intención ligero para el agente.

---

## 19. Resultado final esperado

Al final, el proyecto debe tener:

```txt
Aplicación funcional
Dataset sintético multi-ramo
Pipeline de scoring
Modelo ML entrenado
Detector de anomalías
NLP para narrativas
Grafo de relaciones
Agente con herramientas
RAG documental
Simulador de nuevo siniestro
Modo jurado
Reporte ejecutivo
README claro
Documentación técnica
Pitch preparado
```

---

## 20. Resumen ejecutivo de organización

```txt
Carlos:
  Datos, features, modelos ML, anomalías y métricas.

Jeremy:
  Arquitectura, reglas, scoring, explicabilidad, agente, RAG y simulador.

Justin:
  UI, dashboard, grafo, reportes, modo jurado, README y demo visual.
```

La prioridad del equipo es construir primero una base funcional y luego mejorarla con IA, explicabilidad, visualización y agente consultivo.
