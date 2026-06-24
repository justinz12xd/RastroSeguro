"""Advanced RAG (Retrieval-Augmented Generation) document search engine.

This engine chunks documentation files into semantic paragraphs, normalizes
text to handle diacritics, and scores chunks by term density and overlap
for high-relevance search.
"""

from __future__ import annotations

import string
import unicodedata
from pathlib import Path
from typing import Any

KNOWLEDGE_BASE_DIR = Path("docs/knowledge_base")


def _normalize_text(text: str) -> str:
    """Normalize text by lowering, removing diacritics, and stripping punctuation."""
    text_lower = text.lower()
    # Remove accents/diacritics
    nfd = unicodedata.normalize("NFD", text_lower)
    clean_text = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    # Replace punctuation with spaces to avoid joining words
    for char in string.punctuation + "¿¡":
        clean_text = clean_text.replace(char, " ")
    return " ".join(clean_text.split())


def _extract_terms(text: str) -> set[str]:
    """Extract clean words of length > 3 as indexing/query terms."""
    normalized = _normalize_text(text)
    return {word for word in normalized.split() if len(word) > 3}


def _chunk_document(text: str, max_len: int = 800) -> list[str]:
    """Segment a markdown document into chunks by paragraphs of controlled size."""
    raw_paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current_chunk: list[str] = []
    current_len = 0

    for paragraph in raw_paragraphs:
        p_len = len(paragraph)
        # If adding this paragraph exceeds max_len, save current chunk and start new one
        if current_chunk and (current_len + p_len > max_len):
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [paragraph]
            current_len = p_len
        else:
            current_chunk.append(paragraph)
            current_len += p_len + 2  # +2 accounts for the "\n\n" separator

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks


def search_docs(query: str, top_k: int = 3) -> list[dict[str, str]]:
    """Search documentation for matches, scoring chunks by term overlap and density."""
    query_terms = _extract_terms(query)
    if not query_terms:
        return []

    candidates: list[dict[str, Any]] = []

    # Dynamic scan of all markdown files in the knowledge base directory
    doc_paths = list(KNOWLEDGE_BASE_DIR.glob("*.md")) if KNOWLEDGE_BASE_DIR.exists() else []
    for path in doc_paths:

        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue

        chunks = _chunk_document(text)
        for chunk in chunks:
            chunk_terms = _extract_terms(chunk)
            # Find unique terms matched
            matched_terms = query_terms.intersection(chunk_terms)
            if not matched_terms:
                continue

            # Calculate total term frequency (density) in normalized chunk text
            normalized_chunk = _normalize_text(chunk)
            occurrences = sum(normalized_chunk.split().count(term) for term in matched_terms)

            # Score formula: matches density + matching depth
            score = (len(matched_terms) * 10) + occurrences
            candidates.append({
                "source": str(path),
                "snippet": chunk,
                "score": score
            })

    # Sort by score in descending order
    sorted_candidates = sorted(candidates, key=lambda c: c["score"], reverse=True)

    # Format output (excluding score for compatibility with contracts)
    return [
        {"source": c["source"], "snippet": c["snippet"]}
        for c in sorted_candidates[:top_k]
    ]
