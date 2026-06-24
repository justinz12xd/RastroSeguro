# 2. Código fuente

El código completo está en la **raíz del repositorio**. Este directorio documenta la estructura y cómo navegarla.

## README principal

Ver [`../../README.md`](../../README.md) — instalación, arquitectura, validación y demo.

## Estructura

```txt
RastroSeguro_hackIAthon/
├── api/           # FastAPI (endpoints REST)
├── frontend/      # Dashboard Next.js
├── src/           # Scoring, reglas, ML, NLP, agente, reportes
├── pipelines/     # Generación de datos, entrenamiento, validación
├── data/          # Datasets sintéticos y curados
├── notebooks/     # Notebooks ejecutables
├── models/        # Artefactos ML (.joblib)
├── tests/         # Tests unitarios
├── docs/          # Documentación técnica
└── presentation/  # Pitch ejecutivo (fuente Markdown)
```

## Documentación técnica

| Documento | Ruta |
|-----------|------|
| Arquitectura | `docs/arquitectura.md` |
| Uso de IA | `docs/uso_ia.md` |
| Reglas de negocio | `docs/reglas_negocio.md` |
| Modelo de datos | `docs/modelo_datos.md` |
| Limitaciones | `docs/limitaciones.md` |
| Instrucciones ejecución | `docs/05-instrucciones-ejecucion.md` |

## Tests

```bash
py -3 -m unittest discover -s tests -p "test_*.py"
py -3 -m pipelines.models.validate_deliverables
```
