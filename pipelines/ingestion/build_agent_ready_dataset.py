from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"

MOCK_PATH = DATA_DIR / "synthetic" / "mock_siniestros_scored.csv"
SUPPLIER_FEATURES_PATH = DATA_DIR / "curated" / "ecuador" / "supplier_risk_features.csv"
OUT_DIR_DEFAULT = DATA_DIR / "processed" / "agent_ready"

CITY_TO_PROVINCE = {
    "Quito": "PICHINCHA",
    "Guayaquil": "GUAYAS",
    "Cuenca": "AZUAY",
    "Manta": "MANABI",
}

CANONICAL_FIELDS = [
    "id_siniestro",
    "id_poliza",
    "id_asegurado",
    "ramo",
    "cobertura",
    "fecha_ocurrencia",
    "fecha_reporte",
    "monto_reclamado",
    "monto_estimado",
    "monto_pagado",
    "estado",
    "sucursal",
    "descripcion",
    "documentos_completos",
    "beneficiario",
    "dias_desde_inicio_poliza",
    "dias_desde_fin_poliza",
    "dias_entre_ocurrencia_reporte",
    "historial_siniestros_asegurado",
    "etiqueta_fraude_simulada",
    "supplier_ruc",
    "supplier_risk_signal_score",
    "supplier_risk_band",
    "score_final",
    "nivel_riesgo",
    "alertas_activadas",
    "explicacion",
    "accion_sugerida",
]


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def _as_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(str(v))
    except Exception:
        return default


def _as_int(v: Any, default: int = 0) -> int:
    try:
        return int(float(str(v)))
    except Exception:
        return default


def _pick_state(rng: random.Random, nivel: str) -> str:
    if nivel.lower() == "rojo":
        return rng.choice(["Reserva", "Pago Parcial", "Anticipo"])
    if nivel.lower() == "amarillo":
        return rng.choice(["Reserva", "Pago Parcial", "Liquidado"])
    return rng.choice(["Liquidado", "Pago Total", "Cierre Sin Consecuencia"])


def _infer_alerts(
    monto_ratio: float,
    dias_reporte: int,
    historial: int,
    supplier_band: str,
    supplier_score: float,
    docs_ok: str,
) -> list[str]:
    alerts: list[str] = []
    if monto_ratio >= 0.9:
        alerts.append("Monto alto")
    if dias_reporte >= 15:
        alerts.append("Reporte tardío")
    if historial >= 3:
        alerts.append("Reclamos recurrentes")
    if supplier_band == "rojo" or supplier_score >= 70:
        alerts.append("Proveedor observado")
    if docs_ok == "No":
        alerts.append("Documentos incompletos")
    if not alerts:
        alerts.append("Sin señales críticas")
    return alerts


def _build_explanation(alerts: list[str], supplier_band: str, monto_ratio: float) -> str:
    parts = [f"Señales detectadas: {', '.join(alerts)}."]
    parts.append(f"Riesgo proveedor: {supplier_band}.")
    parts.append(f"Monto reclamado respecto al estimado: {monto_ratio:.2f}.")
    return " ".join(parts)


def _risk_label(score_final: float) -> str:
    if score_final >= 75:
        return "Rojo"
    if score_final >= 45:
        return "Amarillo"
    return "Verde"


def _action_for_label(label: str) -> str:
    if label == "Rojo":
        return "Escalar a revisión antifraude especializada."
    if label == "Amarillo":
        return "Revisión documental y validación de consistencia."
    return "Continuar flujo normal."


def _normalize_supplier_band(v: str) -> str:
    low = str(v or "").strip().lower()
    if low in {"rojo", "amarillo", "verde"}:
        return low
    return "verde"


def build_agent_ready_siniestros(target_rows: int, seed: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    rng = random.Random(seed)
    mock_rows = _load_csv(MOCK_PATH)
    supplier_rows = _load_csv(SUPPLIER_FEATURES_PATH)
    if not mock_rows:
        raise RuntimeError("No se encontraron filas en mock_siniestros_scored.csv")
    if not supplier_rows:
        raise RuntimeError("No se encontraron filas en supplier_risk_features.csv")

    suppliers = []
    for r in supplier_rows:
        suppliers.append(
            {
                "supplier_ruc": r.get("supplier_ruc", ""),
                "supplier_risk_signal_score": _as_float(r.get("risk_signal_score"), 0.0),
                "supplier_risk_band": _normalize_supplier_band(r.get("risk_band", "verde")),
                "sanciones_total": _as_int(r.get("sanciones_total"), 0),
                "contratos_total": _as_int(r.get("contratos_total"), 0),
            }
        )
    # sesgo: más probabilidad de seleccionar proveedores con mayor score
    weights = [max(1.0, s["supplier_risk_signal_score"] / 10.0) for s in suppliers]

    start_date = date(2019, 1, 1)
    end_date = date(2026, 12, 31)
    total_days = (end_date - start_date).days

    out_rows: list[dict[str, Any]] = []
    provider_master: dict[str, dict[str, Any]] = {}
    risk_counter = Counter()

    for i in range(1, target_rows + 1):
        base = mock_rows[(i - 1) % len(mock_rows)]
        supplier = rng.choices(suppliers, weights=weights, k=1)[0]

        # fecha ocurrencia y reporte
        fecha_oc = start_date + timedelta(days=rng.randint(0, total_days))
        dias_reporte = max(0, int(rng.gauss(5, 6)))
        fecha_rep = fecha_oc + timedelta(days=dias_reporte)

        # montos (variaciones sobre plantilla)
        base_reclamado = _as_float(base.get("monto_reclamado"), 1000.0)
        base_suma = max(_as_float(base.get("suma_asegurada"), base_reclamado * 1.3), base_reclamado + 100)
        factor = max(0.35, min(1.35, rng.gauss(1.0, 0.22)))
        monto_reclamado = round(base_reclamado * factor, 2)
        monto_estimado = round(monto_reclamado * rng.uniform(0.75, 1.05), 2)
        monto_pagado = round(monto_estimado * rng.uniform(0.0, 1.0), 2)

        # días respecto a póliza
        dias_ini = rng.randint(0, 365)
        dias_fin = rng.randint(-60, 365)
        historial = max(0, int(rng.gauss(1.2, 1.4)))

        # score final combinado
        base_score = _as_float(base.get("score_final"), 45.0)
        supplier_boost = supplier["supplier_risk_signal_score"] * 0.35
        behavior_boost = (15 if dias_reporte >= 15 else 0) + (10 if monto_reclamado >= 0.9 * base_suma else 0) + (8 if historial >= 3 else 0)
        jitter = rng.uniform(-8, 8)
        score_final = max(0.0, min(100.0, base_score * 0.55 + supplier_boost + behavior_boost + jitter))
        label = _risk_label(score_final)
        risk_counter[label] += 1

        docs_threshold = 0.35 if label == "Rojo" else 0.12
        docs_ok = "No" if rng.random() < docs_threshold else "Sí"
        alerts = _infer_alerts(
            monto_ratio=(monto_reclamado / max(monto_estimado, 1)),
            dias_reporte=dias_reporte,
            historial=historial,
            supplier_band=supplier["supplier_risk_band"],
            supplier_score=supplier["supplier_risk_signal_score"],
            docs_ok=docs_ok,
        )
        explicacion = _build_explanation(alerts, supplier["supplier_risk_band"], monto_reclamado / max(monto_estimado, 1))

        ciudad = base.get("ciudad", "Quito")
        provincia = CITY_TO_PROVINCE.get(ciudad, "PICHINCHA")

        id_siniestro = f"SIN-{i:06d}"
        id_poliza = f"POL-{rng.randint(1, max(1500, target_rows // 4)):05d}"
        id_asegurado = f"ASEG-{rng.randint(1, max(3000, target_rows // 2)):06d}"

        if label == "Rojo":
            etiqueta_fraude_simulada = 1
        elif label == "Amarillo" and rng.random() < 0.25:
            etiqueta_fraude_simulada = 1
        else:
            etiqueta_fraude_simulada = 0

        row = {
            "id_siniestro": id_siniestro,
            "id_poliza": id_poliza,
            "id_asegurado": id_asegurado,
            "ramo": (base.get("ramo") or "vehiculos").strip(),
            "cobertura": (base.get("cobertura") or "choque").strip(),
            "fecha_ocurrencia": fecha_oc.isoformat(),
            "fecha_reporte": fecha_rep.isoformat(),
            "monto_reclamado": monto_reclamado,
            "monto_estimado": monto_estimado,
            "monto_pagado": monto_pagado,
            "estado": _pick_state(rng, label),
            "sucursal": ciudad,
            "descripcion": (base.get("explicacion") or "Caso generado para análisis antifraude.").strip(),
            "documentos_completos": docs_ok,
            "beneficiario": f"PROV-RUC-{supplier['supplier_ruc']}",
            "dias_desde_inicio_poliza": dias_ini,
            "dias_desde_fin_poliza": dias_fin,
            "dias_entre_ocurrencia_reporte": dias_reporte,
            "historial_siniestros_asegurado": historial,
            "etiqueta_fraude_simulada": etiqueta_fraude_simulada,
            "supplier_ruc": supplier["supplier_ruc"],
            "supplier_risk_signal_score": round(supplier["supplier_risk_signal_score"], 2),
            "supplier_risk_band": supplier["supplier_risk_band"],
            "score_final": round(score_final, 2),
            "nivel_riesgo": label,
            "alertas_activadas": "|".join(alerts),
            "explicacion": explicacion,
            "accion_sugerida": _action_for_label(label),
        }
        out_rows.append(row)

        if supplier["supplier_ruc"] not in provider_master:
            provider_master[supplier["supplier_ruc"]] = {
                "supplier_ruc": supplier["supplier_ruc"],
                "supplier_risk_signal_score": round(supplier["supplier_risk_signal_score"], 2),
                "supplier_risk_band": supplier["supplier_risk_band"],
                "sanciones_total": supplier["sanciones_total"],
                "contratos_total": supplier["contratos_total"],
                "provincia_muestra": provincia,
            }

    provider_rows = sorted(provider_master.values(), key=lambda x: x["supplier_risk_signal_score"], reverse=True)
    qa = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rows_siniestros": len(out_rows),
        "rows_proveedores": len(provider_rows),
        "risk_distribution": dict(risk_counter),
        "target_rows": target_rows,
    }
    return out_rows, provider_rows, qa


def write_rag_chunks(rows: list[dict[str, Any]], path: Path, limit: int = 50000) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8") as f:
        selected = rows if limit <= 0 else rows[:limit]
        for r in selected:
            doc = {
                "id": r["id_siniestro"],
                "text": (
                    f"Siniestro {r['id_siniestro']} ({r['ramo']} / {r['cobertura']}) en {r['sucursal']}. "
                    f"Riesgo {r['nivel_riesgo']} con score {r['score_final']}. "
                    f"Proveedor {r['supplier_ruc']} ({r['supplier_risk_band']}, {r['supplier_risk_signal_score']}). "
                    f"Alertas: {r['alertas_activadas']}. "
                    f"Fechas ocurrencia/reporte: {r['fecha_ocurrencia']} / {r['fecha_reporte']}. "
                    f"Monto reclamado/estimado/pagado: {r['monto_reclamado']} / {r['monto_estimado']} / {r['monto_pagado']}."
                ),
                "metadata": {
                    "nivel_riesgo": r["nivel_riesgo"],
                    "supplier_ruc": r["supplier_ruc"],
                    "fecha_ocurrencia": r["fecha_ocurrencia"],
                },
            }
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
            n += 1
    return n


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Genera dataset canónico súper completo listo para agente.")
    p.add_argument("--rows", type=int, default=25000, help="Número de siniestros a generar.")
    p.add_argument("--seed", type=int, default=42, help="Semilla reproducible.")
    p.add_argument(
        "--rag-chunks-max",
        type=int,
        default=50000,
        help="Máximo de chunks para RAG (0 = todos los siniestros).",
    )
    p.add_argument("--output-dir", type=Path, default=OUT_DIR_DEFAULT)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    sin_rows, prov_rows, qa = build_agent_ready_siniestros(target_rows=args.rows, seed=args.seed)

    sin_path = args.output_dir / "siniestros_canonico.csv"
    prov_path = args.output_dir / "proveedores_contexto.csv"
    qa_path = args.output_dir / "qa_agent_ready.json"
    rag_path = args.output_dir / "rag_chunks_siniestros.jsonl"

    _write_csv(sin_path, sin_rows, CANONICAL_FIELDS)
    _write_csv(
        prov_path,
        prov_rows,
        ["supplier_ruc", "supplier_risk_signal_score", "supplier_risk_band", "sanciones_total", "contratos_total", "provincia_muestra"],
    )
    qa["paths"] = {
        "siniestros_canonico": str(sin_path.relative_to(ROOT)),
        "proveedores_contexto": str(prov_path.relative_to(ROOT)),
        "rag_chunks": str(rag_path.relative_to(ROOT)),
    }
    qa["rag_chunks"] = write_rag_chunks(sin_rows, rag_path, limit=args.rag_chunks_max)
    qa_path.write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(qa, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
