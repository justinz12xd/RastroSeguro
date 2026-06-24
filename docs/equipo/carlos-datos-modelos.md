# Carlos — Datos, features y modelos

Carlos construye la base de datos y los modelos que alimentan el scoring de Jeremy y la visualización de Justin.

## Objetivo

Entregar datos sintéticos realistas, features listas para modelar y modelos entrenados que aporten señales de riesgo.

## Responsabilidades

- Generar dataset sintético multi-ramo.
- Inyectar casos normales, amarillos y rojos.
- Crear features para modelos.
- Entrenar `RandomForestClassifier`.
- Entrenar `IsolationForest`.
- Exportar métricas.
- Preparar casos estrella para demo.

## Entregas

```txt
data/synthetic/siniestros.csv
models/fraud_classifier.joblib
models/anomaly_detector.joblib
```

Opcional:

```txt
data/processed/features.csv
reports/model_metrics.json
```

## Columnas críticas para no romper integración

Revisar `docs/02-contratos-integracion.md` antes de cambiar columnas.

Mínimas:

```txt
id_siniestro, id_poliza, id_asegurado, ramo, cobertura, ciudad,
id_proveedor, beneficiario, fecha_inicio_poliza, fecha_fin_poliza,
fecha_ocurrencia, fecha_reporte, monto_reclamado, monto_estimado,
suma_asegurada, descripcion, documentos_completos,
documentos_inconsistentes, historial_siniestros_asegurado,
etiqueta_fraude_simulada
```

## Relación con Jeremy

Jeremy consume tu dataset y modelos para calcular:

- `score_modelo`.
- `score_anomalia`.
- `score_final`.
- Explicaciones.

## Relación con Justin

Justin usa tus datos y métricas para:

- Dashboard.
- Métricas del modelo.
- Distribuciones por ramo.
- Casos estrella.

## Prioridad

Primero entregar un CSV estable. Después mejorar realismo, métricas y modelos.


## Formato recomendado para modelos

Para que Jeremy integre tus modelos sin fricción, guarda los artefactos así:

```python
joblib.dump({
    "model": trained_model,
    "feature_columns": feature_columns,
    "metrics": metrics,
}, "models/fraud_classifier.joblib")
```

Y para anomalías:

```python
joblib.dump({
    "model": anomaly_model,
    "feature_columns": feature_columns,
    "metrics": metrics,
}, "models/anomaly_detector.joblib")
```

Rutas esperadas por Jeremy:

```txt
models/fraud_classifier.joblib
models/anomaly_detector.joblib
```

Si todavía no están listos, el pipeline de Jeremy usa score neutro y no se rompe.
