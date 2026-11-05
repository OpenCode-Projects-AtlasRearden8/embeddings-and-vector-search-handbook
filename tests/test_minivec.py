"""Tests for minivec, the ~80-line Chapter 3 store."""

from __future__ import annotations

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "examples"))

import minivec as mv  # noqa: E402
import toy_embeddings as te  # noqa: E402

DOC = "we accept returns within 30 days for unused items"
OTHER = "the espresso machine pulls a twenty five second shot"


def make_store() -> mv.MiniVec:
    s = mv.MiniVec(dim=256)
    v1 = te.embed(DOC)
    v2 = te.embed(OTHER)
    s.add("refunds", v1, DOC, {"section": "Refunds"})
    s.add("coffee", v2, OTHER, {"section": "Kitchen"})
    return s


def test_add_and_len():
    assert len(make_store()) == 2


def test_search_returns_nearest():
    s = make_store()
    hits = s.search(te.embed(DOC), k=2)
    assert hits[0]["id"] == "refunds"
    assert hits[0]["score"] > 0.999
    assert hits[1]["id"] == "coffee"


def test_where_filter():
    s = make_store()
    hits = s.search(te.embed(DOC), k=2,
                    where={"section": "Kitchen", "nonexistent-meta": True})
    assert all(h["id"] != "refunds" for h in hits)


def test_where_filter_that_matches_nothing_returns_empty():
    s = make_store()
    assert s.search(te.embed(DOC), where={"section": "Nope"}) == []


def test_mixed_dimensions_fail_loudly():
    s = mv.MiniVec(dim=256)
    s.add("a", te.embed("alpha beta", dim=256), "alpha beta")
    try:
        s.add("b", te.embed("gamma delta", dim=128), "gamma delta")
    except mv.DimensionError:
        pass
    else:
        raise AssertionError("mixed dims must raise, not blend silently")
    try:
        s.search(te.embed("query example here", dim=128))
    except mv.DimensionError:
        pass
    else:
        raise AssertionError("mismatched query dim must rise loudly too")


def test_duplicate_id_raises():
    s = make_store()
    try:
        s.add("refunds", te.embed(DOC), DOC)
    except KeyError:
        pass
    else:
        raise AssertionError("duplicate ids must raise")


def test_persistence_round_trip():
    s = make_store()
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "store.json")
        s.save_json(path)
        payload = json.load(open(path, encoding="utf-8"))
        assert payload["dim"] == 256
        assert payload["metric"] == "cosine"
        # the text travels with the vector (Ch. 3: display without re-embedding)
        assert any(i["text"] == DOC for i in payload["items"])
        reloaded = mv.MiniVec.load_json(path)
        assert len(reloaded) == len(s)
        h1 = s.search(te.embed(DOC), k=1)[0]
        h2 = reloaded.search(te.embed(DOC), k=1)[0]
        assert h1["id"] == h2["id"]
        assert abs(h1["score"] - h2["score"]) < 1e-12
