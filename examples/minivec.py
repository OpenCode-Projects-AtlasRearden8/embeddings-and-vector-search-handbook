"""minivec.py — an ~80-line vector store for small collections (stdlib only).

This is Chapter 3, in code without a single dependency: a vector store is

  1. durable storage of vectors + ids + text + metadata, and
  2. brute-force (exact) cosine top-k search.

That's it below. No index, no server, no dependencies. Use these rules of
thumb from the handbook:
  * under a few hundred thousand vectors, brute force is a *correct*
    engineering choice, not a compromise;
  * one model per collection — the dim check here turns silent model
    mixing into a loud error;
  * persist the chunk text, not just the vector (you'll want to display
    results without re-embedding).
"""

from __future__ import annotations

import json
import math

from toy_embeddings import cosine_similarity


class DimensionError(ValueError):
    """Raised when vectors from mixed sources/dimensions reach one store."""


class MiniVec:
    """In-memory vector store with JSON persistence and metadata filters."""

    def __init__(self, dim: int):
        self.dim = dim
        self._ids: list[str] = []
        self._vecs: list[list[float]] = []
        self._texts: dict[str, str] = {}
        self._meta: dict[str, dict] = {}
        self.metric = "cosine"  # recorded, because it's a property of the store

    # ---------- storage ----------
    def add(self, id_: str, vec: list[float], text: str = "",
            metadata: dict | None = None) -> None:
        if len(vec) != self.dim:
            raise DimensionError(
                f"vector dim {len(vec)} != collection dim {self.dim}; "
                "mixed models in one store produce silently wrong search (Ch. 3)"
            )
        if id_ in self._texts:
            raise KeyError(f"duplicate id {id_!r}")
        self._ids.append(id_)
        self._vecs.append(vec)
        self._texts[id_] = text
        self._meta[id_] = dict(metadata or {})

    def __len__(self) -> int:
        return len(self._ids)

    # ---------- search ----------
    def search(
        self,
        query: list[float],
        k: int = 5,
        where: dict | None = None,
    ) -> list[dict]:
        """Exact cosine top-k. `where` filters on metadata equality, e.g.
        {"section": "Refunds"} — applied *before* ranking (Ch. 2, filters)."""
        if len(query) != self.dim:
            raise DimensionError(f"query dim {len(query)} != collection dim {self.dim}")
        hits = []
        for id_, vec in zip(self._ids, self._vecs):
            meta = self._meta[id_]
            if where and any(meta.get(key) != val for key, val in where.items()):
                continue
            hits.append({
                "id": id_,
                "score": cosine_similarity(query, vec),
                "text": self._texts.get(id_, ""),
                "metadata": meta,
            })
        hits.sort(key=lambda h: h["score"], reverse=True)
        return hits[:k]

    # ---------- persistence ----------
    def save_json(self, path: str) -> None:
        payload = {
            "dim": self.dim,
            "metric": self.metric,
            "items": [
                {"id": id_, "vector": vec, "text": self._texts[id_],
                 "metadata": self._meta[id_]}
                for id_, vec in zip(self._ids, self._vecs)
            ],
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
            # (fine for teaching scale; real local stores use binary formats)

    @classmethod
    def load_json(cls, path: str) -> "MiniVec":
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
        store = cls(dim=payload["dim"])
        store.metric = payload.get("metric", store.metric)
        for item in payload["items"]:
            store.add(item["id"], item["vector"], item["text"], item["metadata"])
        return store


def main() -> None:  # pragma: no cover - teaching demo
    from toy_embeddings import embed

    docs = {
        "refunds-policy": ("We accept returns within 30 days. Items must be unused.",
                           {"section": "Refunds"}),
        "apnea-note": ("Patient apnea event at 0300, resolved without intervention.",
                       {"section": "Nursing"}),
        "bread-recipe": ("No-knead bread: mix flour, water, salt; wait 18 hours.",
                         {"section": "Kitchen"}),
    }
    store = MiniVec(dim=256)
    for id_, (text, meta) in docs.items():
        store.add(id_, embed(text), text, meta)

    for q, filt in [
        ("what is the refund window?", None),
        ("what is the refund window?", {"section": "Nursing"}),
    ]:
        print(f"\nquery: {q!r}" + (f"  where={filt}" if filt else ""))
        for hit in store.search(embed(q), k=2, where=filt):
            print(f"  {hit['score']:5.3f}  {hit['id']:<16} {hit['text'][:50]}")

    store.save_json("/tmp/opencode/minivec-demo.json")
    reloaded = MiniVec.load_json("/tmp/opencode/minivec-demo.json")
    assert reloaded.search(embed("refunds"), k=1)[0]["id"] == "refunds-policy"
    print("\npersist + reload: round-trip OK")


if __name__ == "__main__":
    main()
