"""Deterministic feature-hashing 'embedding' used when no OPENAI_API_KEY is configured.

This is a legitimate (if low-quality) fallback, not a mock: it hashes each lowercase word
of the input into one of EMBEDDING_DIM buckets and L2-normalizes the resulting bag-of-
words vector, so cosine similarity still rewards word overlap. It lets the knowledge base
work out of the box in local development; configure OPENAI_API_KEY for real semantic
(meaning-based, not just word-overlap-based) search.
"""
import hashlib
import math
import re

from app.models_provider.embeddings import EMBEDDING_DIM, EmbeddingProvider

_WORD_RE = re.compile(r"[a-zA-Zäöüß0-9]+")


def _hash_embed(text: str) -> list[float]:
    vector = [0.0] * EMBEDDING_DIM
    for word in _WORD_RE.findall(text.lower()):
        bucket = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16) % EMBEDDING_DIM
        vector[bucket] += 1.0
    norm = math.sqrt(sum(v * v for v in vector))
    if norm == 0:
        return vector
    return [v / norm for v in vector]


class FakeEmbeddingProvider(EmbeddingProvider):
    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [_hash_embed(text) for text in texts]
