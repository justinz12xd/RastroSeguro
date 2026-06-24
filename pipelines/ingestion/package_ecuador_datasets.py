from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PUBLIC_DIR = ROOT / "data" / "processed" / "public_ecuador_only"
SYNTH_DIR = ROOT / "data" / "processed" / "synthetic_for_modeling"


def _copy_files(target_dir: Path, relative_paths: list[str]) -> list[dict]:
    target_dir.mkdir(parents=True, exist_ok=True)
    copied: list[dict] = []
    for rel in relative_paths:
        src = ROOT / rel
        if not src.exists():
            continue
        dst = target_dir / src.name
        shutil.copy2(src, dst)
        copied.append(
            {
                "source_path": str(src.relative_to(ROOT)),
                "target_path": str(dst.relative_to(ROOT)),
                "size_bytes": src.stat().st_size,
            }
        )
    return copied


def main() -> None:
    public_files = [
        "data/curated/ecuador/sercop_sanciones_curated.csv",
        "data/curated/ecuador/ocds_contratos_curated.csv",
        "data/curated/ecuador/supplier_risk_features.csv",
        "data/curated/ecuador/inec_dataset_agg.csv",
        "data/curated/ecuador/inec_column_profile.csv",
        "data/curated/ecuador/inec_records_sample.csv",
        "data/curated/ecuador/ecu911_monthly_agg.csv",
        "data/curated/ecuador/curation_summary.json",
        "data/ecuador/inventario_manifest.json",
        "data/ecuador/inventario_links.tsv",
        "data/ecuador/data_dictionary_ecuador.csv",
        "data/ecuador/boost_summary.json",
    ]

    synthetic_files = [
        "data/processed/agent_ready/siniestros_canonico.csv",
        "data/processed/agent_ready/proveedores_contexto.csv",
        "data/processed/agent_ready/rag_chunks_siniestros.jsonl",
        "data/processed/agent_ready/qa_agent_ready.json",
        "data/synthetic/mock_siniestros_scored.csv",
    ]

    public_copied = _copy_files(PUBLIC_DIR, public_files)
    synthetic_copied = _copy_files(SYNTH_DIR, synthetic_files)

    public_manifest = {
        "package_name": "public_ecuador_only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_type": "public_ecuador",
        "notes": "Contiene solo datasets públicos de Ecuador (fuentes gubernamentales y portales públicos).",
        "files": public_copied,
    }
    synth_manifest = {
        "package_name": "synthetic_for_modeling",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_type": "synthetic_enriched_with_public_signals",
        "notes": "Contiene dataset sintético/enriquecido para entrenamiento y stress-test de agente.",
        "files": synthetic_copied,
    }

    (PUBLIC_DIR / "manifest.json").write_text(json.dumps(public_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (SYNTH_DIR / "manifest.json").write_text(json.dumps(synth_manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "public_ecuador_only": {
                    "path": str(PUBLIC_DIR.relative_to(ROOT)),
                    "files": len(public_copied),
                },
                "synthetic_for_modeling": {
                    "path": str(SYNTH_DIR.relative_to(ROOT)),
                    "files": len(synthetic_copied),
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
