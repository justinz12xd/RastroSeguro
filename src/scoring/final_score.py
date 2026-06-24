"""Final scoring pipeline for RastroSeguro."""

from __future__ import annotations

from pathlib import Path
from typing import Any


from src.categorical.scoring import enrich_claims_with_categorical
from src.graph.scoring import enrich_claims_with_graph
from src.model_integration.scoring import enrich_claims_with_model_scores
from src.nlp.scoring import enrich_claims_with_nlp
from src.rules.rule_registry import evaluate_rules, rules_score
from src.utils.risk_levels import clamp_score, risk_level, suggested_action
from src.scoring.calibration import apply_portfolio_calibration
from src.scoring.serialization import serialize_scored_columns
from src.infrastructure.config.paths import RAW_CLAIMS_PATH, SCORED_CLAIMS_PATH

# Paths now live in src.infrastructure.config.paths. Re-exported here as
# INPUT_PATH/OUTPUT_PATH for backward compatibility with existing importers.
INPUT_PATH = RAW_CLAIMS_PATH
OUTPUT_PATH = SCORED_CLAIMS_PATH
NEUTRAL_COMPONENT_SCORE = 50.0

COMPONENT_WEIGHTS = {
    "score_reglas": 0.30,
    "score_modelo": 0.25,
    "score_anomalia": 0.15,
    "score_nlp": 0.15,
    "score_grafo": 0.10,
    "score_categorico": 0.05,
}

from src.scoring.calibration import TARGET_RISK_DISTRIBUTION, apply_portfolio_calibration


def compute_final_score(components: dict[str, float | int | None]) -> float:
    score = 0.0
    for name, weight in COMPONENT_WEIGHTS.items():
        value = components.get(name, NEUTRAL_COMPONENT_SCORE)
        score += clamp_score(value) * weight
    return round(clamp_score(score), 2)


def build_explanation(row: dict[str, Any], alerts: list[dict[str, Any]]) -> str:
    claim_id = row.get("id_siniestro", "el siniestro")
    level = row.get("nivel_riesgo", "Sin clasificar")
    if not alerts:
        return f"El siniestro {claim_id} fue clasificado como {level} sin alertas críticas activadas. Mantener revisión habitual."

    top_alerts = sorted(alerts, key=lambda item: item.get("points", 0), reverse=True)[:4]
    reasons = "; ".join(item.get("message", item.get("name", "alerta")) for item in top_alerts)
    return (
        f"El siniestro {claim_id} fue clasificado como {level} porque acumula señales de riesgo: "
        f"{reasons}. El resultado es una priorización para revisión humana, no una acusación de fraude."
    )


def score_claim(claim: dict[str, Any]) -> dict[str, Any]:
    rule_results = evaluate_rules(claim)
    alerts = [result.to_dict() for result in rule_results]
    score_reglas = rules_score(rule_results)

    components = {
        "score_reglas": score_reglas,
        "score_modelo": claim.get("score_modelo", NEUTRAL_COMPONENT_SCORE),
        "score_anomalia": claim.get("score_anomalia", NEUTRAL_COMPONENT_SCORE),
        "score_nlp": claim.get("score_nlp", NEUTRAL_COMPONENT_SCORE),
        "score_grafo": claim.get("score_grafo", NEUTRAL_COMPONENT_SCORE),
        "score_categorico": claim.get("score_categorico", NEUTRAL_COMPONENT_SCORE),
    }
    final = compute_final_score(components)
    # Guardrail: strong audited rules should be able to escalate even while
    # ML/NLP/graph components are still neutral or unavailable.
    if score_reglas >= 90:
        final = max(final, 80.0)
    elif score_reglas >= 75:
        final = max(final, 76.0)
    level = risk_level(final)

    scored = dict(claim)
    scored.update(components)
    scored["score_final"] = final
    scored["nivel_riesgo"] = level
    scored["alertas_activadas"] = alerts
    scored["rule_trace"] = [
        {
            "code": alert.get("code"),
            "pdf_ref": alert.get("pdf_ref"),
            "points": alert.get("points"),
            "severity": alert.get("severity"),
            "category": alert.get("category"),
            "evidence": alert.get("evidence", {}),
        }
        for alert in alerts
    ]
    scored["explicacion"] = build_explanation(scored, alerts)
    scored["accion_sugerida"] = suggested_action(level)
    return scored


def score_dataframe(df):
    import pandas as pd

    claims = [row.dropna().to_dict() for _, row in df.iterrows()]
    if claims:
        claims = enrich_claims_with_graph(claims)
        claims = enrich_claims_with_categorical(claims)
        claims = enrich_claims_with_model_scores(claims)
    if claims and any(claim.get("descripcion") for claim in claims):
        claims = enrich_claims_with_nlp(claims)
    scored_rows = [score_claim(claim) for claim in claims]
    result = pd.DataFrame(scored_rows)
    result = apply_portfolio_calibration(result)
    return serialize_scored_columns(result)


def run_scoring(input_path: Path = INPUT_PATH, output_path: Path = OUTPUT_PATH) -> Path:
    if not input_path.exists():
        raise FileNotFoundError(
            f"No se encontró {input_path}. Pide a Carlos generar el dataset oficial con: "
            "python -m pipelines.data.generate_synthetic_data"
        )
    import pandas as pd

    df = pd.read_csv(input_path)
    scored = score_dataframe(df)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    scored.to_csv(output_path, index=False)
    return output_path


if __name__ == "__main__":
    try:
        path = run_scoring()
    except FileNotFoundError as exc:
        print(str(exc))
        raise SystemExit(1) from None
    print(f"Scoring generado en {path}")
