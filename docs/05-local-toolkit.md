# Chapter 5 — The Local Toolkit: Your Stack, Your Machine, Your Money (Zero of It)

This chapter pairs with the *companion handbook's* build tutorial. Here we
go a level deeper: what each tool actually is, what it costs you (time,
complexity, disk), and which to pick for which temperament. All four
options need **no cloud account, no API key, no ongoing cost**, and none
of them send your documents anywhere.

## The mental model: two different jobs

Keep these separate or everything gets confusing:

- **An embedding model** turns text into vectors. (A *program* has to run
  it.)
- **A vector store** keeps vectors and searches them.

You need exactly one of each. The four tools below cover both jobs:

| Job | Options in this chapter |
|---|---|
| Run an embedding model | Ollama, any OpenAI-compatible endpoint |
| Store + search vectors | SQLite-vec, Chroma |
| Both at once | Chroma's built-in default embedding model (convenient, slightly less controllable) |

## 5.1 Ollama — run the models

```bash
# one-time setup
ollama pull nomic-embed-text       # 274 MB, 768-dim steady workhorse
# optional larger model
ollama pull mxbai-embed-large      # ~670 MB, 1024-dim

# then it just... runs. Every call hits localhost:11434
curl http://localhost:11434/api/embeddings -d '{
  "model": "nomic-embed-text",
  "prompt": "refund window is 30 days"
}'
```

- **Disk:** a few hundred MB per embedding model. Trivial.
- **Speed:** hundreds of chunks per minute on a laptop CPU; seconds on a GPU.
  Because embedding is a *one-time* cost per document, people over-worry
  about this.
- **Gotcha:** vectors are 768-dim. Your store must be created for that
  dimension. If you later switch models, new vectors join a *new* collection.
- **Normalization gotcha (verified live in `examples/04-`):** Ollama's
  *native* endpoint (`/api/embeddings`) returns un-normalized vectors,
  while the OpenAI-compatible one (`/v1/embeddings`) returns unit-length
  ones. Cosine search is unaffected by scale; dot-product search is not.
  Pick one endpoint and stay consistent (Chapter 2).
- **The same install serves LLMs too** (`ollama run llama3.2` etc.), which is
  why Ollama is the natural center of a local stack.

## 5.2 SQLite-vec — vectors in a file

```bash
pip install sqlite-vec
```

```python
import sqlite3, sqlite_vec
import json

db = sqlite3.connect("my-corpus.db")
db.enable_load_extension(True)
sqlite_vec.load(db)
db.enable_load_extension(False)

db.execute("""
  CREATE VIRTUAL TABLE chunks USING vec0(
    chunk_id TEXT PRIMARY KEY,
    embedding float[768],
    doc TEXT,
    heading TEXT
  )
""")

db.execute("INSERT INTO chunks(chunk_id, embedding, doc, heading) VALUES (?, ?, ?, ?)",
    ("c1", json.dumps([0.1, 0.2]), "handbook.md", "Refunds"))
db.commit()

# nearest neighbors for a query vector `q`
rows = db.execute("""
  SELECT chunk_id, doc, heading, distance
  FROM chunks
  WHERE embedding MATCH ? AND k = 5
  ORDER BY distance
""", (json.dumps(q),)).fetchall()
```

- **Storage model:** everything — embeddings *and* your ordinary columns —
  sits in `my-corpus.db`. Back it up with `cp`. Version it, or don't. Email
  it. That freedom is the appeal.
- **Dimension is fixed per table** (`float[768]`) — a real protection; you
  *cannot* insert a 1024-dim vector into a 768 table, so model mixing fails
  loudly instead of silently. That's a feature.
- **When to pick it:** you like SQL, you want one artifact to back up, your
  corpus is a few hundred thousand chunks or fewer, and you don't want yet
  another server process chugging in the background.

## 5.3 Chroma — fastest from zero to searching

```bash
pip install chromadb
```

```python
import chromadb

client = chromadb.PersistentClient(path="./my-chroma-data")
col = client.get_or_create_collection("handbook")

col.add(
  ids=["c1"],
  documents=["We accept returns within 30 days."],
  embeddings=[[0.1, 0.2, 0.3]],
  metadatas=[{"doc": "handbook.md", "heading": "Refunds"}],
)

res = col.query(
  query_embeddings=[[0.1, 0.2, 0.3]],
  n_results=3,
  where={"doc": "handbook.md"},
)
```

- **Offers a server mode too** (`chroma run`) when you want a stable long-
  lived process instead of library-embedded access. Both are localhost.
- **Strengths:** the API above is basically usage-complete. Built-in
  `where` filters. Ships with an *optional* default embedding model so you
  can try search before choosing an embedding model (it downloads the
  model the first time, which is a surprise the first time).
- **Watch-outs:** bigger dependency tree; occasional API surface changes
  between versions (pin it); fewer low-level knobs by design.
- **When to pick it:** rapid prototyping, notebooks, or when metadata
  filtering is the center of your project and you want it done for you.

## 5.4 OpenAI-compatible endpoints — the flexibility seam

Several local servers all speak the same `/v1/embeddings` JSON dialect:

| Server | Serves embedding models | Endpoint |
|---|---|---|
| Ollama | yes, via `ollama pull` | `http://localhost:11434/v1/embeddings` |
| LM Studio | yes, GUI model picker | `http://localhost:1234/v1/embeddings` |
| llama.cpp `llama-server` | yes, with an appropriate GGUF | `http://localhost:8080/v1/embeddings` |
| vLLM | yes, with packing | `http://localhost:8000/v1/embeddings` |

A single tiny client (see `examples/02-openai-compatible-client.py`) covers
all of them:

```python
import urllib.request, json

def embed_texts(texts, base_url="http://localhost:11434/v1",
                model="nomic-embed-text"):
    body = json.dumps({"input": texts, "model": model}).encode()
    req = urllib.request.Request(f"{base_url}/embeddings", data=body,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read())
    return [d["embedding"] for d in data["data"]]
```

- **Why bother:** you can swap servers without touching your app. Develop
  against LM Studio's GUI, deploy on a vLLM box, test everything with
  Ollama — same client code. When someone says "OpenAI SDK" in a RAG
  tutorial, you can often follow along by pointing that SDK at a local
  `base_url` instead.
- **No keys locally:** most local servers ignore the `Authorization`
  header entirely. Your code passes none.

## Choosing — a decision table by *temperament*

| If you say | Use |
|---|---|
| "I want one file I can back up" | SQLite-vec + Ollama |
| "I want the least code possible" | Chroma + (its default or Ollama) |
| "I already know SQL" | SQLite-vec |
| "I want my client to survive tool changes" | Ollama/OpenAI-compatible + SQLite-vec |
| "I just want to *understand* the pieces first" | Pure Python toy store in `examples/09_*` — no dependencies at all |

## The canonical local stack, end to end

```
┌──────────────┐    ┌───────────────┐    ┌────────────────┐    ┌───────────────┐
│  your docs   │ →  │    chunker    │ →  │  Ollama model  │ →  │   vectors     │
│ (md, txt...) │    │  (seam-aware) │    │ nomic-embed    │    │ + metadata    │
└──────────────┘    └───────────────┘    └────────────────┘    └───────┬───────┘
                                                                      │
        ┌─────────────────────────────────────────────────────────────┘
        ▼
┌────────────────────┐    ┌─────────────────────┐    ┌────────────────┐
│  SQLite-vec query  │ →  │      top-k chunks   │ →  │ LLM (Ollama)   │
│   (cosine, SQL)    │    │  (text + citations) │    │ (optional step)│
└────────────────────┘    └─────────────────────┘    └────────────────┘
```

Every arrow in that diagram is a step you can debug by printing. No step
touches the internet.

## Cost summary — the whole table

**$0.** One-time disk: ~300 MB for Ollama + model, ~100s MB for Python deps.

## Check your understanding

1. You switch from `nomic-embed-text` to `mxbai-embed-large` and add new
   chunks into the *same* SQLite-vec table. What happens, and why?
2. Why does the OpenAI-compatible format matter *for local tools*?
3. When is Chroma's "client/server" mode worth it over the embedded mode?
