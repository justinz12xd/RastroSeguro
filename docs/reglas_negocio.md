# Reglas de negocio — Reto Aseguradora del Sur

Matriz de trazabilidad entre reglas del PDF, códigos internos y señales.

## Reglas críticas PDF (RF)

| PDF | Código | Severidad | Descripción |
|---|---|---|---|
| RF-01 | RF-01 | Rojo | Robo con monto cercano a suma asegurada (pérdida total) |
| RF-02 | RF-02 | Rojo | Documentos inconsistentes / posible falsificación |
| RF-03 | RF-03 / RB-012 | Rojo | Coincidencia con lista restrictiva SERCOP |
| RF-04 | RF-04 | Rojo | Dinámica del accidente físicamente improbable |
| RF-05 | RF-05 | Amarillo | Siniestro <48h desde inicio de póliza |
| RF-06 | RF-06 | Amarillo | Demora atípica en denuncia de robo (>4 días) |
| RF-07 | RF-07 | Amarillo | Narrativa clonada o muy similar |

## Reglas base (RB)

| Código | Señal PDF | Puntos |
|---|---|---|
| RB-001 | Borde inicio vigencia | 4–12 |
| RB-002 | Borde fin vigencia | 4–10 |
| RB-003 | Reporte tardío | 3–5 |
| RB-004 | Monto ≥95% suma asegurada | 7 |
| RB-005 | Monto ≥80% suma asegurada | 4 |
| RB-006 | Documentos incompletos | 4 |
| RB-007 | *(delegado a RF-02)* Documentos inconsistentes | — |
| RB-008 | Alta frecuencia asegurado | 8 |
| RB-009 | Frecuencia moderada asegurado | 4 |
| RB-010 | Proveedor recurrente | 6 |
| RB-011 | Beneficiario recurrente | 6 |
| RB-012 | Lista restrictiva SERCOP | 10 |

## Reglas vehículos (RV)

| Código | Señal PDF | Puntos |
|---|---|---|
| RV-001 | Robo cercano al inicio | 10 |
| RV-005 | Sin tercero identificado | 5 |
| RV-006 | Conductor recurrente | 8 |
| RV-008 | Frecuencia solo RC | 6 |
| RV-009 | Demora denuncia robo (>48h / 24–48h) | 4–8 |
| RV-010 | Volcadura vs relato contradictorio | 6 |
| RV-011 | Accidente múltiple nocturno | 3 |

## Semáforo de riesgo

| Rango | Nivel | Acción |
|---|---|---|
| 0–40 | Verde | Flujo normal |
| 41–75 | Amarillo | Revisión documental |
| 76–100 | Rojo | Revisión antifraude especializada |

Implementación: [`src/utils/risk_levels.py`](../src/utils/risk_levels.py)

## Guardrail ético

Toda alerta usa lenguaje de **posible fraude** o **requiere revisión**. No hay rechazo automático ni acusación.
