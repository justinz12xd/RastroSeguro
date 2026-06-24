# Arquitectura y pipeline

RastroSeguro usa un enfoque híbrido: reglas auditables, modelos de IA, anomalías, NLP, relaciones y explicación final.

## Flujo completo

```txt
Dataset sintético
   ↓
Validación de esquema
   ↓
Feature engineering
   ↓
Reglas base + reglas por ramo
   ↓
Modelo supervisado
   ↓
Detector de anomalías
   ↓
NLP de narrativas similares
   ↓
Análisis de relaciones/grafo
   ↓
Score final compuesto
   ↓
Explicación por siniestro
   ↓
Dashboard + agente + simulador + reporte
```

## Módulos esperados

```txt
src/data/          Dataset, carga y validación
src/features/      Variables para modelos y scoring
src/models/        Entrenamiento y predicción
src/rules/         Reglas auditables
src/nlp/           Similitud de narrativas
src/graph/         Relaciones entre entidades
src/scoring/       Score final
src/explainability/ Explicaciones
src/agent/         Herramientas, router y RAG
src/reports/       Reporte ejecutivo
frontend/          Next.js
```

## Decisión de UI

La app no necesita demasiadas páginas. Debe agrupar funcionalidades avanzadas en secciones fuertes:

```txt
1. Dashboard
2. Revisión de siniestros
3. Inteligencia antifraude
4. Agente y simulador
5. Reporte / demo
```

## Principios técnicos

- Cada módulo debe poder probarse por separado.
- El score final debe ser trazable.
- Las explicaciones deben mencionar señales concretas.
- El agente debe llamar herramientas reales.
- RAG se usa para documentación, no para calcular rankings tabulares.
