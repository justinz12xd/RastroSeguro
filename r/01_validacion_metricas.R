#!/usr/bin/env Rscript
# Validación reproducible de métricas — RastroSeguro (PDF §16)
suppressPackageStartupMessages({
  library(jsonlite)
  library(readr)
})

root <- normalizePath(getwd())
if (!file.exists(file.path(root, "reports", "model_metrics.json"))) {
  root <- normalizePath(file.path(getwd(), ".."))
}

metrics_path <- file.path(root, "reports", "model_metrics.json")
scored_path <- file.path(root, "data", "processed", "siniestros_scored.csv")

cat("=== RastroSeguro — Validación R ===\n\n")

if (file.exists(metrics_path)) {
  metrics <- fromJSON(metrics_path)
  cat("Clasificador F1:", metrics$fraud_classifier$f1, "\n")
  cat("Clasificador AUC:", metrics$fraud_classifier$auc, "\n")
  cat("Tasa anomalías:", metrics$anomaly_detector$anomaly_rate, "\n")
} else {
  cat("WARN: missing", metrics_path, "\n")
}

if (file.exists(scored_path)) {
  df <- read_csv(scored_path, show_col_types = FALSE)
  cat("\nSemáforo de riesgo:\n")
  print(table(df$nivel_riesgo))
  cat("\nScore final — resumen:\n")
  print(summary(df$score_final))
  if ("score_anomalia" %in% names(df) && "etiqueta_fraude_simulada" %in% names(df)) {
    red <- df[df$nivel_riesgo == "Rojo", ]
    cat("\nCasos rojos:", nrow(red), "\n")
    cat("Monto expuesto rojos:", sum(red$monto_reclamado, na.rm = TRUE), "\n")
  }
} else {
  cat("WARN: missing", scored_path, "\n")
}

cat("\nValidación R completada.\n")
