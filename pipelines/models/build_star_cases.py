"""Select demo star cases for Carlos/Jeremy/Justin."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SCORED_PATH = ROOT / "data" / "processed" / "siniestros_scored.csv"
SYNTHETIC_PATH = ROOT / "data" / "synthetic" / "siniestros.csv"
OUTPUT_PATH = ROOT / "reports" / "casos_estrella.json"


def build_star_cases(scored_path: Path = SCORED_PATH, limit: int = 12) -> dict:
    if scored_path.exists():
        df = pd.read_csv(scored_path)
        if "score_final" in df.columns:
            red = df[df["nivel_riesgo"].astype(str).str.lower() == "rojo"].sort_values("score_final", ascending=False)
            yellow = df[df["nivel_riesgo"].astype(str).str.lower() == "amarillo"].sort_values("score_final", ascending=False)
            picks = pd.concat([red.head(limit // 2), yellow.head(limit - limit // 2)], ignore_index=True)
        else:
            picks = df.head(limit)
    elif SYNTHETIC_PATH.exists():
        df = pd.read_csv(SYNTHETIC_PATH)
        picks = df[df["etiqueta_fraude_simulada"] == 1].head(limit)
        if picks.empty:
            picks = df.head(limit)
    else:
        raise FileNotFoundError("No hay siniestros_scored.csv ni siniestros.csv para casos estrella")

    cases = []
    for _, row in picks.iterrows():
        cases.append(
            {
                "id_siniestro": row.get("id_siniestro"),
                "ramo": row.get("ramo"),
                "ciudad": row.get("ciudad"),
                "nivel_riesgo": row.get("nivel_riesgo", "N/A"),
                "score_final": row.get("score_final"),
                "monto_reclamado": row.get("monto_reclamado"),
                "explicacion_demo": row.get("explicacion") or row.get("descripcion"),
                "accion_sugerida": row.get("accion_sugerida", "Revisión documental"),
            }
        )
    return {"count": len(cases), "cases": cases}


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera reports/casos_estrella.json")
    parser.add_argument("--scored", type=Path, default=SCORED_PATH)
    parser.add_argument("--limit", type=int, default=12)
    args = parser.parse_args()
    payload = build_star_cases(args.scored, limit=args.limit)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT_PATH), "count": payload["count"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
