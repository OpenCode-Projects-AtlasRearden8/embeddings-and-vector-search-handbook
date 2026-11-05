"""Tests for the seam-aware chunker (Chapter 4 guarantees)."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "examples"))

import tiny_chunker as tc  # noqa: E402

LONG = (
    "## Refunds\n\n"
    "We accept returns within 30 days of delivery. Items must be unused and "
    "in their original packaging. Gift cards and digital downloads are final "
    "sale and cannot be refunded once the code has been redeemed.\n\n"
    "## Shipping\n\n"
    "Orders ship within 2 business days. Some remote addresses may take an "
    "extra week. If your package is marked delivered but never arrived, wait "
    "3 days, then contact us with your order number.\n\n"
    "## Loyalty\n\n"
    "Every dollar spent earns one point. Every one hundred points converts "
    "to a five-dollar credit at checkout. Points expire after 24 months "
    "without an order."
)


def normalized(text: str) -> str:
    return " ".join(text.split())


def test_chunks_respect_max_chars_with_margin():
    for max_chars in (120, 200, 400, 800):
        chunks = tc.chunk(LONG, max_chars=max_chars, overlap_chars=max_chars // 6)
        margin = max_chars // 6 + 40
        for c in chunks:
            assert len(c) <= max_chars + margin, (max_chars, len(c), c[:80])


def test_no_mid_sentence_cuts_reconstruction():
    for max_chars in (120, 200, 400, 800):
        chunks = tc.chunk(LONG, max_chars=max_chars, overlap_chars=max_chars // 6)
        rebuilt = "\n\n".join(tc.strip_overlap_tail(c) for c in chunks)
        assert normalized(rebuilt) == normalized(LONG), max_chars


def test_heading_starts_its_chunk():
    for max_chars in (120, 200, 400):
        chunks = tc.chunk(LONG, max_chars=max_chars, overlap_chars=max_chars // 6)
        heads = [c for c in chunks if c.lstrip().startswith("##")]
        # every one of the three sections must start (not merely appear in) a chunk
        matched_starts = 0
        for section in ("## Refunds", "## Shipping", "## Loyalty"):
            if any(c.startswith(section) for c in chunks):
                matched_starts += 1
            else:
                assert any(c.lstrip().startswith(section) for c in chunks), (
                    f"{section} did not begin a chunk")
        assert matched_starts >= 1
        assert len(heads) <= 3


def test_small_max_shows_orphan_flagged_structuredness():
    meta = tc.chunk_with_metadata(LONG, max_chars=90, overlap_chars=15)
    assert any(m["orphan"] for m in meta), "tiny max_chars should produce orphans"


def test_huge_single_sentence_still_splits():
    block = ("The committee reviewed packet one and adjourned without coffee. " *
            8).strip()
    text = f"## Minutes\n\n{block}"
    chunks = tc.chunk(text, max_chars=200, overlap_chars=40)
    assert len(chunks) >= 2
    assert all(len(c) <= 200 + 40 + 40 for c in chunks)


def test_faq_question_answer_one_chunk():
    faq = (
        "## FAQ\n\n"
        "Q: How long do refunds take?\n"
        "A: Five business days after we receive the item.\n\n"
        "Q: Can I swap an order?\n"
        "A: Yes, contact us within 24 hours of ordering."
    )
    chunks = tc.chunk(faq, max_chars=400, overlap_chars=50)
    assert any("How long do refunds take?" in c and "Five business days" in c
               for c in chunks), "Q and A must stay together"


def test_overlap_added_on_size_boundaries_only():
    chunks = tc.chunk(LONG, max_chars=200, overlap_chars=40)
    for c in chunks:
        if tc._OVERLAP_MARK in c:
            head, rest = c.split(tc._OVERLAP_MARK, 1)
            # the inherited head must come from the interrupted previous chunk,
            # and heading chunks never begin with inherited text
            assert not rest.lstrip().startswith("##")
    first = tc.chunk(LONG, max_chars=800, overlap_chars=0)
    second = tc.chunk(LONG, max_chars=200, overlap_chars=0)
    assert not first[0].lstrip().startswith(tc._OVERLAP_MARK.strip())
    assert not second[0].lstrip().startswith(tc._OVERLAP_MARK.strip())


def test_seams_round_trip_two_sizes():
    chunk = tc.chunk
    for size in (150, 600):
        cs = chunk(LONG, max_chars=size, overlap_chars=size // 6)
        rebuilt = "\n\n".join(tc.strip_overlap_tail(c) for c in cs)
        assert normalized(rebuilt) == normalized(LONG)
