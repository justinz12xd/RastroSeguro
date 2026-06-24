"""Intent router for the antifraud agent."""

from __future__ import annotations

import unicodedata

from src.agent.intents import CLAIM_REQUIRED_INTENTS, DOC_INTENTS, INTENT_ALIASES, IntentMatch


def normalize_question(question: str) -> str:
    text = unicodedata.normalize("NFD", question.lower())
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return " ".join(text.replace("_", " ").replace("-", " ").split())


def route_intent(question: str) -> str:
    return route(question).name


def route(question: str) -> IntentMatch:
    text = normalize_question(question)
    if any(token in text for token in ("80", "ochenta")) and "proveedor" in text:
        return IntentMatch(
            name="concentracion_rojos",
            confidence=0.95,
            requires_claim_id=False,
            uses_documentation=False,
        )

    best_name = "top_riesgo"
    best_score = 0

    for intent, aliases in INTENT_ALIASES.items():
        score = sum(1 for alias in aliases if normalize_question(alias) in text)
        if score > best_score:
            best_name, best_score = intent, score

    confidence = min(1.0, 0.35 + (best_score * 0.25)) if best_score else 0.35
    return IntentMatch(
        name=best_name,
        confidence=round(confidence, 2),
        requires_claim_id=best_name in CLAIM_REQUIRED_INTENTS,
        uses_documentation=best_name in DOC_INTENTS,
    )
