"""Text normalization for claim narratives."""

from __future__ import annotations

import re
import unicodedata

STOPWORDS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al",
    "y", "o", "que", "en", "por", "para", "con", "sin", "mi", "su", "se",
    "a", "ante", "como", "me", "lo", "es", "fue", "fueron", "del", "sobre",
}

DOMAIN_SYNONYMS = {
    "auto": "vehiculo",
    "carro": "vehiculo",
    "coche": "vehiculo",
    "vehículo": "vehiculo",
    "colision": "choque",
    "colisiono": "choque",
    "colisionó": "choque",
    "impacto": "choque",
    "impactado": "choque",
    "impactada": "choque",
    "impactar": "choque",
    "impactó": "choque",
    "golpeo": "choque",
    "golpeó": "choque",
    "escapo": "huye",
    "escapó": "huye",
    "fuga": "huye",
    "huyo": "huye",
    "huyó": "huye",
    "desconocido": "no_identificado",
    "identificado": "identificado",
    "tercero": "tercero",
}


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    text = strip_accents(str(text).lower())
    text = re.sub(r"[^a-z0-9_\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str | None) -> list[str]:
    normalized = normalize_text(text)
    tokens: list[str] = []
    for token in normalized.split():
        if token in STOPWORDS or len(token) <= 2:
            continue
        tokens.append(DOMAIN_SYNONYMS.get(token, token))
    return tokens


def normalized_for_vectorizer(text: str | None) -> str:
    return " ".join(tokenize(text))
