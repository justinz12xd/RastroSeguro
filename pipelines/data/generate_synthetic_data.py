"""Generate official synthetic claims dataset for team integration."""

from __future__ import annotations

import argparse
import json
import random
from datetime import timedelta
from pathlib import Path

import pandas as pd

from pipelines.data.claim_signals import apply_signals_to_frame
from pipelines.data.demo_scenarios import apply_demo_scenarios
from pipelines.data.ecuador_context import ECUADOR_EXTENSION_COLUMNS, enrich_with_ecuador_context
from src.data.feature_engineering import enrich_base_columns
from pipelines.data.qa_metrics import build_dataset_qa

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "data" / "synthetic" / "siniestros.csv"
CANONICAL_SOURCE = ROOT / "data" / "processed" / "agent_ready" / "siniestros_canonico.csv"

CONTRACT_COLUMNS = [
    "id_siniestro",
    "id_poliza",
    "id_asegurado",
    "ramo",
    "cobertura",
    "ciudad",
    "id_proveedor",
    "beneficiario",
    "fecha_inicio_poliza",
    "fecha_fin_poliza",
    "fecha_ocurrencia",
    "fecha_reporte",
    "monto_reclamado",
    "monto_estimado",
    "suma_asegurada",
    "descripcion",
    "documentos_completos",
    "documentos_inconsistentes",
    "historial_siniestros_asegurado",
    "etiqueta_fraude_simulada",
    "dias_desde_inicio_poliza",
    "dias_desde_fin_poliza",
    "dias_entre_ocurrencia_reporte",
    "id_vehiculo",
    "placa_hash",
    "marca",
    "modelo",
    "anio",
    "tipo_evento",
    "tipo_impacto",
    "tercero_identificado",
    "reporte_policial",
    "hay_testigos",
    "ocurrio_noche",
    "ocurrio_fin_semana",
    "zona_alta_siniestralidad",
    "historial_siniestros_vehiculo",
    "taller",
    "conductor_recurrente",
]

PDF_EXTENSION_COLUMNS = [
    "monto_pagado",
    "estado",
    "sucursal",
    "chasis_hash",
    "motor_hash",
]

OUTPUT_COLUMNS = CONTRACT_COLUMNS + PDF_EXTENSION_COLUMNS + [
    c for c in ECUADOR_EXTENSION_COLUMNS if c not in CONTRACT_COLUMNS
]

VEHICLE_BRANDS = [
    ("Toyota", "Corolla"), ("Toyota", "Hilux"), ("Chevrolet", "Spark"),
    ("Kia", "Rio"), ("Hyundai", "Accent"), ("Nissan", "Sentra"),
    ("Mazda", "3"), ("Volkswagen", "Gol"), ("Renault", "Logan"),
]

def _extract_proveedor_id(row: pd.Series) -> str:
    if pd.notna(row.get("id_proveedor")):
        return str(row["id_proveedor"])
    benef = str(row.get("beneficiario", ""))
    if benef.startswith("PROV-RUC-"):
        return f"PROV-{benef.replace('PROV-RUC-', '')[:12]}"
    ruc = str(row.get("supplier_ruc", "0000000000001"))
    return f"PROV-{ruc}"


def _from_canonical(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["ciudad"] = out.get("sucursal", "Quito")
    out["id_proveedor"] = out.apply(_extract_proveedor_id, axis=1)
    out["beneficiario"] = out.get("beneficiario", out["id_proveedor"])

    fo = pd.to_datetime(out["fecha_ocurrencia"], errors="coerce")
    out["fecha_inicio_poliza"] = fo - pd.to_timedelta(out["dias_desde_inicio_poliza"].fillna(0).astype(int), unit="D")
    out["fecha_fin_poliza"] = fo + pd.to_timedelta(out["dias_desde_fin_poliza"].fillna(180).astype(int), unit="D")

    out["suma_asegurada"] = (out["monto_estimado"].astype(float) * 1.2).clip(lower=1000).round(2)
    out["documentos_inconsistentes"] = out["documentos_completos"].map(
        lambda v: str(v).strip().lower() in {"no", "false", "0"}
    )

    if "monto_pagado" in df.columns:
        out["monto_pagado"] = pd.to_numeric(df["monto_pagado"], errors="coerce").fillna(0).round(2)
    else:
        out["monto_pagado"] = (out["monto_estimado"].astype(float) * 0.5).round(2)
    if "estado" in df.columns:
        out["estado"] = df["estado"].fillna("Reserva")
    else:
        out["estado"] = "Reserva"
    out["sucursal"] = out.get("sucursal", out["ciudad"])

    is_vehicle = out["ramo"].astype(str).str.lower() == "vehiculos"
    out["id_vehiculo"] = out["id_asegurado"].where(is_vehicle, "")
    out["placa_hash"] = out["id_siniestro"].str[-6:].where(is_vehicle, "")
    out["chasis_hash"] = out["id_siniestro"].str[-8:].where(is_vehicle, "")
    out["motor_hash"] = out["id_siniestro"].str[-10:-4].where(is_vehicle, "")

    rng = random.Random(42)
    marcas, modelos, anios = [], [], []
    for idx, row in out.iterrows():
        if str(row.get("ramo", "")).lower() == "vehiculos":
            brand, model = rng.choice(VEHICLE_BRANDS)
            marcas.append(brand)
            modelos.append(model)
            anios.append(rng.randint(2010, 2024))
        else:
            marcas.append("")
            modelos.append("")
            anios.append(None)
    out["marca"] = marcas
    out["modelo"] = modelos
    out["anio"] = anios
    out["tipo_evento"] = out["cobertura"].where(is_vehicle, "")
    out["tipo_impacto"] = "posterior"
    out["tercero_identificado"] = ~is_vehicle | (out["etiqueta_fraude_simulada"] == 0)
    out["reporte_policial"] = is_vehicle & (out["cobertura"].astype(str).str.lower() == "robo")
    out["hay_testigos"] = out["etiqueta_fraude_simulada"] == 0
    out["ocurrio_noche"] = False
    out["ocurrio_fin_semana"] = False
    out["zona_alta_siniestralidad"] = out["ciudad"].isin(["Guayaquil", "Quito"])
    out["historial_siniestros_vehiculo"] = out["historial_siniestros_asegurado"].where(is_vehicle, 0)
    out["taller"] = out["beneficiario"].where(is_vehicle, "")
    out["conductor_recurrente"] = out["historial_siniestros_asegurado"] >= 2

    if "supplier_ruc" in df.columns:
        out["supplier_ruc"] = df["supplier_ruc"]
    if "supplier_risk_signal_score" in df.columns:
        out["supplier_risk_signal_score"] = df["supplier_risk_signal_score"]
    if "supplier_risk_band" in df.columns:
        out["supplier_risk_band"] = df["supplier_risk_band"]

    out = enrich_with_ecuador_context(out)
    out = apply_signals_to_frame(out)
    out = apply_demo_scenarios(out)
    out = enrich_base_columns(out)
    for col in OUTPUT_COLUMNS:
        if col not in out.columns:
            out[col] = None
    return out[OUTPUT_COLUMNS]


def _generate_fresh(rows: int, seed: int) -> pd.DataFrame:
    rng = random.Random(seed)
    ramos = ["vehiculos", "salud", "hogar", "vida", "generales"]
    coberturas = {
        "vehiculos": ["choque", "robo", "rc"],
        "salud": ["atencion_medica"],
        "hogar": ["incendio", "danio"],
        "vida": ["fallecimiento"],
        "generales": ["danio"],
    }
    ciudades = ["Quito", "Guayaquil", "Cuenca", "Manta"]
    records: list[dict] = []
    start = pd.Timestamp("2019-01-01")

    for i in range(1, rows + 1):
        ramo = rng.choice(ramos)
        cobertura = rng.choice(coberturas[ramo])
        ciudad = rng.choice(ciudades)
        dias_ini = rng.randint(0, 300)
        dias_fin = rng.randint(30, 365)
        dias_reporte = max(0, int(rng.gauss(4, 5)))
        fo = start + timedelta(days=rng.randint(0, 2500))
        fi = fo - timedelta(days=dias_ini)
        ff = fo + timedelta(days=dias_fin)
        fr = fo + timedelta(days=dias_reporte)
        monto = round(max(300, rng.gauss(6000, 4000)), 2)
        monto_est = round(monto * rng.uniform(0.8, 1.05), 2)
        suma = round(monto * rng.uniform(1.1, 2.0), 2)
        monto_pagado = round(monto_est * rng.uniform(0.0, 1.0), 2)
        estados = ["Reserva", "Liquidado", "Pago Parcial", "Pago Total", "Negativa"]
        historial = max(0, int(rng.gauss(1.0, 1.2)))
        fraude = 1 if (dias_ini <= 15 and monto > suma * 0.9) or historial >= 3 else int(rng.random() < 0.08)
        docs_ok = fraude == 0 or rng.random() > 0.4
        brand_model = rng.choice(VEHICLE_BRANDS) if ramo == "vehiculos" else ("", "")
        records.append(
            {
                "id_siniestro": f"SIN-{i:06d}",
                "id_poliza": f"POL-{rng.randint(1, 5000):05d}",
                "id_asegurado": f"ASEG-{rng.randint(1, 8000):06d}",
                "ramo": ramo,
                "cobertura": cobertura,
                "ciudad": ciudad,
                "sucursal": ciudad,
                "monto_pagado": monto_pagado,
                "estado": rng.choice(estados),
                "id_proveedor": f"PROV-{rng.randint(1, 200):03d}",
                "beneficiario": f"Taller/Clinica {rng.randint(1, 80)}",
                "fecha_inicio_poliza": fi.date().isoformat(),
                "fecha_fin_poliza": ff.date().isoformat(),
                "fecha_ocurrencia": fo.date().isoformat(),
                "fecha_reporte": fr.date().isoformat(),
                "monto_reclamado": monto,
                "monto_estimado": monto_est,
                "suma_asegurada": suma,
                "descripcion": f"Siniestro {cobertura} en {ciudad} para revisión antifraude.",
                "documentos_completos": "Sí" if docs_ok else "No",
                "documentos_inconsistentes": not docs_ok,
                "historial_siniestros_asegurado": historial,
                "etiqueta_fraude_simulada": fraude,
                "dias_desde_inicio_poliza": dias_ini,
                "dias_desde_fin_poliza": dias_fin,
                "dias_entre_ocurrencia_reporte": dias_reporte,
                "id_vehiculo": f"VEH-{rng.randint(1, 4000):05d}" if ramo == "vehiculos" else "",
                "placa_hash": f"PL{i % 10000:04d}" if ramo == "vehiculos" else "",
                "chasis_hash": f"CH{i % 10000:04d}" if ramo == "vehiculos" else "",
                "motor_hash": f"MO{i % 10000:04d}" if ramo == "vehiculos" else "",
                "marca": brand_model[0],
                "modelo": brand_model[1],
                "anio": rng.randint(2010, 2024) if ramo == "vehiculos" else None,
                "tipo_evento": cobertura if ramo == "vehiculos" else "",
                "tipo_impacto": rng.choice(["frontal", "posterior", "lateral"]) if ramo == "vehiculos" else "",
                "tercero_identificado": fraude == 0,
                "reporte_policial": ramo == "vehiculos" and cobertura == "robo",
                "hay_testigos": fraude == 0,
                "ocurrio_noche": rng.random() < 0.2,
                "ocurrio_fin_semana": rng.random() < 0.3,
                "zona_alta_siniestralidad": ciudad in {"Quito", "Guayaquil"},
                "historial_siniestros_vehiculo": historial if ramo == "vehiculos" else 0,
                "taller": f"Taller {rng.randint(1, 40)}" if ramo == "vehiculos" else "",
                "conductor_recurrente": historial >= 2,
            }
        )
    return _from_canonical(pd.DataFrame(records))


def generate_dataset(rows: int = 25000, seed: int = 42, source: Path | None = CANONICAL_SOURCE) -> pd.DataFrame:
    if source and source.exists():
        df = pd.read_csv(source, nrows=rows if rows > 0 else None)
        return _from_canonical(df)
    return _generate_fresh(rows=rows, seed=seed)


def validate_dataset(df: pd.DataFrame) -> dict:
    return build_dataset_qa(df)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Genera data/synthetic/siniestros.csv")
    p.add_argument("--rows", type=int, default=25000)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    p.add_argument("--source", type=Path, default=CANONICAL_SOURCE)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    df = generate_dataset(rows=args.rows, seed=args.seed, source=args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)
    qa = validate_dataset(df)
    qa_path = args.output.parent / "siniestros_qa.json"
    qa_path.write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(args.output), **qa}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
