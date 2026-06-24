"""Routing coverage for the §12 mandatory agent questions and common phrasings."""

from __future__ import annotations

import pytest

from src.agent.router import route

# §12 — the 12 questions the agent must answer, mapped to their expected intent.
PDF_QUESTIONS = [
    ("¿Cuáles son los 10 siniestros con mayor riesgo de posible fraude?", "top_riesgo"),
    ("¿Por qué el siniestro SIN-046 fue marcado como alto riesgo?", "explicar_siniestro"),
    ("¿Qué proveedores concentran más alertas?", "ranking_proveedores"),
    ("¿Qué ramos tienen mayor porcentaje de casos sospechosos?", "riesgo_por_ramo"),
    ("¿Qué ciudades presentan mayor concentración de alertas?", "ranking_ciudades"),
    ("¿Qué asegurados tienen mayor frecuencia de reclamos?", "frecuencia_asegurados"),
    ("¿Qué documentos faltan en los casos críticos?", "documentos_faltantes"),
    ("¿Qué casos tienen montos atípicos?", "montos_atipicos"),
    ("¿Qué siniestros ocurrieron cerca del inicio de la póliza?", "borde_vigencia"),
    ("¿Qué patrones se repiten en los reclamos sospechosos?", "patrones_repetidos"),
    ("Genera un resumen ejecutivo de los casos críticos.", "resumen_ejecutivo"),
    ("Recomienda qué casos debería revisar primero el analista.", "recomendar_revision"),
]

# Alternative phrasings the jury might use — must still route correctly.
PHRASING_VARIANTS = [
    ("¿Qué conexiones tiene el siniestro SIN-046 en el grafo?", "conexiones_grafo"),
    ("Muéstrame las relaciones del siniestro SIN-046", "conexiones_grafo"),
    ("¿Hay redes de fraude organizadas en el portafolio?", "redes_fraude"),
    ("Genera el expediente antifraude del siniestro SIN-046", "expediente_siniestro"),
    ("¿Hay narrativas similares al siniestro SIN-046?", "narrativas_similares"),
    ("¿Qué día es hoy?", "fecha_actual"),
    ("Hola", "saludo"),
    ("¿Qué puedes hacer?", "ayuda_agente"),
]


@pytest.mark.parametrize("question, expected", PDF_QUESTIONS)
def test_pdf_questions_route_to_expected_intent(question: str, expected: str) -> None:
    assert route(question).name == expected


@pytest.mark.parametrize("question, expected", PHRASING_VARIANTS)
def test_phrasing_variants_route_to_expected_intent(question: str, expected: str) -> None:
    assert route(question).name == expected
