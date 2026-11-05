"""05-sqlite-vec-demo.py — TOY TOOL: vectors in a plain SQLite file.

Optional. Requires `pip install sqlite-vec` AND a machine where the
extension loads. Degrades calmly to a skip-message otherwise (by design).

Run:  python3 examples/05-sqlite-vec-demo.py
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile

try:
    import sqlite_vec
except ImportError:
    print("[skip] sqlite-vec not installed. To try it:")
    print("  pip install sqlite-vec")
    print("Then re-run. Nothing here needs an API key or network.")
    sys.exit(0)

from toy_embeddings import embed  # noqa: E402

DB_PATH = os.path.join(tempfile.gettempdir(), "embeddings-handbook-demo.db")
DIM = 256


def embed_ollama_local(texts: list[str], model: str = "nomic-embed-text") -> list[list[float]] | None:
    """Try the local OpenAI-compatible endpoint (unit-normalized vectors).

    Returns None if no server/model is available (Caller falls back to the
    toy vectorizer — a teaching stand-in, honestly labeled in the output)."""
    import urllib.error
    import urllib.request
    try:
        body = json.dumps({"input": texts, "model": model}).encode()
        req = urllib.request.Request(
            "http://localhost:11434/v1/embeddings",
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


def create_db(path: str) -> sqlite3.Connection:
    if os.path.exists(path):
        os.remove(path)
    db = sqlite3.connect(path)
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)
    db.execute(
        f"CREATE VIRTUAL TABLE chunks USING vec0("
        f"  chunk_id TEXT PRIMARY KEY,"
        f"  embedding float[{{}}] distance_metric=cosine,"
        f"  section  TEXT"
        f")".format(DIM)
    )
    return db


def main() -> None:
    global DIM  # noqa: PLW0603 - teaching demo rebinds dim based on vector source
    docs = {
        "refunds": "We accept returns within 30 days. Items must be unused and in original packaging.",
        "loyalty": "Every dollar spent earns one point. One hundred points is a five-dollar credit.",
        "apnea": "Patient apnea event at 0300, resolved without intervention.",
    }
    texts = list(docs.values())
    real_vecs = embed_ollama_local(texts)
    if real_vecs:
        dim = len(real_vecs[0])
        source = f"Ollama nomic-embed-text (real neural embeddings, dim {dim})"
        using_ollama = True
    else:
        real_vecs = [embed(t) for t in texts]
        dim = DIM
        source = f"toy word-overlap vectorizer (dim {dim}; weak but honest)"
        using_ollama = False
    DIM = dim  # the table is created for the dimension actually in use

    db = create_db(DB_PATH)
    try:
        for chunk_id, vec in zip(docs, real_vecs):
            db.execute(
                "INSERT INTO chunks(chunk_id, embedding, section) VALUES (?, ?, ?)",
                (chunk_id, json.dumps(vec), chunk_id),
            )
        db.commit()

        if using_ollama:
            query_vec = json.dumps(embed_ollama_local(["how do refunds work"])[0])
        else:
            query_vec = json.dumps(embed("how do refunds work"))
        rows = db.execute(
            """
            SELECT chunk_id, distance
            FROM chunks
            WHERE embedding MATCH ? AND k = 3
            ORDER BY distance
            """,
            (query_vec,),
        ).fetchall()

        print(f"[ok] embeddings from: {source}")
        print(f"[ok] stored {len(docs)} vectors of dim {dim} in {DB_PATH}")
        print("top-3 nearest to 'how do refunds work' (cosine distance, lower = closer):")
        for chunk_id, dist in rows:
            print(f"  dist {dist:6.3f}  {chunk_id}")
        if not using_ollama:
            print("(toy note: word-overlap vectors are so sparse that distances")
            print("  bunch up — that bunching is the differentiating power")
            print("  neural embedding models add. Nothing is broken.)")
        print("\nOne .db file, zero servers. Back it up with `cp`.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
