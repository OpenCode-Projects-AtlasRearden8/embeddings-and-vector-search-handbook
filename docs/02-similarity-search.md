# Chapter 2 — Similarity Search: What "Close" Means

Once text is a point in space, the search question becomes geometric:
**which of my points are nearest to this query point?** This chapter is
about how "nearest" is measured, what shortcuts are (and aren't), and the
failure modes that turn a slick demo into a lying one.

## The three ways to measure closeness

### 1. Cosine similarity — the default

Cosine similarity asks: *do these two arrows point in the same direction?*
It ignores arrow length entirely, comparing only the angle.

```
cos_sim(a, b) = (a · b) / (|a| × |b|)
```

- Range: **−1 to +1.** 1 = same direction, 0 = unrelated-ish, −1 = opposite.
- Why everyone uses it: embedding *length* is noisy (longer or more emphatic
  text can produce a longer vector for model-dependent reasons), while
  *direction* is where the meaning lives. Cosine throws away the noise.
- Most embedding models are even trained so their outputs are **normalized**
  (length exactly 1). Then cosine similarity is identical to the plain dot
  product, which is why you'll see libraries use dot product without
  explaining anything. Same thing.

### 2. Dot product — cosine without the dividing

```
dot(a, b) = a[0]*b[0] + a[1]*b[1] + ...
```

If vectors are pre-normalized, dot product and cosine give identical rankings.
If not, dot product quietly rewards *long* vectors, which is rarely what you
want. Rule of thumb: normalize your vectors, then it doesn't matter which you
use — but know which you're using, because when results look weird, this is
the first place to check.

### 3. Euclidean distance — plain straight-line distance

```
dist(a, b) = sqrt((a[0]-b[0])² + (a[1]-b[1])² + ...)
```

(If both vectors are normalized, *ranking by euclidean distance* matches
cosine ranking, because on a unit sphere, closest-vs-farthest angle is the
same thing. But don't take that on faith for un-normalized vectors.)

| Metric | Use when | Watch out for |
|---|---|---|
| Cosine | Mixed-length text, default choice, most models trained for it | Nothing much; it's the sane default |
| Dot | Normalized vectors; speed-critical loops | Un-normalized vectors rewarding long text |
| Euclidean | Clustering, some image models | Length bias on un-normalized data |

**Practical rule: pick cosine, verify with cosine, don't mix metrics in the
same store.** A metric is a property of the search call, and some vector
stores bake it in at collection-creation time and never let you change it.

## How many neighbors: top-k

A similarity search almost always returns a *list*: the top-k nearest
neighbors, sorted. You set k.

- k = 5 is a common default for RAG (Chapter 4 explains why not radically
  higher or lower).
- The scores come with each hit. A good store returns the *distance*, and you
  need to know whether high = similar (cosine similarity) or high = far
  (euclidean distance). Confusing these two is a rite of passage for every
  RAG developer. It's fine. We've all done it.

## Exact search vs approximate search (ANN)

Here's a thing most tutorials gloss over: for **small collections**, you
don't need anything fancy.

| Collection size | What you need |
|---|---|
| Under ~50,000 vectors | Brute force. Compare your query against every vector. Python can do ~100k comparisons a second; a few hundred docs is instant |
| 50k – a few million | Approximate methods start to matter |
| Really big | ANN indexes are table stakes (see below) |

**Brute force is a feature, not a failure.** It is exact, deterministic,
debuggable, takes zero setup, and your assertions in tests behave nicely.
Our example in `examples/` does exactly this with pure Python.

### Approximate Nearest Neighbor (ANN) — the idea

For millions of points, checking every one is slow. ANN indexes trade a
little *accuracy* for a lot of *speed*:

- **IVF-style** (inverted file): cluster the space into cells; at query time,
  only look inside the few nearest cells.
- **HNSW** (hierarchical navigable small world): build a graph of
  shortcuts — "highway tiers" — so search hops across the space instead of
  walking every street. This is what SQLite-vec, Chroma, and friends use by
  default.

The trade you're accepting: an ANN index might miss the true nearest
neighbor a small percentage of the time. Parameters exist to tune recall
(Chroma/SQLite-vec quotes have knobs; when you're small, turn them up or
just use brute force).

**When you should care: honestly, later.** If you're under a few hundred
thousand vectors, none of this matters. Don't tune ANN knobs before you have
the problem.

## Why top-k retrieval is not "the answer"

The single biggest misconception: *similarity score = relevance*. Wrong at
least four ways:

1. **Similar is not the same as relevant.** The query "how do I reset my
   password?" will be highly similar to *irrelevant* docs about password
   policies, password manager features, or password resets for a different
   product. Ranked lists here are starting points for an LLM to reason over,
   not final answers.
2. **One query, one shot.** A single embedding of the query might miss the
   right doc because of phrasing. Multi-query retrieval (run several
   paraphrases, merge results) helps; it's cheap.
3. **Scores aren't calibrated.** A cosine of 0.82 in one collection means
   nothing across collections. Treat scores as *rank order*, not grades.
4. **Filters exist for a reason.** Metadata filtering (by date, source,
   department) before or after similarity search often fixes ranking
   problems more cleanly than any vector trickery.

## Debugging a bad ranking

When retrieval returns garbage, work this ladder from cheap to expensive:

1. **Look at the raw neighbors.** Print the top-10 texts + scores and *read
   them*. Is the query embedding landing in a weird neighborhood?
2. **Whittle the query.** Shorten it. Remove filler words. LLMs to do
   "query expansion" exist, but 80% of the time a shorter query wins.
3. **Check chunk quality.** Nine times out of ten, the document chunks are
   the problem (next chapter), not the similarity math.
4. **Check the metric and normalization.** Dot vs cosine, ±inverted
   distance interpretation.
5. **Only then** consider: re-embed, try another model, or add a reranker.

## Check your understanding

1. Why does cosine ignore vector length — and when is dot product the same thing?
2. At 20,000 vectors, do you need ANN? (Look at the table again.)
3. A store hands back distance scores where *lower = better*. Did you get
   cosine similarities or euclidean distances?
