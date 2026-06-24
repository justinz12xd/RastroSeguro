"""Export PDF §6.2 complementary tables from siniestros.csv."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "data" / "synthetic" / "siniestros.csv"
DEFAULT_OUT_DIR = ROOT / "data" / "synthetic"
PROVEEDORES_CTX = ROOT / "data" / "processed" / "agent_ready" / "proveedores_contexto.csv"

CANALES = ["directo", "broker", "digital", "agencia"]
ESTADOS_POLIZA = ["vigente", "vencida", "suspendida", "mora"]
SEGMENTOS = ["retail", "premium", "corporativo", "micro"]


def export_complementary_tables(
    input_path: Path = DEFAULT_INPUT,
    output_dir: Path = DEFAULT_OUT_DIR,
) -> dict[str, str]:
    df = pd.read_csv(input_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    polizas = _build_polizas(df)
    asegurados = _build_asegurados(df)
    proveedores = _build_proveedores(df)
    documentos = _build_documentos(df)

    paths = {
        "polizas": output_dir / "polizas.csv",
        "asegurados": output_dir / "asegurados.csv",
        "proveedores": output_dir / "proveedores.csv",
        "documentos": output_dir / "documentos.csv",
        "manifest": output_dir / "dataset_manifest.json",
    }
    polizas.to_csv(paths["polizas"], index=False)
    asegurados.to_csv(paths["asegurados"], index=False)
    proveedores.to_csv(paths["proveedores"], index=False)
    documentos.to_csv(paths["documentos"], index=False)

    manifest = {
        "source": str(input_path.relative_to(ROOT)),
        "lineage": df["data_source_lineage"].iloc[0] if "data_source_lineage" in df.columns and len(df) else "",
        "tables": {
            "siniestros": {"rows": int(len(df)), "path": str(input_path.relative_to(ROOT))},
            "polizas": {"rows": int(len(polizas)), "path": str(paths["polizas"].relative_to(ROOT))},
            "asegurados": {"rows": int(len(asegurados)), "path": str(paths["asegurados"].relative_to(ROOT))},
            "proveedores": {"rows": int(len(proveedores)), "path": str(paths["proveedores"].relative_to(ROOT))},
            "documentos": {"rows": int(len(documentos)), "path": str(paths["documentos"].relative_to(ROOT))},
        },
        "relationships": [
            "siniestros.id_poliza -> polizas.id_poliza",
            "siniestros.id_asegurado -> asegurados.id_asegurado",
            "siniestros.id_proveedor -> proveedores.id_proveedor",
            "documentos.id_siniestro -> siniestros.id_siniestro",
        ],
    }
    paths["manifest"].write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {k: str(v) for k, v in paths.items()}


def _build_polizas(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby("id_poliza", as_index=False).agg(
        id_asegurado=("id_asegurado", "first"),
        ramo=("ramo", "first"),
        fecha_inicio=("fecha_inicio_poliza", "first"),
        fecha_fin=("fecha_fin_poliza", "first"),
        suma_asegurada=("suma_asegurada", "max"),
        ciudad=("ciudad", "first"),
    )
    grouped["prima"] = (grouped["suma_asegurada"] * 0.04).round(2)
    grouped["deducible"] = (grouped["suma_asegurada"] * 0.05).round(2)
    grouped["canal_venta"] = [CANALES[i % len(CANALES)] for i in range(len(grouped))]
    grouped["estado_poliza"] = [ESTADOS_POLIZA[i % len(ESTADOS_POLIZA)] for i in range(len(grouped))]
    return grouped[
        [
            "id_poliza",
            "id_asegurado",
            "ramo",
            "fecha_inicio",
            "fecha_fin",
            "prima",
            "suma_asegurada",
            "deducible",
            "canal_venta",
            "ciudad",
            "estado_poliza",
        ]
    ]


def _build_asegurados(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby("id_asegurado", as_index=False).agg(
        ciudad=("ciudad", "first"),
        num_polizas=("id_poliza", "nunique"),
        reclamos_12m=("id_siniestro", "count"),
        historial=("historial_siniestros_asegurado", "max"),
    )
    grouped["segmento"] = grouped["reclamos_12m"].map(
        lambda n: SEGMENTOS[min(3, int(n) // 3)]
    )
    grouped["antiguedad_anios"] = (grouped["historial"] + 1).clip(lower=1, upper=15)
    grouped["mora_actual"] = grouped["reclamos_12m"].map(lambda n: int(n) >= 4)
    grouped["score_cliente_simulado"] = (
        50 + grouped["reclamos_12m"] * 5 + grouped["historial"] * 3
    ).clip(0, 100).round(1)
    return grouped.rename(columns={"antiguedad_anios": "antiguedad"})[
        [
            "id_asegurado",
            "segmento",
            "antiguedad",
            "ciudad",
            "num_polizas",
            "reclamos_12m",
            "mora_actual",
            "score_cliente_simulado",
        ]
    ]


def _build_proveedores(df: pd.DataFrame) -> pd.DataFrame:
    ctx = pd.read_csv(PROVEEDORES_CTX) if PROVEEDORES_CTX.exists() else pd.DataFrame()
    grouped = df.groupby("id_proveedor", as_index=False).agg(
        ciudad=("ciudad", "first"),
        reclamos_asociados=("id_siniestro", "count"),
        monto_promedio_reclamado=("monto_reclamado", "mean"),
        **(
            {"casos_observados": ("nivel_riesgo", lambda s: int((s.astype(str).str.lower() != "verde").sum()))}
            if "nivel_riesgo" in df.columns
            else {}
        ),
    )
    if "casos_observados" not in grouped.columns:
        grouped["casos_observados"] = (grouped["reclamos_asociados"] * 0.2).astype(int)
    grouped["pct_casos_observados"] = (
        grouped["casos_observados"] / grouped["reclamos_asociados"].clip(lower=1) * 100
    ).round(2)
    grouped["tipo"] = grouped["id_proveedor"].map(
        lambda p: "taller" if str(p).startswith("PROV-") else "proveedor"
    )
    grouped["antiguedad_anios"] = (grouped["reclamos_asociados"] // 5 + 1).clip(upper=10)
    if not ctx.empty and "supplier_ruc" in ctx.columns:
        ctx_map = ctx.set_index("supplier_ruc")
        grouped["supplier_ruc"] = grouped["id_proveedor"].astype(str).str.replace("PROV-", "", regex=False)
        grouped["supplier_risk_band"] = grouped["supplier_ruc"].map(
            lambda r: ctx_map.loc[r, "supplier_risk_band"] if r in ctx_map.index else "verde"
        )
    grouped["monto_promedio_reclamado"] = grouped["monto_promedio_reclamado"].round(2)
    cols = [
        "id_proveedor",
        "tipo",
        "ciudad",
        "reclamos_asociados",
        "monto_promedio_reclamado",
        "pct_casos_observados",
        "antiguedad_anios",
    ]
    return grouped[cols].rename(columns={"antiguedad_anios": "antiguedad"})


def _build_documentos(df: pd.DataFrame) -> pd.DataFrame:
    tipos = ["denuncia", "factura", "informe_tecnico", "foto_evidencia"]
    rows: list[dict] = []
    sample = df.sort_values("score_final", ascending=False).head(500) if "score_final" in df.columns else df.head(500)
    if "score_final" not in df.columns:
        sample = df[df.get("etiqueta_fraude_simulada", 0) == 1].head(500) if len(df) else df
    for _, claim in sample.iterrows():
        docs_ok = str(claim.get("documentos_completos", "Sí")).strip().lower() in {"si", "sí", "yes", "1", "true"}
        inconsistent = bool(claim.get("documentos_inconsistentes", False))
        for j, tipo in enumerate(tipos[:3 if docs_ok else 2]):
            rows.append(
                {
                    "id_documento": f"DOC-{claim['id_siniestro']}-{j+1:02d}",
                    "id_siniestro": claim["id_siniestro"],
                    "tipo_documento": tipo,
                    "entregado": docs_ok or j == 0,
                    "legible": not inconsistent,
                    "fecha_emision": claim.get("fecha_reporte", claim.get("fecha_ocurrencia", "")),
                    "inconsistencia_detectada": inconsistent and j > 0,
                    "observacion": "" if docs_ok else "Documento pendiente de revisión",
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Exporta tablas complementarias PDF §6.2")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    paths = export_complementary_tables(args.input, args.output_dir)
    print(json.dumps(paths, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
