# Reading Guide

*The Embeddings & Vector Search Handbook — Asdale Dynamics, LLC*

This is the theory companion to the practical *RAG Your Docs Handbook*. That book
shows you how to wire up a retrieval pipeline; this one explains what is happening
underneath — in plain English, the way a friend would explain it, without assuming
you have a math degree or a data center.

## The chapters, in one sentence each

| Chapter | File | In one sentence |
|---|---|---|
| 1. What Embeddings Actually Are | [01-what-embeddings-are.md](01-what-embeddings-are.md) | Text becomes a list of numbers, and similar text gets a similar list. |
| 2. Similarity Search | [02-similarity-search.md](02-similarity-search.md) | Finding "nearest" points in space, and why "close" is not the same as "correct." |
| 3. Vector Stores | [03-vector-stores.md](03-vector-stores.md) | A database that stores lists of numbers and answers "which are closest?" fast. |
| 4. Chunking | [04-chunking.md](04-chunking.md) | Cutting documents into pieces so retrieval can find the *right piece*, not a haystack. |
| 5. The Local Toolkit | [05-local-toolkit.md](05-local-toolkit.md) | SQLite-vec, Chroma, Ollama embeddings, and OpenAI-compatible endpoints — all free, all on your machine, no API keys. |
| 6. When RAG Is Overkill | [06-when-rag-is-overkill.md](06-when-rag-is-overkill.md) | An honest decision guide: sometimes Ctrl+F beats the whole pipeline. |
| 7. Cheat Sheet & Glossary | [07-cheat-sheet-glossary.md](07-cheat-sheet-glossary.md) | The whole book compressed, plus a glossary you can actually read. |

## How to read it

- **New to all of this?** Read straight through, chapters 1 → 7. Chapter 1 is
  the foundation; everything else leans on it.
- **Have built a RAG demo already?** Skim chapters 1–2, then spend your time
  on chapters 4 (chunking — where most quality lives) and 6 (when it's overkill).
- **Just want the toolcake?** Chapter 5 + the cheat sheet. But come back to
  chapter 2 — the cosine similarity section is where intuition pays rent.

## Companion site

The `site/` folder contains a static HTML page with interactive illustrations
(toy-embedding playground, cosine similarity visualizer, chunking viewer).
Open `site/index.html` in any browser. No server, no account, no key.

## A promise

Nothing in this repo calls the internet. No environment variables, no API
keys, no telemetry. Every example runs on your machine, and every test runs
offline.
