# examples/ — runnable companions to the handbook

Everything here runs **offline, with zero API keys**. Scripts prefixed with
a number are demos; `toy_embeddings.py`, `tiny_chunker.py`, and
`minivec.py` are small, teaching-sized libraries the demos (and the
tests in `tests/`) import.

## Which to run when

| Script | Needs | What it shows |
|---|---|---|
| `01-word-overlap-embeddings.py` | nothing | Chapter 1's toy vectorizer and its limits |
| `02-openai-compatible-client.py` | any local `/v1` embeddings server (or nothing — it skips) | Chapter 5's portable wire format |
| `03-minivec-demo.py` | nothing | chunk → embed → store → filter → persist end-to-end |
| `04-ollama-embeddings.py` | [Ollama](https://ollama.com) running locally (or it skips) | Chapter 5's model runner |
| `05-sqlite-vec-demo.py` | `pip install sqlite-vec` (or it skips) | Chapter 5's one-file store |
| `06-chroma-demo.py` | `pip install chromadb` (or it skips) | Chapter 5's batteries-included store |

Optional demos exit with a `[skip]` message and exit code 0 when the
service/dependency isn't present — an intentionally-runnable-but-optional
design, since the toolkit chapters are about tools you may not have yet.

## Run them

```bash
cd embeddings-and-vector-search-handbook   # repo root
python3 examples/01-word-overlap-embeddings.py
python3 examples/03-minivec-demo.py
```

Optional ones:

```bash
ollama pull nomic-embed-text && ollama serve   # first: install Ollama
python3 examples/04-ollama-embeddings.py

pip install sqlite-vec chromadb
python3 examples/05-sqlite-vec-demo.py
python3 examples/06-chroma-demo.py
```

## Honesty notes

* `toy_embeddings.py` is NOT a neural embedding model — it's a hashing
  bag-of-words stand-in so the *mechanics* (vectors, cosine, top-k,
  persistence) run with zero dependencies. What real models add is
  meaning beyond word overlap (Chapter 1).
* `minivec.py` is NOT a production vector store — it's the Chapter 3
  semantics in ~100 lines so you can read every line. For real local
  work: SQLite-vec or Chroma (Chapter 5).
* All test coverage lives in `tests/` — run `python3 -m pytest tests/`
  from the repo root, or `python3 verify.py` for the full checklist.
