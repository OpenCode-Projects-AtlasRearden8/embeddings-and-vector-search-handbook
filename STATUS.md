# STATUS.md — What was built and how it verifies

*Repo: The Embeddings & Vector Search Handbook — Asdale Dynamics, LLC*
*Date: 2026-11-05*

## What was built

A plain-English **theory handbook** on embeddings, similarity search,
vector stores, RAG chunking, and honest "when RAG is overkill" guidance —
designed to *complement* the practical `rag-your-docs-handbook` project
(that one is the build tutorial; this one is the "why it works, what it
costs, when to skip it" companion). Everything is local-first, keyless,
and free of personal data.

### Structure

| Path | Contents |
|---|---|
| `docs/` | 8 markdown files: reading guide + 7 chapters (~8,000 words) |
| `site/` | Static HTML illustration site — `index.html` + `styles.css` + `app.js` (vanilla JS, zero deps, zero network calls) |
| `examples/` | 6 runnable demos + 3 teaching libraries (`toy_embeddings.py`, `tiny_chunker.py`, `minivec.py`) |
| `tests/` | 22 pytest tests covering the three teaching modules |
| `verify.py` | One-command verification checklist (30 checks) |
| `README.md` | Orientation, quick start, links, credit, compatibility notes |
| `LICENSE` | MIT, copyright line: `Copyright (c) 2026 Asdale Dynamics, LLC` (exact) |

### Chapters (docs/)

1. `01-what-embeddings-are.md` — vectors as points on a meaning map; where
   they come from; honest caveats (model-bound coords, no reversibility,
   long-text averaging).
2. `02-similarity-search.md` — cosine/dot/euclidean, top-k, brute force vs
   ANN (and why ANN is irrelevant under ~50k vectors), why "similar ≠
   relevant", a debugging ladder for bad rankings.
3. `03-vector-stores.md` — what stores actually do; deep dives on
   SQLite-vec, Chroma, Ollama embeddings, and OpenAI-compatible local
   endpoints; a temperament-based decision table.
4. `04-chunking.md` — seam-aware cutting, max-chars/overlap knobs, a
   pattern library per text type, summary chunks, metadata filters, a
   symptom→cause→fix field guide.
5. `05-local-toolkit.md` — the full offline stack with code; includes a
   live-verified gotcha: Ollama's native `/api/embeddings` returns
   *un-normalized* vectors while `/v1/embeddings` normalizes (norm 1.0 vs
   ~21 measured locally).
6. `06-when-rag-is-overkill.md` — six decision cases; the Ctrl+F-first
   heuristic; silent failure modes of RAG (confident answers from slightly
   wrong chunks) called out explicitly.
7. `07-cheat-sheet-glossary.md` — seven-sentence summary, command crib,
   dimension table, plain-English glossary, and answers to every chapter's
   "check your understanding" exercises.

### Site (site/)

Interactive, offline illustrations — all hand-rolled canvas math:

- **Meaning map** — click anywhere to drop a query vector; dashed lines
  show a search finding its 3 nearest neighbors across four topic clusters.
- **Cosine playground** — drag two unit arrows; live cosine / dot /
  euclidean readouts with plain-English interpretation (and why cos == dot
  only for unit-length vectors).
- **Close words vs close vectors** — the apnea/babka table showing the two
  keyword-search failure directions embeddings fix.
- **Chunking, live** — a real JS port of the seam-aware chunker with a
  slider; orphan chunks flagged in amber.
- **Decision flow** — 3-question "is RAG overkill?" flow with 5 verdicts
  and a back button.

### Examples (examples/)

| Demo | Runs offline? | What it proves |
|---|---|---|
| `01-word-overlap-embeddings.py` | fully | The toy vectorizer's limits: 'refund window' scores 0.000 vs the refunds doc because the doc says 'returns' — neural models fix exactly this |
| `02-openai-compatible-client.py` | needs a local server (skips calmly) | The portable `/v1/embeddings` wire format; verified live against Ollama |
| `03-minivec-demo.py` | fully | chunk → embed → store → filter → persist round-trip |
| `04-ollama-embeddings.py` | needs Ollama (skips calmly) | Native Ollama API + the normalization gotcha |
| `05-sqlite-vec-demo.py` | needs `sqlite-vec` pip install (skips calmly) | One-file SQLite store; uses real Ollama embeddings when present, toy fallback otherwise |
| `06-chroma-demo.py` | needs `chromadb` pip install (skips calmly) | Chroma collections + cosine space + cleanup |

## How to run it

```bash
cd embeddings-and-vector-search-handbook

# everything at once
python3 verify.py

# pieces
python3 -m pytest tests/ -q          # tests
python3 examples/01-word-overlap-embeddings.py   # zero-dep demo
python3 examples/03-minivec-demo.py              # zero-dep demo
node --check site/app.js              # if node exists (site runs without it)
open site/index.html                  # or double-click

# optional local tools
ollama pull nomic-embed-text && ollama serve
python3 examples/04-ollama-embeddings.py
pip install sqlite-vec    && python3 examples/05-sqlite-vec-demo.py
pip install chromadb      && python3 examples/06-chroma-demo.py
```

## Verification results (this environment)

`python3 verify.py` output, all 30 checks PASS:

- docs: all 8 files present & substantive
- secret-free scan: no key-like patterns anywhere
- python: all 6 examples compile; **22/22 pytest tests pass**; all 6 demos
  run (offline-for-real or skip-and-explain)
- site: files present; every JS-referenced id exists in HTML; `node --check`
  parses app.js
- hygiene: LICENSE carries the exact required copyright line; README
  credits Asdale Dynamics, LLC

Live-tool verification in this environment (beyond the checklist):

- Ollama 0.40.14 was running locally: pulled `nomic-embed-text` (274 MB),
  embedded via **both** `/v1/embeddings` (normalized, norm 1.0000) and
  `/api/embeddings` (norm ≈ 21.4) — the normalization gotcha in Chapter 5 is
  measured fact, not doc folklore.
- SQLite-vec: real 768-dim vectors stored in one `.db` file; cosine
  KNN ranked `refunds` (0.422) before `loyalty` (0.560) before `apnea`
  (0.679) for the query 'how do refunds work' — a meaningful, correct
  ranking (the toy-vector fallback path also works, with honest
  "distances bunch up because word-overlap vectors are orthogonal" notes).
- Chroma: persistent client + cosine space + metadata cleanup verified;
  same meaningful ranking with real embeddings (0.413 vs 0.582).

## Known gaps (honest list)

- **No LLM answering step.** The pipeline demo covers chunk→embed→store→
  search; the final "feed top-k to an LLM" step remains the companion
  handbook's territory (and needs `--embeddings`-capable chat models).
- **Toy embeddings are word-overlap only.** Deliberate (zero deps,
  hand-checkable); real meaning comes from Ollama demos, which need the
  service running. The gap is labeled everywhere.
- **Site canvases need pointer input.** Meaning-map hover/labels and knob
  dragging are mouse/touch only; screen-reader users get the prose
  equivalents in `docs/` but not the interactive layer.
- **SQLite-vec ANN knobs not demonstrated** — brute-force KNN only, which
  is the honest recommendation under ~50k vectors (Chapter 2's table).
- **Python 3.10+ required** (tests use `X | None` syntax).
- **node --check is a syntax check, not a browser test.** The site uses
  standard APIs (canvas 2D, pointer events), but no automated browser
  harness is included. `pytest`/`verify.py` do not cover JS behavior.

## Style guarantees met

- No API keys, no secrets, no personal data (secret-pattern scan enforces).
- Everything runs locally; no remote calls; nothing published/pushed.
- MIT LICENSE with exact required line; README credits Asdale Dynamics, LLC.
- Plain, warm, tested like the friend-it-was-written-for tone throughout.
