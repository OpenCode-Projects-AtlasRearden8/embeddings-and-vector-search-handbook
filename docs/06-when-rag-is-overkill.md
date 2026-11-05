# Chapter 6 — When RAG Is Overkill (Read This Before Building Anything)

This is the most valuable chapter in the book, and the shortest in spirit:
*most of the time, you don't need RAG.* Building embeddings-and-vector
-search for a corpus that fits in Ctrl+F is bringing a forklift to move a
ham sandwich. Let's find out which is which.

## Six decision cases, concretely

### Case 1 — "I have one document, a few dozen pages"
**Paste it.** Modern LLMs have big context windows. If the whole corpus
fits, or even half fits, a retrieval layer is pure overhead. The LLM sees
*everything*, so nothing is lost to bad chunking. Use RAG when:
- it doesn't fit, or
- your context charges per token and you want to be economical (but with
  local models, you don't).

### Case 2 — "I need to find a file, not a fact"
**Ctrl+F / `grep` / OS search.** If you're finding *"which file has the
word 'invoice'"* — keyword search is the tool, and embeddings are not.

### Case 3 — "I need FAQs, a glossary, structured entries"
**Ctrl+F within that file.** FAQ data is (question → answer) pairs, and
keyword search is nearly perfect on them: query words appear in the
question, byte for byte. This is the word-shaped/meaning-shaped split that
Chapter 2's "similar is not relevant" warned about.

### Case 4 — "I want to know what topics are in my corpus"
**Print the titles.** No, really. Files named `tax-fraud.md`,
`health-review.md`, `complaint-2024-11.md`, `book-toc.md` already answer
this. Save the embeddings for when titles stop working — a few tables of
title+summary go further than you'd think. If you truly need grouping,
doing it by hand, chunk by chunk, is feasible up to surprisingly large
corpora, and you will *read* what you have.

### Case 5 — "I want a searchable personal notes system"
**SQLite FTS (full-text search)** or even SQLite + `LIKE` queries. If your
notes are your own text, you wrote them in your own style and can search
them in your own words. Full-text search is:
- exact and deterministic,
- honest, in a way embeddings are not (empty results = no match; nothing
  *hallucinated*),
- indexable, cheap, and inspectable.
- Then add embeddings only when your vocabulary drifts — when you start
  thinking "the note used different words than my query" — which is the
  first honest signal to reach for them.

### Case 6 — "The docs are huge, scattered, and I don't know their structure"
**Honestly, this is the first real RAG case.** This is also the
correct frame for most people's initial project: a pile of PDFs from the
county clerk, a business's policy manual, chat exports, or 9 years of
scatterbrained notes. RAG shines when:
- no keyword query you could write reliably maps to where the answer lives;
- questions are open-ended, phrased naturally, and might require
  combining two or three different documents;
- the corpus keeps growing, and you can't re-write an index by hand.

## The one-line heuristic

> **Try to answer your question with Ctrl+F first. If you can, no embeddings.**

## The "honest costs of RAG" people skip

It's not free. Every RAG pipeline adds:
- **Maintenance surface** — model versions, chunk boundaries, restart
  bugs. Real things that break.
- **Silent failure modes** — when keyword search fails you see it; when
  RAG retrieves a *slightly wrong* chunk, the LLM answers *confidently*
  from it. You get heart-burningly plausible lies. This is genuinely the
  worst property of the whole technology and Chapter 2 explains why scores
  will lie to you if you trust them.
- **Debugging complexity.** "Is the answer wrong because the chunk was
  wrong, or because the LLM misread a right chunk?"

You accept these costs because you *need* the capability. Don't accept
them because a tutorial did.

## When RAG is *not* enough (and what helps instead)

1. **You need exact answers.** (Ex: "what is my SSN?" — you should probably
   not be answering this from approximate retrieval.
2. **Cross-document deduction.** "Given my total travel spend and my
   tax records, what's my tax deduction?" — That's an agent + a
   spreadsheet, not retrieval, at any quality level worth doing.
3. **You need *certified* answers** — for clinical or legal or business
   decisions where "we found an adjacent paragraph" being wrong is
   unacceptable. LLMs paraphrase; paraphrase is the enemy here.
   Use exact retrieval + show the doc + preserve breadth.
4. **Multi-step research tasks.** You need agentic workflows that can
   branch, not a simple "top-5 search" — that's a *different* class of
   system and layering RAG under an agent is one case; a pure "retrieve
   and stuff" is another.

## Excuses people use to skip the decision, and the truth

| Excuse | Truth |
|---|---|
| "RAG is cool / interviewers like it" | Do it for its merits only. It ships you bugs. |
| "It might be handy someday" | Build the simplest thing that works now. Add RAG when you have a case for it. |
| "It's only 40 lines of code" | 40 lines to *run* and about 4 hours to run *well*. Chunking (Ch. 4) is not in the 40. |

## The practical middle ground worth learning

If you do decide RAG *is* right, 80/20 it:

1. **Chunk with seams + overlap** (Ch. 4).
2. **Store vectors + metadata in one file** (SQLite-vec).
3. **Retrieval with cosine + a metadata filter where possible.**
4. **Retrieve top-5, and *show them* in your UI.** RAG's most underrated
   value is giving you sources to read — a "for further reading" feature,
   not a truth machine.
5. **Don't try: rerankers, query rewriting, hybrid BM25+vector, RAGAS
   eval, parent-document retrieval.** Those all add real value; they also
   add real complexity. Get the boring pipeline *boringly correct* first.
6. **Keep a README that says which model embedded which collection.**

## Check your understanding

1. Your mom asks for a chatbot over her 20-page family recipe doc. What
   does Ch. 6 say? (Three words.)
2. When does *keyword search* beat retrieval, structurally, and why?
3. Which is worse — keyword search returning "no results," or RAG
   returning a *nearly* right chunk? Why?
