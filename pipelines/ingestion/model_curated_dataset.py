from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "ecuador"
DEFAULT_OUT = ROOT / "data" / "curated" / "ecuador"

RUC_RE = re.compile(r"\b\d{13}\b")

SERCOP_FIELDS = [
    "year",
    "ruc",
    "razon_social",
    "fecha_emision",
    "estado",
    "tipo_sancion",
    "plazo_dias",
    "motivo_corto",
    "pdf_url",
    "source_url",
    "raw",
]
OCDS_FIELDS = [
    "year_query",
    "query_type",
    "search_term",
    "supplier_ruc",
    "ocid",
    "id",
    "year",
    "month",
    "method",
    "internal_type",
    "locality",
    "region",
    "suppliers",
    "buyer",
    "amount",
    "date",
    "title",
    "description",
    "budget",
]
INEC_AGG_FIELDS = [
    "dataset_key",
    "year",
    "source_key",
    "page_url",
    "download_url",
    "member_name",
    "total_cells",
    "rows_distintos",
    "cols_distintas",
    "cells_numericas",
    "cells_texto",
]
INEC_COLUMN_PROFILE_FIELDS = [
    "dataset_key",
    "year",
    "col_idx",
    "cells_total",
    "rows_distintos",
    "numeric_ratio",
    "unique_values_capped",
    "top_values_json",
]
INEC_SAMPLE_FIELDS = [
    "dataset_key",
    "year",
    "row_idx",
    "col_1",
    "col_2",
    "col_3",
    "col_4",
    "col_5",
    "col_6",
    "col_7",
    "col_8",
    "col_9",
    "col_10",
]


def _clean_ruc(value: Any) -> str:
    s = re.sub(r"\D", "", str(value or ""))
    return s if len(s) == 13 else ""


def _to_int(value: Any) -> int | None:
    try:
        return int(str(value).strip())
    except Exception:
        return None


def _to_float(value: Any) -> float:
    try:
        return float(str(value).strip())
    except Exception:
        return 0.0


def _parse_any_date(value: Any) -> str:
    s = str(value or "").strip()
    if not s:
        return ""
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    if "T" in s:
        return s.split("T")[0]
    return ""


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def _add_capped_unique(container: dict[str, Any], key: str, value: str, cap: int) -> None:
    if not value:
        return
    uniq_key = f"_{key}_set"
    over_key = f"_{key}_overflow"
    s = container.setdefault(uniq_key, set())
    if container.get(over_key):
        return
    s.add(value)
    if len(s) > cap:
        container[over_key] = True


def _count_capped_unique(container: dict[str, Any], key: str, cap: int) -> int:
    uniq_key = f"_{key}_set"
    over_key = f"_{key}_overflow"
    s = container.get(uniq_key, set())
    if container.get(over_key):
        return cap
    return len(s)


def load_sercop_rows(path: Path) -> list[dict[str, Any]]:
    csv.field_size_limit(sys.maxsize)
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    with path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            source_url = row.get("source_url") or row.get("source_page") or ""
            clean = {
                "year": _to_int(row.get("year")),
                "ruc": _clean_ruc(row.get("ruc")),
                "razon_social": (row.get("razon_social") or "").strip(),
                "fecha_emision": _parse_any_date(row.get("fecha_emision")),
                "estado": (row.get("estado") or "").strip(),
                "tipo_sancion": (row.get("tipo_sancion") or "").strip(),
                "plazo_dias": _to_int(row.get("plazo_dias")),
                "motivo_corto": (row.get("motivo_corto") or "").strip(),
                "pdf_url": (row.get("pdf_url") or "").strip(),
                "source_url": source_url.strip(),
                "raw": (row.get("raw") or "")[:1200],
            }
            dedup = f"{clean['ruc']}|{clean['fecha_emision']}|{clean['pdf_url']}|{clean['raw'][:200]}"
            if dedup in seen:
                continue
            seen.add(dedup)
            rows.append(clean)
    return rows


def _extract_supplier_ruc(supplier_ruc: Any, suppliers: Any) -> str:
    direct = _clean_ruc(supplier_ruc)
    if direct:
        return direct
    m = RUC_RE.search(str(suppliers or ""))
    return m.group(0) if m else ""


def load_ocds_rows(path: Path) -> list[dict[str, Any]]:
    csv.field_size_limit(sys.maxsize)
    rows: list[dict[str, Any]] = []
    seen_ocid: set[str] = set()
    with path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ocid = str(row.get("ocid") or "").strip()
            if not ocid or ocid in seen_ocid:
                continue
            seen_ocid.add(ocid)
            rows.append(
                {
                    "year_query": _to_int(row.get("year_query")),
                    "query_type": (row.get("query_type") or "").strip(),
                    "search_term": (row.get("search_term") or "").strip(),
                    "supplier_ruc": _extract_supplier_ruc(row.get("supplier_ruc"), row.get("suppliers")),
                    "ocid": ocid,
                    "id": _to_int(row.get("id")),
                    "year": _to_int(row.get("year")),
                    "month": _to_int(row.get("month")),
                    "method": (row.get("method") or "").strip(),
                    "internal_type": (row.get("internal_type") or "").strip(),
                    "locality": (row.get("locality") or "").strip(),
                    "region": (row.get("region") or "").strip(),
                    "suppliers": (row.get("suppliers") or "").strip(),
                    "buyer": (row.get("buyer") or "").strip(),
                    "amount": _to_float(row.get("amount")),
                    "date": _parse_any_date(row.get("date")),
                    "title": (row.get("title") or "").strip(),
                    "description": (row.get("description") or "")[:500],
                    "budget": _to_float(row.get("budget")),
                }
            )
    return rows


def aggregate_ecu911(path: Path, max_rows: int = 0) -> list[dict[str, Any]]:
    csv.field_size_limit(sys.maxsize)
    agg: dict[tuple[str, str, str, str], int] = defaultdict(int)
    with path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for i, row in enumerate(reader, start=1):
            if max_rows and i > max_rows:
                break
            fecha = _parse_any_date(row.get("Fecha"))
            ym = fecha[:7] if fecha else ""
            key = (
                ym,
                str(row.get("provincia", "")).strip().upper(),
                str(row.get("Servicio", "")).strip().upper(),
                str(row.get("Subtipo", "")).strip().upper(),
            )
            agg[key] += 1

    return [
        {
            "year_month": year_month,
            "provincia": provincia,
            "servicio": servicio,
            "subtipo": subtipo,
            "total_eventos": total_eventos,
        }
        for (year_month, provincia, servicio, subtipo), total_eventos in agg.items()
    ]


def aggregate_inec(
    path: Path,
    max_rows: int = 0,
    sample_rows_per_dataset: int = 2000,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Curado de INEC materializado por celda.
    Entrada esperada por fila:
      event_type,source_key,page_url,file_name,row_idx,col_idx,value,download_url,member_name
    """
    csv.field_size_limit(sys.maxsize)
    by_dataset: dict[str, dict[str, Any]] = {}
    by_dataset_col: dict[tuple[str, str], dict[str, Any]] = {}
    sample_rows: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)

    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for i, line in enumerate(f, start=1):
            if max_rows and i > max_rows:
                break
            if not line:
                continue
            line = line.rstrip("\n\r")
            if not line:
                continue
            # Salta bloques nulos/corruptos del inicio.
            if "\x00" in line:
                continue

            # Estructura base esperada: 9 campos.
            parts = line.split(",")
            if len(parts) < 9:
                continue

            source_key = (parts[1] or "").strip()
            page_url = (parts[2] or "").strip()
            dataset_key = (parts[3] or "").strip()
            row_idx = (parts[4] or "").strip()
            col_idx = (parts[5] or "").strip()
            value = ",".join(parts[6:-2]).strip()
            download_url = (parts[-2] or "").strip()
            member_name = (parts[-1] or "").strip()

            year_match = re.search(r"(20\d{2})", dataset_key)
            year = year_match.group(1) if year_match else ""

            key = dataset_key or member_name or download_url
            if not key:
                continue
            agg = by_dataset.setdefault(
                key,
                {
                    "dataset_key": dataset_key,
                    "year": year,
                    "source_key": source_key,
                    "page_url": page_url,
                    "download_url": download_url,
                    "member_name": member_name,
                    "total_cells": 0,
                    "_cols": set(),
                    "_rows_overflow": False,
                    "cells_numericas": 0,
                    "cells_texto": 0,
                },
            )
            agg["total_cells"] += 1
            _add_capped_unique(agg, "rows", row_idx, 100000)
            if col_idx:
                agg["_cols"].add(col_idx)
            v = (value or "").strip()
            if not v:
                continue
            try:
                float(v.replace(",", ""))
                agg["cells_numericas"] += 1
            except ValueError:
                agg["cells_texto"] += 1

            # Perfil por columna del dataset
            col_key = (key, col_idx)
            cagg = by_dataset_col.setdefault(
                col_key,
                {
                    "dataset_key": key,
                    "year": year,
                    "col_idx": col_idx,
                    "cells_total": 0,
                    "numeric_cells": 0,
                    "_top_counts": defaultdict(int),
                },
            )
            cagg["cells_total"] += 1
            _add_capped_unique(cagg, "rows", row_idx, 50000)
            is_numeric = False
            try:
                float(v.replace(",", ""))
                is_numeric = True
            except ValueError:
                is_numeric = False
            if is_numeric:
                cagg["numeric_cells"] += 1
            if v:
                _add_capped_unique(cagg, "unique", v, 50000)
                # Mantén conteo top en memoria (cap de claves).
                if v in cagg["_top_counts"] or len(cagg["_top_counts"]) < 2000:
                    cagg["_top_counts"][v] += 1

            # Muestra de filas reconstruidas (wide), útil para inspección humana.
            ds_samples = sample_rows[key]
            if row_idx in ds_samples:
                ds_samples[row_idx][f"col_{col_idx}"] = v
            elif row_idx and len(ds_samples) < sample_rows_per_dataset:
                ds_samples[row_idx] = {"dataset_key": key, "year": year, "row_idx": row_idx, f"col_{col_idx}": v}

    out: list[dict[str, Any]] = []
    for _, agg in by_dataset.items():
        out.append(
            {
                "dataset_key": agg["dataset_key"],
                "year": agg["year"],
                "source_key": agg["source_key"],
                "page_url": agg["page_url"],
                "download_url": agg["download_url"],
                "member_name": agg["member_name"],
                "total_cells": agg["total_cells"],
                "rows_distintos": _count_capped_unique(agg, "rows", 100000),
                "cols_distintas": len(agg["_cols"]),
                "cells_numericas": agg["cells_numericas"],
                "cells_texto": agg["cells_texto"],
            }
        )
    out.sort(key=lambda x: (x.get("year") or "", x["total_cells"]), reverse=True)

    col_profiles: list[dict[str, Any]] = []
    for (_, _), cagg in by_dataset_col.items():
        top_values = sorted(cagg["_top_counts"].items(), key=lambda kv: kv[1], reverse=True)[:10]
        unique_display = _count_capped_unique(cagg, "unique", 50000)
        ratio = (cagg["numeric_cells"] / cagg["cells_total"]) if cagg["cells_total"] else 0.0
        col_profiles.append(
            {
                "dataset_key": cagg["dataset_key"],
                "year": cagg["year"],
                "col_idx": cagg["col_idx"],
                "cells_total": cagg["cells_total"],
                "rows_distintos": _count_capped_unique(cagg, "rows", 50000),
                "numeric_ratio": round(ratio, 6),
                "unique_values_capped": unique_display,
                "top_values_json": json.dumps([{"value": v, "count": n} for v, n in top_values], ensure_ascii=False),
            }
        )
    col_profiles.sort(key=lambda x: (x.get("year") or "", int(str(x.get("col_idx") or "0") or 0)))

    sample_out: list[dict[str, Any]] = []
    for _, rows_map in sample_rows.items():
        sample_out.extend(rows_map.values())
    sample_out.sort(key=lambda x: (x.get("year") or "", x.get("dataset_key") or "", int(str(x.get("row_idx") or "0") or 0)))
    return out, col_profiles, sample_out


def build_supplier_features(sercop_rows: list[dict[str, Any]], ocds_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sanc_map: dict[str, dict[str, Any]] = {}
    for r in sercop_rows:
        supplier_ruc = r.get("ruc") or ""
        if not supplier_ruc:
            continue
        item = sanc_map.setdefault(
            supplier_ruc,
            {"sanciones_total": 0, "motivos": set(), "ultima_sancion": ""},
        )
        item["sanciones_total"] += 1
        motivo = (r.get("motivo_corto") or "").strip()
        if motivo:
            item["motivos"].add(motivo)
        fecha = r.get("fecha_emision") or ""
        if fecha and fecha > item["ultima_sancion"]:
            item["ultima_sancion"] = fecha

    cont_map: dict[str, dict[str, Any]] = {}
    for r in ocds_rows:
        supplier_ruc = r.get("supplier_ruc") or ""
        if not supplier_ruc:
            continue
        item = cont_map.setdefault(
            supplier_ruc,
            {"contratos_total": 0, "buyers": set(), "monto_total": 0.0, "ultimo_contrato": ""},
        )
        item["contratos_total"] += 1
        buyer = (r.get("buyer") or "").strip()
        if buyer:
            item["buyers"].add(buyer)
        item["monto_total"] += _to_float(r.get("amount"))
        fecha = r.get("date") or ""
        if fecha and fecha > item["ultimo_contrato"]:
            item["ultimo_contrato"] = fecha

    all_rucs = sorted(set(sanc_map.keys()) | set(cont_map.keys()))
    rows: list[dict[str, Any]] = []
    for supplier_ruc in all_rucs:
        s = sanc_map.get(supplier_ruc, {"sanciones_total": 0, "motivos": set(), "ultima_sancion": ""})
        c = cont_map.get(supplier_ruc, {"contratos_total": 0, "buyers": set(), "monto_total": 0.0, "ultimo_contrato": ""})
        score = min(
            100.0,
            (s["sanciones_total"] * 18)
            + (len(s["motivos"]) * 4)
            + (c["contratos_total"] * 0.15)
            + (8 if c["monto_total"] > 1_000_000 else 0),
        )
        if score <= 25:
            band = "verde"
        elif score <= 60:
            band = "amarillo"
        else:
            band = "rojo"
        rows.append(
            {
                "supplier_ruc": supplier_ruc,
                "sanciones_total": s["sanciones_total"],
                "motivos_distintos": len(s["motivos"]),
                "contratos_total": c["contratos_total"],
                "compradores_unicos": len(c["buyers"]),
                "monto_total": round(c["monto_total"], 2),
                "ultima_sancion": s["ultima_sancion"],
                "ultimo_contrato": c["ultimo_contrato"],
                "risk_signal_score": round(score, 2),
                "risk_band": band,
            }
        )

    rows.sort(key=lambda x: (x["risk_signal_score"], x["sanciones_total"]), reverse=True)
    return rows


def run(
    output_dir: Path,
    skip_ecu911: bool,
    ecu911_max_rows: int,
    skip_inec: bool,
    inec_max_rows: int,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    sercop_raw = RAW_DIR / "sercop_sanciones_2021_2026.csv"
    ocds_raw = RAW_DIR / "ocds_proveedores_2021_2026.csv"
    ecu911_raw = RAW_DIR / "ecu911_2021_2026.csv"
    inec_raw = RAW_DIR / "inec_siniestros_2021_2026.csv"

    sercop_rows = load_sercop_rows(sercop_raw)
    ocds_rows = load_ocds_rows(ocds_raw)
    features_rows = build_supplier_features(sercop_rows, ocds_rows)

    sercop_out = output_dir / "sercop_sanciones_curated.csv"
    ocds_out = output_dir / "ocds_contratos_curated.csv"
    features_out = output_dir / "supplier_risk_features.csv"
    _write_csv(sercop_out, sercop_rows, SERCOP_FIELDS)
    _write_csv(ocds_out, ocds_rows, OCDS_FIELDS)
    _write_csv(
        features_out,
        features_rows,
        [
            "supplier_ruc",
            "sanciones_total",
            "motivos_distintos",
            "contratos_total",
            "compradores_unicos",
            "monto_total",
            "ultima_sancion",
            "ultimo_contrato",
            "risk_signal_score",
            "risk_band",
        ],
    )

    inec_info: dict[str, Any] = {"skipped": skip_inec}
    if not skip_inec:
        inec_rows, inec_col_profiles, inec_samples = aggregate_inec(inec_raw, max_rows=inec_max_rows)
        inec_out = output_dir / "inec_dataset_agg.csv"
        inec_col_profile_out = output_dir / "inec_column_profile.csv"
        inec_sample_out = output_dir / "inec_records_sample.csv"
        _write_csv(inec_out, inec_rows, INEC_AGG_FIELDS)
        _write_csv(inec_col_profile_out, inec_col_profiles, INEC_COLUMN_PROFILE_FIELDS)
        _write_csv(inec_sample_out, inec_samples, INEC_SAMPLE_FIELDS)
        inec_info = {
            "rows": len(inec_rows),
            "path": str(inec_out.relative_to(ROOT)),
            "column_profile_rows": len(inec_col_profiles),
            "column_profile_path": str(inec_col_profile_out.relative_to(ROOT)),
            "sample_rows": len(inec_samples),
            "sample_path": str(inec_sample_out.relative_to(ROOT)),
            "max_rows_input": inec_max_rows,
        }

    ecu911_info: dict[str, Any] = {"skipped": skip_ecu911}
    if not skip_ecu911:
        ecu911_rows = aggregate_ecu911(ecu911_raw, max_rows=ecu911_max_rows)
        ecu911_out = output_dir / "ecu911_monthly_agg.csv"
        _write_csv(ecu911_out, ecu911_rows, ["year_month", "provincia", "servicio", "subtipo", "total_eventos"])
        ecu911_info = {
            "rows": len(ecu911_rows),
            "path": str(ecu911_out.relative_to(ROOT)),
            "max_rows_input": ecu911_max_rows,
        }

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "curated_outputs": {
            "sercop_sanciones_curated": {"rows": len(sercop_rows), "path": str(sercop_out.relative_to(ROOT))},
            "ocds_contratos_curated": {"rows": len(ocds_rows), "path": str(ocds_out.relative_to(ROOT))},
            "supplier_risk_features": {"rows": len(features_rows), "path": str(features_out.relative_to(ROOT))},
            "inec_dataset_agg": inec_info,
            "ecu911_monthly_agg": ecu911_info,
        },
        "inec_raw_reference": {
            "path": str(inec_raw.relative_to(ROOT)),
            "size_bytes": inec_raw.stat().st_size if inec_raw.exists() else 0,
            "recommended_strategy": "mantener fuera de Supabase y cargar solo agregados derivados",
        },
    }
    summary_path = output_dir / "curation_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Modela dataset curado para Postgres/Supabase.")
    p.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    p.add_argument("--skip-ecu911-agg", action="store_true", help="No genera agregados de ECU911.")
    p.add_argument("--skip-inec-agg", action="store_true", help="No genera agregados de INEC.")
    p.add_argument(
        "--ecu911-max-rows",
        type=int,
        default=0,
        help="Limita filas de entrada ECU911 para pruebas rápidas (0 = sin límite).",
    )
    p.add_argument(
        "--inec-max-rows",
        type=int,
        default=0,
        help="Limita filas de entrada INEC para pruebas rápidas (0 = sin límite).",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    summary = run(
        args.output_dir,
        skip_ecu911=args.skip_ecu911_agg,
        ecu911_max_rows=args.ecu911_max_rows,
        skip_inec=args.skip_inec_agg,
        inec_max_rows=args.inec_max_rows,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
