# 3. Dataset

Datos **sintéticos** generados para la prueba + datos **públicos** de Ecuador como contexto de riesgo de proveedores.

## Archivos en esta carpeta

| Archivo | Descripción |
|---------|-------------|
| `siniestros.csv` | 25 000 siniestros multi-ramo con etiqueta de fraude simulada |
| `polizas.csv` | Pólizas vinculadas |
| `asegurados.csv` | Asegurados |
| `proveedores.csv` | Proveedores / talleres |
| `documentos.csv` | Documentos adjuntos |
| `siniestros_qa.json` | Métricas de calidad del dataset |
| `dataset_manifest.json` | Manifiesto y metadatos |
| `ecuador/` | Datos públicos curados (SERCOP, OCDS, señales proveedor) |

## Regenerar

```bash
py -3 -m pipelines.data.generate_synthetic_data
py -3 -m src.scoring.final_score
```

## Fuentes públicas Ecuador

| Fuente | Archivo |
|--------|---------|
| SERCOP sanciones | `ecuador/sercop_sanciones_curated.csv` |
| OCDS contratos | `ecuador/ocds_contratos_curated.csv` |
| Señales proveedor | `ecuador/supplier_risk_features.csv` |

Inventario: [`../../docs/inventario-fuentes-ecuador.md`](../../docs/inventario-fuentes-ecuador.md)

## Nota

Todos los datos son sintéticos o de fuentes públicas. No contiene información real de asegurados ni credenciales.
