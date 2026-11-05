"""toy_embeddings.py — a no-dependency "embedding" for teaching.

*A real embedding model is a neural network trained on billions of texts.
This module is NOT that.* It is a hashing bag-of-words vectorizer with
L2-normalized TF weights, built only to make the *mechanics* of
Chapter 1-2 (vectors, cosine similarity, top-k) concrete and runnable
offline. Its "knowledge" is exactly one thing: shared words. That is the
baseline that real models improve on, and the honest framing for the
handbook.

Everything here is deterministic: hashing uses crc32 (stable across runs
and Python versions), so the same text always yields the same vector.
"""

from __future__ import annotations

import math
import re
import zlib

DEFAULT_DIM = 256

_WORD_RE = re.compile(r"[a-z0-9']+")


def tokenize(text: str) -> list[str]:
    """Lowercased word tokens. Set to False to keep case if you prefer."""
    return _WORD_RE.findall(text.lower())


def embed(text: str, dim: int = DEFAULT_DIM) -> list[float]:
    """Text -> a length-`dim` L2-normalized vector (hashing trick).

    Each token votes for one index (crc32(token) % dim); votes accumulate;
    the vector is scaled to length 1 so cosine == dot product (Chapter 2).
    """
    vec = [0.0] * dim
    tokens = tokenize(text)
    for tok in tokens:
        vec[zlib.crc32(tok.encode("utf-8")) % dim] += 1.0
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


def embed_batch(texts: list[str], dim: int = DEFAULT_DIM) -> list[list[float]]:
    return [embed(t, dim) for t in texts]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine of the angle between two vectors (Chapter 2)."""
    if len(a) != len(b):
        raise ValueError(
            "dimension mismatch: vectors from different embedding models "
            "must never be compared (Chapter 3)"
        )
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def top_k(query: list[float], items: list[tuple[str, list[float]]], k: int = 5) -> list[tuple[str, float]]:
    """Brute-force nearest neighbors: (id, cosine score), best first.

    This is the whole "vector store" loop for small collections —
    see minivec.py for the persistence/filtered version.
    """
    scored = [(name, cosine_similarity(query, vec)) for name, vec in items]
    scored.sort(key=lambda t: t[1], reverse=True)
    return scored[:k]


def main() -> None:  # pragma: no cover - teaching demo
    docs = {
        "refunds-policy": "We accept returns within 30 days. Items must be unused.",
        "apnea-note": "Patient apnea event at 0300, resolved without intervention.",
        "bread-recipe": "No-knead bread: mix flour, water, salt; wait 18 hours.",
    }
    vecs = embed_batch(list(docs.values()))
    ids = list(docs)
    for query_text in [
        "what is the refund window?",
        "patient stopped breathing overnight",
        "how long do I let dough rest?",
    ]:
        print(f"\nquery: {query_text!r}")
        for name, score in top_k(embed(query_text), list(zip(ids, vecs))):
            bar = "#" * int(score * 40)
            print(f"  {score:5.3f} {bar:<40} {name}")
    print("\n(Word-overlap only — real embedding models replace exact words with meaning. Chapter 1.)")


if __name__ == "__main__":
    main()
