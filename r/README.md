# Análisis R — RastroSeguro

Scripts de validación reproducible para el jurado (PDF §16). **No integrados en runtime Python.**

## Requisitos

- R >= 4.2
- Paquetes: `jsonlite`, `readr`, `dplyr`, `ggplot2`, `knitr`, `rmarkdown`

## Setup con renv (recomendado)

```r
install.packages("renv")
renv::init()
renv::install(c("jsonlite", "readr", "dplyr", "ggplot2", "knitr", "rmarkdown"))
renv::snapshot()
```

## Ejecución

```bash
Rscript r/01_validacion_metricas.R
```

Render notebook:

```bash
Rscript -e "rmarkdown::render('r/02_exploracion_siniestros.Rmd')"
```

## Salida esperada

- Resumen semáforo Verde/Amarillo/Rojo
- Métricas F1/AUC desde `reports/model_metrics.json`
- Gráficos de concentración por proveedor y ramo
