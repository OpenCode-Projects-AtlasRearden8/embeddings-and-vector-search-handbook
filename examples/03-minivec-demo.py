"""03-minivec-demo.py — DEMO: the tiny in-memory vector store (Chapter 3).

Runs fully offline with zero dependencies. Demonstrates the full loop:
chunk -> embed (toy) -> store -> cosine top-k with a metadata filter ->
persist to JSON and reload.

Run:  python3 examples/03-minivec-demo.py   (from the repo root)
"""
import sys
import tempfile
import os

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "examples"
sys.path.insert(0, HERE)

from toy_embeddings import embed  # noqa: E402
from minivec import MiniVec  # noqa: E402
from tiny_chunker import chunk_with_metadata, strip_overlap_tail  # noqa: E402

SAMPLE = open(os.path.join(HERE, "sample-doc.md"), encoding="utf-8").read()


def main() -> None:
    chunks = chunk_with_metadata(SAMPLE, max_chars=400, overlap_chars=50)
    print(f"chunked sample-doc.md into {len(chunks)} chunks "
          f"({sum(c['orphan'] for c in chunks)} orphans)")

    store = MiniVec(dim=256)
    for i, c in enumerate(chunks):
        store.add(f"chunk-{i:02d}", embed(strip_overlap_tail(c["text"])),
                  c["text"], {"heading_start": c["starts_with_heading"]})
    print(f"added {len(store)} vectors to the store (dim={store.dim})")

    q = embed("how do I get points back at checkout")
    print("\ntop-3 (no filter):")
    for hit in store.search(q, k=3):
        print(f"  {hit['score']:5.3f}  {hit['id']}  {hit['text'][:60]!r}")

    print("\ntop-3 (where heading_start == True):")
    for hit in store.search(q, k=3, where={"heading_start": True}):
        print(f"  {hit['score']:5.3f}  {hit['id']}  {hit['text'][:60]!r}")

    path = os.path.join(tempfile.gettempdir(), "minivec-demo.json")
    store.save_json(path)
    reloaded = MiniVec.load_json(path)
    assert len(reloaded) == len(store)
    print(f"\npersisted to {path} and reloaded {len(reloaded)} vectors — round-trip OK")


if __name__ == "__main__":
    main()
