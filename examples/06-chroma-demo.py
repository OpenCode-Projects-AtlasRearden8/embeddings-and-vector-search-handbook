"""06-chroma-demo.py — TOY TOOL: the fastest path to local vector search.

Optional. Requires `pip install chromadb`. Degrades calmly otherwise
(by design).

Run:  python3 examples/06-chroma-demo.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

try:
    import chromadb
except ImportError:
    print("[skip] chromadb not installed. To try it:")
    print("  pip install chromadb")
    print("Nothing here needs an API key or network.")
    sys.exit(0)

from toy_embeddings import embed  # noqa: E402


def embed_openai_compatible(
    texts: list[str],
    base_url: str = "http://localhost:11434/v1",
    model: str = "nomic-embed-text",
) -> list[list[float]] | None:
    """Real neural embeddings from any local /v1 server; None if unavailable."""
    import urllib.error
    import urllib.request
    try:
        body = json.dumps({"input": texts, "model": model}).encode()
        req = urllib.request.Request(
            f"{base_url.rstrip('/')}/embeddings",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read())
        vecs = [item["embedding"] for item in payload["data"]]
        if not vecs or len({len(v) for v in vecs}) != 1:
            return None
        return vecs
    except (urllib.error.URLError, urllib.error.HTTPError, ConnectionError,
            OSError, json.JSONDecodeError, KeyError, ValueError):
        return None


def get_vecs(texts: list[str]) -> tuple[list[list[float]], str]:
    """Ollama-first, toy-fallback — with an honest label either way."""
    real = embed_openai_compatible(texts)
    if real:
        return real, f"Ollama nomic-embed-text (real neural embeddings, dim {len(real[0])})"
    return [embed(t) for t in texts], "toy word-overlap vectorizer (weak but honest)"


def main() -> None:
    path = os.path.join(tempfile.gettempdir(), "embeddings-handbook-chroma")
    client = chromadb.PersistentClient(path=path)
    collection = client.get_or_create_collection(
        "handbook-demo",
        metadata={"hnsw:space": "cosine"},
    )
    collection.delete(where={}) if collection.count() else None

    docs = {
        "refunds": "We accept returns within 30 days. Items must be unused.",
        "loyalty": "Every dollar spent earns one point; hundred points is $5 credit.",
        "apnea": "Patient apnea event at 0300, resolved without intervention.",
    }
    ids = list(docs)
    vecs, source = get_vecs([docs[i] for i in ids])
    collection.add(
        ids=ids,
        documents=[docs[i] for i in ids],
        embeddings=vecs,
        metadatas=[{"section": i} for i in ids],
    )

    query = "how do refunds work"
    query_vec, _ = get_vecs([query])
    res = collection.query(
        query_embeddings=[query_vec[0]],
        n_results=2,
        include=["documents", "distances", "metadatas"],
    )

    print(f"[ok] embeddings from: {source}")
    print(f"[ok] collection 'handbook-demo' at {path}")
    print(f"top-2 nearest to {query!r} (cosine distance, lower = closer):")
    for id_, dist, meta, doc in zip(
        res["ids"][0], res["distances"][0], res["metadatas"][0], res["documents"][0]
    ):
        print(f"  dist {dist:6.3f}  {id_} ({meta.get('section')})  {doc[:55]!r}")
    if "toy word-overlap" in source:
        print("(toy note: distances bunch at 1.0 — the differentiating power")
        print("  of neural models is invisible here. Try with Ollama: it")
        print("  partitions meaning instead of just matching words.)")

    client.delete_collection("handbook-demo")
    print("(cleaned up demo collection)")


if __name__ == "__main__":
    main()
