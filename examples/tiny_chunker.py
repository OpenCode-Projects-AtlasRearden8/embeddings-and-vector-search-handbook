"""tiny_chunker.py — the seam-aware chunker from Chapter 4, stdlib only.

The rules (bold marks differences from the naive "cut every N chars"):

1. Cut at natural *seams*: the text is split into blocks at blank lines,
   and a markdown heading always begins a new chunk and travels with the
   block it introduces — so a chunk is one topic.
2. **Never split a sentence** unless a whole block exceeds `max_chars`;
   then sentences are regrouped instead of chopped at a character count.
3. Coalesce small blocks up to `max_chars` — so chunks aren't orphans
   unless the source itself is tiny (a property of the corpus).
4. A size-caused boundary (not a heading boundary) carries a small tail of
   the previous chunk into the next — Chapter 4's OVERLAP-CHARS knob.
"""

from __future__ import annotations

import re

_SENT_RE = re.compile(r"[^.!?]+[.!?]+(?:\s|$)|[^.!?]+$")
_HEADING_RE = re.compile(r"^\s*#{1,6}\s")
_OVERLAP_MARK = " \u2026 "


def tokenize_blocks(text: str) -> list[str]:
    """Split into blank-line-separated blocks, trimmed, in document order."""
    return [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]


def split_sentences(block: str) -> list[str]:
    """Sentences keep their trailing punctuation and internal whitespace."""
    return [s.strip() for s in _SENT_RE.findall(block) if s.strip()]


def _tail(text: str, n: int) -> str:
    """Trailing ~n chars of text, aligned to a word boundary."""
    if n <= 0 or len(text) <= n:
        return text.strip()
    tail = text[-n:]
    cut = tail.find(" ")
    return tail[cut + 1:].strip() if cut != -1 else tail.strip()


def _regroup_sentences(block: str, max_chars: int) -> list[str]:
    """Group sentences of an oversized block into <= max_chars pieces."""
    pieces: list[str] = []
    cur = ""
    for sent in split_sentences(block):
        if cur and len(cur) + 1 + len(sent) > max_chars:
            pieces.append(cur)
            cur = sent
        elif cur:
            cur = cur + " " + sent
        else:
            cur = sent
    if cur:
        pieces.append(cur)
    return pieces


def strip_overlap_tail(ch: str) -> str:
    """Inverse of the overlap post-pass: remove a leading inherited tail."""
    if _OVERLAP_MARK in ch:
        return ch.split(_OVERLAP_MARK, 1)[1]
    return ch


def chunk(text: str, max_chars: int = 800, overlap_chars: int = 100) -> list[str]:
    """Chunk markdown-ish text at seams, in document order.

    Guarantees (enforced by tests/test_tiny_chunker.py):
    * every chunk <= max_chars + margin, where margin = overlap_chars + 40;
    * no sentence is split across chunks;
    * a markdown heading always starts the chunk it introduces.
    """
    if max_chars < 40:
        raise ValueError("max_chars too small to hold a single sentence sensibly")
    overlap_chars = min(overlap_chars, max_chars // 4)

    blocks = tokenize_blocks(text)
    raw_chunks: list[tuple[str, bool]] = []  # (text, starts_fresh)
    pending_heading = ""                     # heading waiting for its body
    cur = ""                                 # chunk under construction
    cur_is_fresh = True                      # did cur start at a seam?

    def flush() -> None:
        nonlocal cur, cur_is_fresh
        if cur.strip():
            raw_chunks.append((cur.strip(), cur_is_fresh))
        cur, cur_is_fresh = "", True

    for block in blocks:
        if _HEADING_RE.match(block):
            if cur:
                flush()
            pending_heading = block
            continue

        unit = (pending_heading + "\n\n" + block) if pending_heading else block
        pending_heading = ""
        unit_is_fresh = bool(_HEADING_RE.match(unit))

        if len(unit) > max_chars:
            pieces = _regroup_sentences(unit, max_chars)
            for i, piece in enumerate(pieces):
                fresh = unit_is_fresh and i == 0
                if not cur:
                    cur, cur_is_fresh = piece, fresh
                elif len(cur) + 2 + len(piece) <= max_chars:
                    cur = cur + "\n\n" + piece
                else:
                    flush()
                    cur, cur_is_fresh = piece, fresh
        else:
            if not cur:
                cur, cur_is_fresh = unit, unit_is_fresh
            elif len(cur) + 2 + len(unit) <= max_chars:
                cur = cur + "\n\n" + unit
            else:
                flush()
                cur, cur_is_fresh = unit, unit_is_fresh

    if pending_heading:
        cur = (cur + "\n\n" + pending_heading) if cur else pending_heading
    flush()

    chunks = [c for c, _ in raw_chunks]
    fresh_flags = [f for _, f in raw_chunks]

    # overlap post-pass: only size-caused boundaries carry a previous tail
    if overlap_chars > 0:
        for i in range(1, len(chunks)):
            if fresh_flags[i]:
                continue
            head = _tail(chunks[i - 1], overlap_chars)
            if head and not chunks[i].startswith(head):
                chunks[i] = head + _OVERLAP_MARK + chunks[i]
    return chunks


def chunk_with_metadata(text: str, max_chars: int = 800, overlap_chars: int = 100) -> list[dict]:
    """Chunk + the metadata Chapter 4 says every chunk should carry."""
    return [
        {
            "text": c,
            "chars": len(c),
            "orphan": len(re.findall(r"[A-Za-z0-9']+", c)) < 25,
            "starts_with_heading": bool(_HEADING_RE.match(c)),
        }
        for c in chunk(text, max_chars=max_chars, overlap_chars=overlap_chars)
    ]


def main() -> None:  # pragma: no cover - teaching demo
    sample = open("examples/sample-doc.md", encoding="utf-8").read()
    for size in (800, 200, 120):
        print(f"--- max_chars={size} ---")
        meta = chunk_with_metadata(sample, max_chars=size, overlap_chars=size // 7)
        for i, c in enumerate(meta):
            flag = " ORPHAN" if c["orphan"] else ""
            print(f"[chunk {i}, {c['chars']} chars{flag}]")
            print(c["text"][:98] + ("..." if c["chars"] > 98 else ""))
            print()


if __name__ == "__main__":
    main()
