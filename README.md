# The Embeddings & Vector Search Handbook

*Plain-English theory for embeddings, similarity search, vector stores, and
RAG chunking — with cheap, local, keyless options.*

**By Asdale Dynamics, LLC** — the AI-education publishing company behind
Dylan Asdale's *The Massive AI Manual*. This handbook is the theory
companion to the practical *rag-your-docs-handbook* project: that one
shows you how to wire a pipeline together; this one explains what is
actually happening underneath, the way a friend would. It deepens the
concepts; it does not duplicate the build tutorial.

## What's inside

| Path | What it is |
|---|---|
| `docs/` | The handbook: 7 chapters, plain English, honest caveats |
| `docs/README-reading-guide.md` | Start here — the reading order in one page |
| `site/index.html` | Static illustrated site (open in a browser; zero network) |
| `examples/` | Runnable demos. Core ones need **no dependencies and no keys** |
| `tests/` | Pytest suite for every teaching module |
| `verify.py` | One-command verification checklist |

## The chapters

1. **What embeddings actually are** — vectors as points on a meaning map,
   where they come from, and the honest caveats (`docs/01-what-embeddings-are.md`)
2. **Similarity search** — cosine vs dot vs euclidean, top-k, and why
   approximate search (ANN) doesn't matter until ~50k vectors (`docs/02-similarity-search.md`)
3. **Vector stores** — what they really do, plus deep dives on the free
   local options: SQLite-vec, Chroma, Ollama, OpenAI-compatible endpoints
   (`docs/03-vector-stores.md`)
4. **Chunking** — seam-aware cuts, size/overlap knobs, pattern library,
   failure modes. Where RAG quality actually lives (`docs/04-chunking.md`)
5. **The local toolkit** — the full offline stack, code-first (`docs/05-local-toolkit.md`)
6. **When RAG is overkill** — six decision cases and the one-line
   heuristic: *try Ctrl+F first* (`docs/06-when-rag-is-overkill.md`)
7. **Cheat sheet & glossary** — the whole book compressed (`docs/07-cheat-sheet-glossary.md`)

## Quick start

```bash
# read the handbook
$EDITOR docs/README-reading-guide.md

# play with the illustrations (no server, no account, no key)
open site/index.html          # macOS — or just double-click it

# run the teaching demos (zero dependencies beyond Python 3.10+)
python3 examples/01-word-overlap-embeddings.py
python3 examples/03-minivec-demo.py

# optional: the local AI tools (all keyless, all offline)
ollama pull nomic-embed-text && ollama serve
python3 examples/04-ollama-embeddings.py
pip install sqlite-vec && python3 examples/05-sqlite-vec-demo.py
pip install chromadb   && python3 examples/06-chroma-demo.py
```

## Verify everything

```bash
python3 verify.py      # tests + syntax checks + demo smoke tests
```

or individually: `python3 -m pytest tests/ -q` and `node --check site/app.js` (if you have Node; the site runs fine without).

## Promises this project keeps

- **No API keys, no secrets, no accounts.** Nothing calls the internet
  except truly-optional model downloads you always run yourself.
- **No personal data.** Sample texts are invented (FAQ pages, bread
  recipes, toy nursing notes — the latter purely educational, never
  medical advice).
- **Local-first.** Core tracks run on any machine with just Python.
- **Honest.** Chapter 6 exists mostly to talk you *out* of building RAG
  when Ctrl+F would serve you better.

## Compatibility notes

- Handbook examples target **Python 3.10+** (matches `sqlite-vec`/`chromadb`).
- The site needs only a modern browser; works fully offline.
- Ollama 0.4+ recommended for the optional demos (`--embeddings` server
  flag or the checkpoints listed in `docs/05-local-toolkit.md`).
- OpenAI-compatible endpoints: works with Ollama `:11434/v1`,
  LM Studio `:1234/v1`, vLLM `:8000/v1`, and llama-server `:8080/v1`.

## License & credit

MIT — see `LICENSE`. © 2026 Asdale Dynamics, LLC.

Part of the beginner-friendly AI library from Asdale Dynamics, LLC:
books, guides, and practical tools explained like a friend would —
plain English, step by step, never condescending. Hub: dylanasdale.github.io.
