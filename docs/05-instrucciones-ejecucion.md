# Instrucciones de ejecución

Este documento define el camino esperado para correr RastroSeguro de punta a punta.

## Instalación

```bash
pip install -r requirements.txt
```

## Flujo completo esperado

### 0. Inventariar fuentes públicas Ecuador (opcional)

```bash
python -m pipelines.ingestion.scrape_ecuador --year-start 2021 --year-end 2026
```

Salidas: `data/ecuador/inventario_manifest.json`, `data/ecuador/inventario_links.tsv`.  
Ver [inventario-fuentes-ecuador.md](./inventario-fuentes-ecuador.md).

### 0.1 Modelar dataset curado para base de datos (opcional)

```bash
py -3 -m pipelines.ingestion.model_curated_dataset --skip-ecu911-agg
```

Ver guía de despliegue: [06-modelado-dataset-supabase.md](./06-modelado-dataset-supabase.md).

### 1. Generar dataset sintético

```bash
python -m pipelines.data.generate_synthetic_data
```

Salida esperada:

```txt
data/synthetic/siniestros.csv
```

### 2. Entrenar modelos

```bash
python -m pipelines.models.train_classifier
python -m pipelines.models.train_anomaly
```

Salidas esperadas:

```txt
models/fraud_classifier.joblib
models/anomaly_detector.joblib
```

### 3. Calcular scoring

```bash
python -m src.scoring.final_score
```

Salida esperada:

```txt
data/processed/siniestros_scored.csv
```

### 4. Ejecutar API + frontend Next.js

```bash
uvicorn api.main:app --reload --port 8000
cd frontend && npm run dev
```

## Verificación rápida

Antes de integrar cambios, confirmar:

- [ ] Existe `data/synthetic/siniestros.csv`.
- [ ] Existe `data/processed/siniestros_scored.csv`.
- [ ] `score_final` está entre 0 y 100.
- [ ] `nivel_riesgo` contiene Verde, Amarillo o Rojo.
- [ ] Las alertas son explicables.
- [ ] El frontend Next.js carga sin errores.
- [ ] No se subieron credenciales ni datos reales.


## Puente API para Next.js

Instalar dependencias con uv:

```bash
uv venv
uv pip install -r requirements.txt
```

Ejecutar API:

```bash
uv run uvicorn api.main:app --reload --port 8000
```

Validar:

```bash
curl http://localhost:8000/api/health
```

El frontend Next.js debe usar:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```
