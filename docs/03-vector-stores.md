# Chapter 3 — Vector Stores: What They Actually Do

Strip away the marketing and a **vector store** is a small thing:

> It stores vectors, and answers: *given this query vector, which stored
> vectors are closest?* Plus a bit of bookkeeping.

That's the core loop. Everything else — clients, distance metrics, metadata
filters, persistence, server processes — is convenience.

## The three jobs a vector store does

1. **Store** vectors durably (ideally with a link back to the original text
   and any metadata).
2. **Search** — nearest-neighbor queries, using an exact or approximate
   method (Chapter 2).
3. **Filter/retrieve** — optionally combine similarity with metadata rules
   like `{"where": {"source": "clinical-notes", "year": {"$gte": 2024}}}`.

A vector store is *not* responsible for chunking, embedding, or answering
questions. Those happen before and after. When a demo conflates them, it's
harder to debug — keep the layers separate.

## Consistency rules worth tattooing somewhere

- **One model, one collection.** Vectors in a single collection must all
  come from the same embedding model and have the same number of dimensions.
  Mixing models in one collection is the #1 way to produce confidently
  wrong search results. If you switch models: new collection (or snapshot +
  delete + re-embed).
- **Persist everything, including chunk text.** Vector + ID + metadata +
  the chunk text itself. If you store only vectors, you'll be re-embedding
  every time you want to display a result.
- **Embed at write time, not query time, for bulk.** But queries must embed
  at query time, obviously. Keep a record of which model version produced
  each batch. (Write the model name in your metadata: `model: nomic-embed-text`. Cheap insurance.)

## The cheap local options (deep dive)

These are the tools the book actually uses. They're all free, local-first,
and need no API keys.

### SQLite-vec — the "one file" choice

- **What it is:** an extension for SQLite (`pip install sqlite-vec`, or just
  load the extension library) that adds vector columns and search to an
  ordinary SQLite database. Your data lives in one `.db` file. That's the
  whole storage story.
- **Strengths:**
  - Single-file storage; copy it, back it up, email it to yourself.
  - SQLite is the world's most deployed database — boring in the best way.
  - No server process. `import sqlite3; conn.execute("load vec0")` — done.
  - Perfect size: a few hundred thousand vectors is comfortable.
  - Combines beautifully with normal SQL joins over your metadata:
    `SELECT ... FROM vec_items JOIN docs USING(doc_id) WHERE docs.status='active'`
- **Watch-outs:**
  - Provides brute-force (`KNN`) plus optional ANN index depending on
    version; check your version's docs.
  - It's an extension — confirm it loads cleanly on your machine the first time.
- **Pick it when:** you want a corpus that lives beside your other data,
  you're comfortable with a little SQL, and you don't want a background
  server.

### Chroma — the "developer experience" choice

- **What it is:** a purpose-built local vector database with a friendly
  Python/JS API. Runs either **embedded** (a library call, data in a local
  folder) or **client/server** (a localhost process you start).
- **Strengths:**
  - Very short path from idea to working: `collection.add(ids, embeddings, documents, metadatas)` —
    done.
  - Metadata filtering built in and easy (`where={"topic": "x"}`).
  - It can use an "embedding function" abstraction, so if you're doing the
    *opposite* of this book you can swap models easily. This book does
    embedding via Ollama (below) rather than Chroma's built-in default model.
  - Persistence is a directory — snapshot the directory, ship it.
- **Watch-outs:**
  - Heavy by comparison; the dependency tree is bigger.
  - API has churned over versions. Pin your version.
  - Fewer knobs (deliberately). It's opinionated.
- **Pick it when:** you want the shortest possible code and filterable
  local search, and don't mind a heavier dependency.

### Ollama embeddings — the "local model broker"

- **What it is:** Ollama is a local program for running open-weight LLMs and
  embedding models on your own machine. `ollama pull nomic-embed-text` gets
  you a good embedding model; `ollama pull mxbai-embed-large` gets a bigger
  one. Then any HTTP call to `http://localhost:11434/api/embeddings` returns
  vectors. No cloud. No key. No rate limit.
- **Strengths:**
  - Runs fully offline after the (one-time) download.
  - Comfortably fast: embedding a few thousand chunks is a coffee break,
    not a weekend.
  - Same tool serves your *LLM* later — one install powers the whole
    pipeline.
- **Watch-outs:**
  - Model quality varies; `nomic-embed-text` is the steady default.
  - CPU-only machines are slower. It still works; run it once, cache the
    vectors, forget it.
  - You must embed with the same model forever for that collection. Write
    the model name in your metadata (can't say this too often).
- **Pick it when:** you want zero external services and you control the
  hardware. This is the default choice throughout the handbook's examples.

### Any OpenAI-compatible endpoint — the "your server, your rules" option

- **What it is:** a *wire format* that many local inference servers speak:
  `POST /v1/embeddings` with a JSON body like `{"input": [...], "model":
  "..."}`, returning vectors. Ollama, LM Studio, llama.cpp's built-in
  `llama-server`, vLLM — all of them can serve this exact protocol.
- **Why it matters:** your *client code* stops caring which tool is behind
  it. Point at a different `base_url` (e.g. `/v1`), same code, same JSON.
  You can develop against LM Studio, run tests against Ollama, and — if you
  ever want to — swap in a hosted provider without rewriting anything.
- **No keys in local mode:** most local servers ignore auth entirely, which
  is the point. Your key config stays local; nothing in this repo does so.
- **Watch-outs:**
  - Timeout behavior and error messages vary between servers; write your
    client to fail loudly.
  - Respect model naming differences (`nomic-embed-text` in Ollama vs
    whatever LM Studio names the same weights).
- **Pick it when:** you want flexibility at the seams, or you're already
  running one of those servers for chat.

## Side-by-side

| | SQLite-vec | Chroma | Ollama (embeddings) | OpenAI-compatible endpoints |
|---|---|---|---|---|
| What it is | Embedding storage (in SQLite) | Database with local API/Ops | Runs the embedding *models* | A wire format many servers speak |
| Storage | One `.db` file | A local directory | n/a (model on disk) | n/a |
| Server process | None | Optional | Yes (local) | Yes (local) |
| Best size | 10s – 100k+ vectors | 10s – millions | every size — it's the model | every size |
| Filtering power | SQL joins, very flexible | Built-in `where` filters | — | — |
| Code complexity | Low-medium (SQL) | Very low | Low (HTTP) | Low (HTTP) |
| Network | None | Local only | Local only | Local only |
| Our default use | Persistence layer of choice for plain projects | Fastest prototype | Where our vectors come from | Fallback / flexibility layer |

They're not competing. The canonical local stack looks like:

```
your docs → chunker → Ollama embeds chunks → vectors live in
SQLite-vec (or Chroma) → search → top-k chunks → LLM (maybe also Ollama)
```

## What about "just use it in memory"?

For tiny jobs, honestly, yes: store vectors in a Python list or numpy array
and call `cosine_similarity` yourself. Our `examples/09_*` does exactly this.
The store is a list; the "index" is a for-loop. When the corpus is under a
few thousand chunks, that's not a hack — it's the correct engineering. The
moment you want persistence, filtering, or to survive process restarts,
move into SQLite-vec or Chroma.

## Red flags worth naming

- **The collection's model isn't written down anywhere.** Future-you will
  re-embed with a different model and nothing will warn you.
- **Vectors stored, text not.** You'll re-embed to show results. Boring pain.
- **A distance metric set at creation and never recorded.** Store which
  metric you chose, in a README inside your data folder if you must.
- **The store is the product.** It isn't. The chunking (Ch. 4) and the
  answering are where quality lives; the store is plumbing.

## Check your understanding

1. A friend's search returns nonsense. They switch from Chroma to
   SQLite-vec. Do you expect the results to improve? Why not?
2. Why must the vector and the chunk text travel through every part of the
   pipeline together?
3. Your corpus is 800 chunks. Do you need an ANN index?
