# Chapter 4 — Chunking: Where RAG Quality Actually Lives

*This is the most important chapter in the book. Read it slower than the others.*

## The problem chunking solves

You can't meaningfully embed a 40-page PDF in one vector — one number-blob for
forty pages is an average, and averages erase detail (Chapter 1). And even if
you could, retrieving the *whole document* to answer "what was the refund
window?" is like sending your entire filing cabinet to answer one question.

So: slice the doc into pieces, embed each piece, retrieve the few *best
pieces*. Those pieces are **chunks**. The quality of your whole RAG system is
bounded by the quality of your chunks. Bad chunks = the LLM confidently
answers from the wrong paragraph. There is no embedding model good enough to
fix bad chunk boundaries.

## Cuts on seams, not hydrogen atoms

The amateur move is to cut text every N characters. It's cheap but it cuts
sentences and paragraphs in half — and half a sentence embeds as nonsense.

The professional move: cut at the **natural seams** of the text — paragraph
breaks, headings, list items, table rows. Modern chunkers (ours included) do
this by *never cutting mid-sentence* unless a single sentence is huge, and
*coalescing* small pieces into comfortably-sized chunks so no chunk is a
12-word orphan.

## The two knobs

1. **MAX-CHARS (the classic name is "chunk size")** — how big a chunk is
   allowed to be. Expressed in characters here because that's stable across
   LLM tokenizers; libraries like LangChain and LlamaIndex usually count
   tokens instead.
   - Too small → chunks with no context ("shall be refunded within") —
     pointless.
   - Too big → chunks about many topics at once, so they're only
     *moderately* similar to everything — irrelevant.
   - Sweet spot for most text: **400–1200 characters**, i.e., chatty
     paragraphs. Appendix or highly structured data might want smaller;
     editorial/long-form might want bigger.
2. **OVERLAP-CHARS** — when you must cut (doc longer than MAX-CHARS chunk can
   handle), have the next chunk begin a bit *inside* the end of the previous
   one. 10-20% overlap of MAX-CHARS is standard; this keeps a sentence that
   straddles a border *whole* in at least one chunk.

## The pattern library (what actually happens in the field)

Different text types want different strategies; a real corpus is a
smorgasbord.

1. **Plain prose.** Paragraphs. Coalesce to MAX-CHARS. Trivial and correct.
2. **Markdown / docs / books-with-headings.** Keep the heading *with* its
   body. A chunk that starts `## Refunds\nWe accept returns within 30 days`
   carries its own topic; a chunk that starts mid-list does not. Adding
   heading breadcrumbs ("Nursing Handoff > End of Shift > Medication
   Reconciliation") as a prefix is one of the highest-ROI retrieval tricks
   invented — the embedding is enriched with organizing context the honest
   text lacked on its own.
3. **Tables.** Do not split rows across chunks if you can help it. Each
   table (or logically grouped set of rows) is one chunk. Tables embed poorly
   as prose, so a parallel *text rendering of the same facts* as a second
   chunk is standard practice ("SKU 88231: refund window 30 days; restocking
   15%").
4. **Q&A / FAQ docs.** Question + its answer = one chunk. Never split.
5. **Code.** Functions/classes are the natural seam. Blank-line-based
   heuristics that ignore syntax break code badly; structure-aware splitters
   are worth it here more than anywhere.
6. **Conversational logs / transcripts.** Turn boundaries. A chunk per few
   exchanges, with speaker labels preserved ("Nurse: ...", "Patient: ...").

## Cohesion: the idea that separates good chunkers from bad

Two sentences belong in the same chunk when they *continue each other's
thought*. Pairs like "However," / "Therefore," / "in other words" / "That
is why" are *liaison* sentences — they are meaningless without their
antecedents, so a chunk boundary should basically never fall right after
one. Conversely, boundary is cheap before a heading, a new `# section`, a
list bullet, or a line that opens a fresh topic.

Our example chunker implements this by coalescing prose greedily and only
cutting on hard seams. You don't need something fancy; you need something
that honors seams 98% of the time. We chose boring and predictable so you
can verify it by eye.

## What gets embedded: text, and *only* text — which text?

A classic mistake is assuming the text you *embed* must be the exact text
you *show the LLM*. Those can differ, deliberately:

- **Prefix breadcrumbs** (heading path) help the *embedder* understand the
  chunk but can be stripped before the LLM sees it (the LLM usually sees
  larger context window and can get context from elsewhere). It's fine to
  embed an *augmented* view and store/retrieve the plain version — just do
  it deliberately and record what you did.
- **Summary chunks:** for each document, add a chunk whose text is a
  hand-written or LLM-written summary of the whole document. It becomes
  "the shallowest point of entry" for vague queries like "what is this doc
  about?" — which pure paragraph chunks fail at.
- **Multi-embedded variants:** some pipelines embed the same content twice,
  once as raw text and once as a rewritten "hypothetical question it
  answers." More vectors to store — better recall on question-shaped
  queries. Costs embedding time; helps retrieval. Start without it.

## Size sanity-check table (empirically)

| Corpus type | Reasonable MAX-CHARS | Rationale |
|---|---|---|
| Nursing/clinical-style notes, step lists | ~400 | One procedure per chunk, needs tightness |
| General documentation / help-center articles | 800 | A section ≈ one chunk |
| Books, essays, long-form prose | 1000–1500 | Paragraphs are meatier; more coherence |
| Code | Syntax-driven (function-level) | Even a "small" function that's split is useless |

These are starting points, not laws. Tune by *reading what comes back*, not
by the numbers. If chunks as retrieved look incomplete when you print
them, that's the ground truth, not a metric.

## Metadata: your quiet superpower

Every chunk should carry metadata: doc title, section, page (if known), date,
source path, hash. Reason: retrieval failures are often fixed by
*filtering* ("but only from the 2026 handbook"), not by better vectors.
Chapter 2 promised that filters fix rankings more reliably than model swaps;
this is where you make it possible.

## Common failure modes (a field guide)

| Symptom | Likely cause | Fix |
|---|---|---|
| Retrieved chunks start mid-sentence, end mid-thought | Cutting at fixed chars | Seam-based chunking + overlap |
| Answer mixes up topics from different sections | One section per chunk violated; heading context lost | Heading-prefixed chunks |
| "What is the refund window?" retrieves the table but with unparseable meaning | Raw table text | Add a text rendering of the table as a sibling chunk |
| Question about one doc returns another doc's chunks | No doc-level metadata filtering (or doc summary chunk missing) | Metadata + summary chunk |
| Everything scores ~0.35 and ranks feel arbitrary | Chunks have no topical concentration | Sizes too large; cut smaller and re-embed |

## Check your understanding

1. Why does "cut every 500 characters" hurt embedding quality? (Two reasons.)
2. Why is overlap needed *even with* seam-honored boundaries?
3. Your corpus is a 12-page FAQ. What flat-out obvious chunking wins?
4. Why might you embed the *heading path* even though you'd strip it before
   showing it to the LLM?
