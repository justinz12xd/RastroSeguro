# Guía general del equipo — RastroSeguro

Este documento alinea a Carlos, Jeremy y Justin para trabajar en paralelo sin romper contratos de integración.

## Decisión de producto

RastroSeguro será una solución avanzada, pero ordenada:

```txt
Funcionalidades avanzadas: sí.
Demasiadas pantallas independientes: no.
```

La app debe demostrar IA explicable, análisis de riesgo, relaciones y agente, pero agrupado en pocas secciones fuertes.

## Principio central

> RastroSeguro no acusa fraude ni rechaza reclamos. Prioriza siniestros con señales de posible fraude para revisión humana.

## Prioridad del equipo

1. Dataset sintético multi-ramo.
2. Reglas y score explicable.
3. Modelos de IA y anomalías.
4. Dashboard y bandeja de revisión.
5. NLP, relaciones, agente y simulador.
6. Reporte, casos estrella y demo final.

## Responsabilidades

| Persona | Responsabilidad | Entrega principal |
|---|---|---|
| Carlos | Datos, features, modelos y métricas | Dataset, modelos y métricas |
| Jeremy | Reglas, scoring, explicación, agente y simulador | `siniestros_scored.csv` y funciones analíticas |
| Justin | Next.js, visualización, demo y reporte | App funcional y demo clara |

## Reglas para trabajar en paralelo

- No cambiar nombres de columnas sin avisar.
- No cambiar rutas de archivos contratadas sin actualizar `docs/02-contratos-integracion.md`.
- Cada módulo debe tener una salida clara para los demás.
- Primero integrar el flujo completo, luego pulir.
- Las funciones del agente no deben inventar cálculos: deben consultar herramientas reales.
- La UI puede agrupar funcionalidades en tabs; no todo requiere una página separada.

## Flujo objetivo

```txt
Dataset de Carlos
   ↓
Reglas + modelos + scoring de Jeremy
   ↓
Dashboard + revisión + demo de Justin
```

## Qué evitar

- Crear muchas vistas sin datos reales detrás.
- Hacer un chatbot que responda solo con prompts.
- Hacer reglas aisladas que no generen explicación.
- Cambiar contratos de integración en silencio.
- Usar lenguaje acusatorio como “fraude confirmado” salvo en feedback humano explícito.
