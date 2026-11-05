"""01-word-overlap-embeddings.py — DEMO: the toy vectorizer from Chapter 1.

Runs fully offline with zero dependencies. Shows the "word-overlap"
embedding and its honest limits: it ranks by shared words, which is the
baseline real neural embedding models improve on.

Run:  python3 examples/01-word-overlap-embeddings.py
"""
import sys

sys.path.insert(0, "examples")

from toy_embeddings import embed, top_k, embed_batch  # noqa: E402

DOCS = {
    "refunds-policy": "We accept returns within 30 days. Items must be unused.",
    "apnea-note": "Patient apnea event at 0300, resolved without intervention.",
    "bread-recipe": "No-knead bread: mix flour, water, salt; wait 18 hours.",
}


def main() -> None:
    ids = list(DOCS)
    vecs = embed_batch([DOCS[i] for i in ids])
    queries = [
        "what is the refund window?",          # shares ZERO key words with the refunds doc
        "patient stopped breathing overnight",  # shares "patient" with the apnea note
        "how long do I let dough rest?",        # shares zero words with the bread doc
    ]
    for query_text in queries:
        print(f"query: {query_text!r}")
        for name, score in top_k(embed(query_text), list(zip(ids, vecs))):
            bar = "#" * int(score * 40)
            print(f"  {score:5.3f} {bar:<40} {name}")
        print()
    summary = """What to notice (this IS the lesson, not a bug):

  * 'refund window' scores 0.000 against the refunds policy — the doc says
    'returns', not 'refund', so pure word overlap misses a true match.
  * 'stopped breathing' ranks the apnea note FIRST, but only via the shared
    word 'patient' — accidental, not understanding.
  * 'dough rest' scores 0.000 against the bread recipe ('rest' vs 'wait').

Chapter 1: real neural embedding models replace exact-word overlap with
learned meaning, fixing exactly these misses. This toy exists so every
number above is checkable by hand.
"""
    print(summary)


if __name__ == "__main__":
    main()
