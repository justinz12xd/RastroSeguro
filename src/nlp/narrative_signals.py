"""Convert narrative similarity matches into explainable risk signals."""

from __future__ import annotations

from src.nlp.similarity_engine import SimilarityMatch


def classify_similarity(similarity: float) -> tuple[int, str]:
    """PDF §7: >=85% -> 8 pts; 70-84% -> 4 pts."""
    if similarity >= 0.85:
        return 8, "alta"
    if similarity >= 0.70:
        return 4, "media"
    return 0, "sin_alerta"


def build_narrative_signal(claim_id: str, matches: list[SimilarityMatch]) -> dict[str, object]:
    if not matches:
        return {
            "id_siniestro": claim_id,
            "score_nlp": 0,
            "alerta_narrativa": False,
            "siniestros_similares": [],
            "explicacion_nlp": "No se detectaron narrativas similares por encima del umbral configurado.",
        }

    best = matches[0]
    points, level = classify_similarity(best.similarity)
    similar_claims = [match.to_dict() for match in matches]
    return {
        "id_siniestro": claim_id,
        "score_nlp": min(100, points * 12.5),
        "alerta_narrativa": points > 0,
        "nivel_alerta_nlp": level,
        "siniestros_similares": similar_claims,
        "explicacion_nlp": (
            f"Narrativa similar a {best.target_id} con {best.similarity:.0%} de similitud. "
            "Esto sugiere revisar posible repetición de relato o patrón operativo."
        ),
    }
