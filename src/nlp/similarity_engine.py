"""Narrative similarity engines with dependency-safe fallback."""

from __future__ import annotations

from dataclasses import dataclass

from src.nlp.text_normalization import normalized_for_vectorizer, tokenize


@dataclass(frozen=True)
class SimilarityMatch:
    source_id: str
    target_id: str
    similarity: float

    def to_dict(self) -> dict[str, float | str]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "similarity": round(self.similarity, 4),
        }


class TokenSimilarityEngine:
    """Fallback engine based on token Jaccard similarity."""

    def compute(self, narratives: dict[str, str], threshold: float = 0.70, top_k: int = 3) -> dict[str, list[SimilarityMatch]]:
        token_sets = {claim_id: set(tokenize(text)) for claim_id, text in narratives.items()}
        matches: dict[str, list[SimilarityMatch]] = {claim_id: [] for claim_id in narratives}

        ids = list(narratives)
        for i, source_id in enumerate(ids):
            for target_id in ids[i + 1:]:
                similarity = self._jaccard(token_sets[source_id], token_sets[target_id])
                if similarity >= threshold:
                    matches[source_id].append(SimilarityMatch(source_id, target_id, similarity))
                    matches[target_id].append(SimilarityMatch(target_id, source_id, similarity))

        return {claim_id: sorted(items, key=lambda item: item.similarity, reverse=True)[:top_k] for claim_id, items in matches.items()}

    @staticmethod
    def _jaccard(left: set[str], right: set[str]) -> float:
        if not left or not right:
            return 0.0
        return len(left & right) / len(left | right)


class TfidfSimilarityEngine:
    """TF-IDF cosine similarity engine when scikit-learn is available."""

    def compute(self, narratives: dict[str, str], threshold: float = 0.70, top_k: int = 3) -> dict[str, list[SimilarityMatch]]:
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
        except Exception:
            return TokenSimilarityEngine().compute(narratives, threshold=threshold, top_k=top_k)

        ids = list(narratives)
        texts = [normalized_for_vectorizer(narratives[claim_id]) for claim_id in ids]
        if not texts or all(not text for text in texts):
            return {claim_id: [] for claim_id in ids}

        matrix = TfidfVectorizer(ngram_range=(1, 2), min_df=1).fit_transform(texts)
        similarities = cosine_similarity(matrix)
        matches: dict[str, list[SimilarityMatch]] = {claim_id: [] for claim_id in ids}

        for i, source_id in enumerate(ids):
            for j, target_id in enumerate(ids):
                if i == j:
                    continue
                similarity = float(similarities[i, j])
                if similarity >= threshold:
                    matches[source_id].append(SimilarityMatch(source_id, target_id, similarity))

        return {claim_id: sorted(items, key=lambda item: item.similarity, reverse=True)[:top_k] for claim_id, items in matches.items()}
