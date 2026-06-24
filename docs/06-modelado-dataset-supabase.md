# Modelado de dataset para Supabase

Este flujo deja la data lista para despliegue sin cargar CSV crudos gigantes.

## 1) Generar dataset curado

Desde la raíz del repo:

```bash
py -3 -m pipelines.ingestion.model_curated_dataset --skip-ecu911-agg
```

Salida esperada en `data/curated/ecuador/`:

- `sercop_sanciones_curated.csv`
- `ocds_contratos_curated.csv`
- `supplier_risk_features.csv`
- `inec_dataset_agg.csv`
- `inec_column_profile.csv`
- `inec_records_sample.csv`
- `curation_summary.json`

Si quieres incluir agregados de ECU911:

```bash
py -3 -m pipelines.ingestion.model_curated_dataset
```

Genera adicionalmente `ecu911_monthly_agg.csv`.

## 2) Crear tablas en Supabase

En SQL Editor de Supabase, ejecutar:

- `db/supabase/schema_curated.sql`

Esto crea tablas, índices y políticas RLS de solo lectura para `anon` y `authenticated`.

## 3) Cargar CSVs

Opciones:

1. **Table Editor (rápido)**: Import Data from CSV (útil para archivos pequeños/medianos).
2. **Carga masiva**: usar `COPY`/`psql` para archivos grandes.

> En dashboard, la importación CSV tiene límite de tamaño por archivo (documentación actual: 100MB).  
> Si un archivo supera eso, dividirlo o usar `COPY`.

Orden recomendado de carga:

1. `sercop_sanciones_curated.csv` -> `public.sercop_sanctions`
2. `ocds_contratos_curated.csv` -> `public.ocds_contracts`
3. `supplier_risk_features.csv` -> `public.supplier_risk_features`
4. `inec_dataset_agg.csv` -> `public.inec_dataset_agg`
5. `inec_column_profile.csv` -> `public.inec_column_profile`
6. `inec_records_sample.csv` -> `public.inec_records_sample`
7. `ecu911_monthly_agg.csv` -> `public.ecu911_monthly_agg` (opcional)

## 4) Qué NO subir a Supabase

- `data/raw/ecuador/inec_siniestros_2021_2026.csv` (muy grande para carga directa)
- crudos completos que no uses en consultas en línea

Para esos, mantener **cold storage** (disco/S3/Drive) y subir solo agregados necesarios.

## 5) Dataset canónico para agente (súper completo)

Generar paquete para agente con siniestros + contexto proveedor + chunks para RAG:

```bash
py -3 -m pipelines.ingestion.build_agent_ready_dataset --rows 25000
```

Salidas en `data/processed/agent_ready/`:

- `siniestros_canonico.csv`
- `proveedores_contexto.csv`
- `rag_chunks_siniestros.jsonl`
- `qa_agent_ready.json`

Esquema SQL para Supabase:

- `db/supabase/schema_agent_ready.sql`
