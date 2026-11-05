"""Tests for the toy hashing-vectorizer (Chapter 1 mechanics)."""

from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "examples"))

import toy_embeddings as te  # noqa: E402


def test_same_text_same_vector():
    assert te.embed("refund window is 30 days") == te.embed("refund window is 30 days")


def test_unit_length_and_dimension():
    v = te.embed("we accept returns within 30 days", dim=256)
    assert len(v) == 256
    assert abs(math.sqrt(sum(x * x for x in v)) - 1.0) < 1e-9


def test_identical_text_has_cosine_one():
    a = te.embed("no knead bread mixes flour and water")
    b = te.embed("no knead bread mixes flour and water")
    assert te.cosine_similarity(a, b) > 0.999999


def test_disjoint_texts_have_zero_cosine():
    a = te.embed("alpha beta gamma delta epsilon")
    b = te.embed("omega psi chi tau lambda")
    assert te.cosine_similarity(te.embed("zeta a b c"), te.embed("q w e r")) >= 0.0
    # vocabularies chosen to be fully disjoint, so hashing gives 0 overlap here
    a = te.embed("alpha beta gamma delta")
    b = te.embed("omega psi chi tau")
    assert te.cosine_similarity(a, b) == 0.0


def test_model_mismatch_raises_not_silent():
    a = te.embed("refund", dim=256)
    b = te.embed("refund", dim=128)
    try:
        te.cosine_similarity(a, b)
    except ValueError as exc:
        assert "dimension" in str(exc).lower()
    else:
        raise AssertionError("comparing 256-dim with 128-dim must fail loudly")


def test_top_k_orders_by_score():
    docs = {
        "bread": "no knead bread mixes flour water and salt",
        "refund": "we accept returns within 30 days for unused items",
        "coffee": "espresso pulls in twenty five seconds",
    }
    ids = list(docs)
    vecs = te.embed_batch([docs[i] for i in ids])
    hits = te.top_k(te.embed("when do I get my money back for returns"),
                    list(zip(ids, vecs)))
    assert len(hits) == len(ids)
    # word overlap ranks refund first; ordering is best-first
    assert [h[0] for h in hits] == sorted(ids, key=lambda i: -hits[[x[0] for x in hits].index(i)][1])
    assert hits[0][1] >= hits[-1][1]
    assert any(h[0] == "refund" for h in hits), hits
    scores = [h[1] for h in hits]
    assert scores == sorted(scores, reverse=True)


def test_null_vector_defensive():
    a = te.embed("hello", dim=128)
    assert te.cosine_similarity([0.0] * 128, a) == 0.0
    assert te.cosine_similarity([0.0] * 128, [0.0] * 128) == 0.0
