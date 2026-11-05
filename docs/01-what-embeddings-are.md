# Chapter 1 — What Embeddings Actually Are

## The elevator version

An **embedding** is a list of numbers that represents the *meaning* of a piece
of text, arranged so that pieces of text with similar meanings get lists that
are close together.

That's it. That's the whole trick. Everything else in this book is variations
on "how do we compare lists of numbers and find the ones that are close?"

## A concrete example

Take these three sentences:

1. *"My dog loves peanut butter."*
2. *"I can't believe he ate the whole jar of peanut butter — the dog did."*
3. *"Quarterly revenue exceeded projections due to favorable bond spreads."*

When you send sentences 1 and 2 through an embedding model, the two output
vectors will be *near* each other in high-dimensional space. Sentence 3 will
land somewhere far away, even though it shares zero "important words" with the
others. In old-school keyword search, sentence 1 and sentence 3 are unrelated
(no shared terms) and sentence 2 is only weakly related (shares "peanut
butter"). An embedding model can rank them the way a human would, because it
was trained on enormous amounts of text and learned patterns like *"sentences
about dogs eating human food tend to co-occur near each other."*

## What the numbers actually look like

You don't read the numbers. They don't have human-readable meaning individually.
A modern embedding for one sentence looks like:

```
[ -0.0372,  0.1109, -0.2001,  0.0583, ..., 0.0271 ]
```

Typical sizes:

| Model | Dimensions | Notes |
|---|---|---|
| `all-MiniLM-L6-v2` | 384 | Small, fast, very common baseline |
| `nomic-embed-text` (Ollama) | 768 | Good local workhorse |
| `text-embedding-3-small` (OpenAI) | 1536 | Proprietary; needs API key — mentioned for comparison, not used in this book |
| `bge-base-en-v1.5` | 768 | Strong free local option |

Why so many dimensions? Because meaning is *complicated*, and the model uses
each dimension as a faint vote for some concept. No single dimension means
"dog." Instead, thousands of subtle patterns combine so that dog sentences
cluster together. Think of it like a song: no single sample of an MP3 contains
"the chorus" — the meaning lives in the *pattern* across all of them.

## The geometry that matters

The most useful mental picture: imagine every sentence is a point on a map.
That's literally what a vector is — coordinates. And here is the map's golden
rule:

> **Distance ≈ dissimilarity. Close points ≈ similar meaning.**

- "credit card dispute" and "chargeback complaint" → neighbors.
- "credit card dispute" and "how to prune tomatoes" → far apart.
- The whole embedding space is a map with billions of "neighborhoods" of meaning:
  a legal-arguments district, a cooking-recipes district, a football-tactics
  district — and when you zoom out, they all cluster into larger boroughs:
  "everyday leisure," "technical writing," "hard manual work."

Two practical consequences:

1. **You can find things without knowing their exact words.** Searching for
   "patient stopped breathing" can find a note that says "apnea event during
   sternotomy recovery" — because their coordinates are near.
2. **You can cluster, browse, and deduplicate**, not just search. Points that
   sit together *are* a topic.

## Where embeddings come from

Embedding models are neural networks trained by showing them billions of text
pairs and asking: *should these be near or far?* The training signals come from
places like:

- **Co-occurrence**: sentences appearing near each other in the same document
  tend to be related.
- **Contrastive pairs**: duplicate questions from forums (should be near),
  unrelated posts (should be far).
- **Hard negatives**: pairs that *look* similar on the surface but aren't —
  like "Type 1 diabetes" vs "Type 2 diabetes." Good models are trained to push
  these apart, which is exactly the discrimination a naive keyword search
  fails at.

## The honest caveats (please actually read this part)

Embeddings are useful *approximations*, not magic meanings-bytes:

- **No model knows your world.** A general-purpose model may place "sheet
  metal gauge 12" and "gauge 14" closer together than a metalworker would
  want — the model never worked in an auto body shop. Domain-specific models
  exist, but for most local projects the general model is fine and the fix is
  better *chunk text* (Chapter 4), not a fancier model.
- **Numbers are model-specific.** You cannot compare a vector from model A
  with a vector from model B. Ever. They're different maps. When you switch
  models, you re-embed everything.
- **Reversibility is zero.** You cannot turn a vector back into text. The
  map keeps the neighborhood, not the house.
- **There are boundaries.** Very short texts ("?)", typos, IDs like
  "SKU-88231") embed poorly. Very long texts get *averaged* — a single vector
  for a 30-page PDF squashes away most of the content. This is why the next
  three chapters exist.

## What embeddings are *for*

Every use of embeddings is one of four verbs:

1. **Search** — "find me the chunks nearest to this query."
2. **Group** — "cluster my notes; what topics exist?"
3. **Compare** — "is this new complaint a duplicate of one of these 400?"
4. **Feed** — "hand the closest chunks to an LLM so it can answer with
   receipts." (This is RAG, Chapter 4's whole world.)

If your task isn't one of those four, embeddings are probably the wrong tool.

## Check your understanding

1. Why can embedding search find "stopped breathing" via "apnea event"?
2. Why must all vectors in one store come from the same model?
3. Why does a 30-page document make a bad single embedding?
   *(Hint: what does "one point per document" throw away?)*

Answers are in the cheat sheet, Chapter 7.
