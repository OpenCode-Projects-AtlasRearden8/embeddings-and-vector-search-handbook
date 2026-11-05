# Chapter 7 — Cheat Sheet & Glossary

## The seven sentences of the whole book

1. An embedding is a list of numbers standing for a text's *meaning*, set up
   so similar meanings = nearby vectors (Ch. 1).
2. Similarity = geometry: cosine of the angle between vectors; always treats
   the result as *a ranking*, not a truth score (Ch. 2).
3. A vector store is just: "keep these lists, answer which is closest," plus
   filters and persistence — one local model, one collection (Ch. 3).
4. Chunking (cutting at seams, keeping context, 400–1200 chars, 10–20%
   overlap) is where quality lives; bad chunks sink even great models (Ch. 4).
5. The free local stack — Ollama (model) + SQLite-vec or Chroma (storage),
   optionally via OpenAI-compatible endpoints — is fully offline and costs
   $0 (Ch. 5).
6. RAG is overkill far more often than your feed suggests: if Ctrl+F solves
   it, solve it with Ctrl+F (Ch. 6).
7. Retrieval is a *sourcing tool*, not an oracle. LLMs paraphrase; you read
   the sources and decide (Ch. 2, 4, 6).

## Command crib

```bash
# Embedding model (Ollama) — one-time
ollama pull nomic-embed-text

# Sanity check it's alive
curl -s http://localhost:11434/api/embeddings \
  -d '{"model":"nomic-embed-text","prompt":"test"}' | head -c 200

# SQLite-vec
pip install sqlite-vec

# Chroma
pip install chromadb
```

## The dimension table

| Model | Dims | Local? | Notes |
|---|---|---|---|
| all-MiniLM-L6-v2 | 384 | ✔ via sentence-transformers | Classic small baseline |
| nomic-embed-text | 768 | ✔ Ollama | Our default |
| mxbai-embed-large | 1024 | ✔ Ollama | Larger, stronger |
| text-embedding-3-small | 1536 | ✘ (paid API) | For comparison; not used here |

## Glossary (plain English, short)

- **ANN (approximate nearest neighbor):** an index that finds *almost*-nearest
  fast, trading small accuracy loss for speed. Irrelevant below ~50k vectors.
- **Chunk:** a piece of a document, sized for embedding and retrieval.
- **Chunking:** cutting text into chunks at natural seams.
- **Collection:** a named group of vectors in a store — all from one model.
- **Cosine similarity:** 1 → same direction/same-ish meaning; −1 → opposite.
- **Dimensionality:** how many numbers in each embedding (a box's size).
- **Distance metric:** the way a store measures "closeness" — cosine/dot/
  euclidean. Must match what your model was trained for (usually cosine).
- **Embedding:** text → vector.
- **Embedding model:** the neural net doing the turning.
- **FTS (full-text search):** keyword searching over text — SQLite ships a
  great version called FTS5, good idea pre-RAG.
- **HNSW:** the common ANN graph structure. "Search by hopping shortcuts."
- **Inverted index:** the data structure under keyword search. Opposite
  philosophy: exact word matches, exact results, no model.
- **Metadata filter:** a rule (source, date, tags) applied before/with
  similarity, fixing arbitrary results.
- **RAG (retrieval-augmented generation):** put top-k chunks in an LLM's
  context so it answers with real citations.
- **Top-k:** answer only with the k nearest chunks (k=5 is a fine default).
- **Vector store:** a database for vectors + nearest-neighbor search.
- **Overlap (chunking term):** the deliberate duplication of the tail of
  chunk N into chunk N+1.

## Answers to the "Check your understanding" prompts

**Ch. 1:** (1) Both texts sit near each other in the model's map, because it
learned "apnea" and "stopped breathing" co-occur in similar clinical narrative
contexts. (2) Different models are different maps: coordinates have no shared
meaning — 0.3 in one space is not 0.3 in another. (3) A 30-page doc's one
vector is the *average* of 30 pages of unrelated topics, which erases all
useful detail — the whole point of chunking.

**Ch. 2:** (1) Length tracks verbosity/emphasis (noise); direction tracks
meaning (signal). Dot = cosine when both vectors are normalized. (2) No.
(3) Euclidean-based (or you've got the interpretation inverted — either way,
check before comparing).

**Ch. 3:** (1) No — the store only does *storage + search*; if the chunks and
queries were bad, no store fixes the neighborhoods. (2) Because periods
without text (or text without IDs) mean re-embedding or losing sources at
exactly the worst moment. (3) No. A million is when HNSW starts buying you
time; 800 is a for-loop.

**Ch. 4:** (1) It cuts sentences mid-thought, so each chunk embeds as broken
narrative; and the constant size ignores where topics begin. (2) Because even
a good seam occasionally cuts a thought that *continues*; overlap catches the
"genre" of straddling thoughts. (3) Question + answer as one chunk, plainly.
(4) Because the embedding input and the chat prompt are *different
artifacts*; you design them independently (and say so in your README).

**Ch. 5:** (1) Insert fails: dimension mismatch (768 vs 1024). If you disable
that check, you get conflated maps and *silently wrong* search — that's why
per-table dim is your friend. (2) It means client code survives server
changes (Ollama ↔ LM Studio ↔ vLLM) untouched, code once, follow along with
tutorials. (3) When you want it running as a service shared by several
processes/notebooks — the "always on" pattern.

**Ch. 6:** (1) "Paste it." (2) When the query's words live in the doc (the
word-shaped vs meaning-shaped distinction: one specific keyword beats any
embedding). (3) Keyword's failure is honest (empty output = you moved on);
RAG's failure is a confident wrong paragraph dressed up as an answer.
