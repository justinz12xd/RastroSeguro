# Modelo de datos — RastroSeguro

## Tabla principal: siniestros

Archivo: `data/synthetic/siniestros.csv`

Campos mínimos PDF §6.1 + extensiones vehiculares y Ecuador.

| Campo | Tipo | Origen |
|---|---|---|
| id_siniestro | PK | Sintético |
| id_poliza | FK → polizas | Sintético |
| id_asegurado | FK → asegurados | Sintético |
| monto_pagado, estado, sucursal | PDF §6.1 | agent_ready |
| placa_hash, chasis_hash, motor_hash | Vehículo anonimizado | Generado |
| supplier_ruc, lista_restrictiva_sercop | Ecuador SERCOP/OCDS | Curación pública |

## Tablas complementarias PDF §6.2

| Tabla | Archivo | Relación |
|---|---|---|
| Pólizas | `data/synthetic/polizas.csv` | 1:N siniestros |
| Asegurados | `data/synthetic/asegurados.csv` | 1:N siniestros |
| Proveedores | `data/synthetic/proveedores.csv` | 1:N siniestros |
| Documentos | `data/synthetic/documentos.csv` | N:1 siniestros |

Manifest: `data/synthetic/dataset_manifest.json`

## Scoring

Archivo: `data/processed/siniestros_scored.csv`

Incluye componentes `score_reglas`, `score_modelo`, `score_anomalia`, `score_nlp`, `score_grafo`, `score_final`, `nivel_riesgo`.

## Esquemas SQL de referencia

- [`db/supabase/schema_agent_ready.sql`](../db/supabase/schema_agent_ready.sql)
- [`db/supabase/schema_curated.sql`](../db/supabase/schema_curated.sql)

El prototipo usa archivos planos CSV; los esquemas SQL documentan migración futura.
