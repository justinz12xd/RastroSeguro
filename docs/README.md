# Documentación — RastroSeguro

Índice de documentación para coordinar el trabajo del equipo y preparar la entrega del **hackIAthon 2026 — Reto Aseguradora del Sur**.

> **¿Qué es el proyecto?** Lee el [README principal](../README.md) o el [pitch](../presentation/RastroSeguro-Pitch.md).  
> **¿Cómo instalar, desplegar y operar?** Lee la [guía técnica](./guia-tecnica.md).

## Lectura rápida por rol

| Rol | Leer primero | Objetivo |
|---|---|---|
| Todos | [01-guia-general-equipo.md](./01-guia-general-equipo.md) | Alinear alcance, prioridades y reglas de trabajo |
| Todos | [02-contratos-integracion.md](./02-contratos-integracion.md) | Evitar romper columnas, rutas y funciones compartidas |
| Carlos | [equipo/carlos-datos-modelos.md](./equipo/carlos-datos-modelos.md) | Dataset, features, modelos y métricas |
| Jeremy | [equipo/jeremy-scoring-agente.md](./equipo/jeremy-scoring-agente.md) | Reglas, scoring, explicabilidad, agente y simulador |
| Justin | [equipo/justin-nextjs-puente-api.md](./equipo/justin-nextjs-puente-api.md) | Next.js, vistas, demo y consumo de API |

## Documentos de coordinación

| Archivo | Para qué sirve |
|---|---|
| [guia-tecnica.md](./guia-tecnica.md) | Instalación, arquitectura, variables, deploy, tests |
| [01-guia-general-equipo.md](./01-guia-general-equipo.md) | Resumen operativo para trabajar en paralelo |
| [02-contratos-integracion.md](./02-contratos-integracion.md) | Contratos de dataset, scoring, explicación, agente y simulador |
| [03-arquitectura-pipeline.md](./03-arquitectura-pipeline.md) | Arquitectura técnica y flujo de datos |
| [04-demo-y-vistas.md](./04-demo-y-vistas.md) | Organización de la app en menos páginas con tabs internas |
| [05-instrucciones-ejecucion.md](./05-instrucciones-ejecucion.md) | Comandos esperados para correr el proyecto |
| [06-plan-jeremy-cerebro-antifraude.md](./06-plan-jeremy-cerebro-antifraude.md) | Plan del núcleo de reglas, scoring y agente de Jeremy |

## Documentos por integrante

| Integrante | Documento |
|---|---|
| Carlos | [equipo/carlos-datos-modelos.md](./equipo/carlos-datos-modelos.md) |
| Jeremy | [equipo/jeremy-scoring-agente.md](./equipo/jeremy-scoring-agente.md) |
| Justin | [equipo/justin-nextjs-puente-api.md](./equipo/justin-nextjs-puente-api.md) |

## Documentos base del proyecto

Estos documentos mantienen el contexto original y estratégico:

| Archivo | Descripción |
|---|---|
| [reto-aseguradora-del-sur.md](./reto-aseguradora-del-sur.md) | Especificación del reto, entregables y criterios de evaluación |
| [planteamiento-tecnico-rastoseguro.md](./planteamiento-tecnico-rastoseguro.md) | Concepto técnico y diferenciadores de RastroSeguro |
| [organizacion-equipo.md](./organizacion-equipo.md) | Organización original del equipo y plan de trabajo |
| [inventario-fuentes-ecuador.md](./inventario-fuentes-ecuador.md) | Fuentes públicas EC (CKAN, INEC, SERCOP) y script de inventario |

## Decisión actual de alcance

```txt
Funcionalidades avanzadas: sí.
Demasiadas vistas independientes: no.
```

La app debe destacar con scoring explicable, IA, relaciones, agente y simulador, pero agrupado en pocas secciones fuertes:

```txt
Dashboard
Revisión de siniestros
Inteligencia antifraude
Agente y simulador
Reporte / demo
```

> No usaremos “modo jurado” como módulo formal de producto. La necesidad de demo se cubre con casos estrella y reporte/demo ejecutivo.
