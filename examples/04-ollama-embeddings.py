"""04-ollama-embeddings.py — TOY TOOL: direct Ollama native-API demo.

Optional and offline when Ollama runs at localhost:11434. If Ollama is
not running, exits calmly with setup instructions — that's by design,
not a test failure.

Run:  python3 examples/04-ollama-embeddings.py
      OLLAMA_MODEL=mxbai-embed-large python3 examples/04-ollama-embeddings.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

BASE = "http://localhost:11434"
TIMEOUT = 60


def ollama_embed(texts: list[str], model: str) -> list[list[float]]:
    """POST /api/embeddings — Ollama's native endpoint (one text per call)."""
    out = []
    for text in texts:
        body = json.dumps({"model": model, "prompt": text}).encode("utf-8")
        req = urllib.request.Request(
            f"{BASE}/api/embeddings",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            payload = json.loads(resp.read())
        out.append(payload["embedding"])
    return out


def alive() -> bool:
    try:
        urllib.request.urlopen(BASE, timeout=5)
    except urllib.error.HTTPError:
        return True
    except (urllib.error.URLError, ConnectionError, OSError):
        return False
    return True


def main() -> None:
    model = os.environ.get("OLLAMA_MODEL", "nomic-embed-text")

    if not alive():
        print(f"[skip] Ollama not running at {BASE}")
        print("Install from https://ollama.com, then:")
        print(f"  ollama pull {model}")
        print("  ollama serve        # or the desktop app")
        sys.exit(0)

    dims_used: dict[int, int] = {}
    texts = ["Refunds are processed within 30 days.", "Customer bought two lamps."]
    try:
        vecs = ollama_embed(texts, model)
    except (urllib.error.HTTPError, urllib.error.URLError, ConnectionError,
            OSError, json.JSONDecodeError, KeyError) as exc:
        code = getattr(exc, "code", None)
        if code == 404:
            print(f"[skip] model {model!r} not found on this machine.")
            print(f"Run:  ollama pull {model}")
            sys.exit(0)
        print(f"[error] {exc}")
        sys.exit(1)

    import math
    norms = []
    for text, vec in zip(texts, vecs):
        dims_used[len(vec)] = 1
        norms.append(math.sqrt(sum(x * x for x in vec)))
        preview = ", ".join(f"{x:+.3f}" for x in vec[:4])
        print(f"dim={len(vec)}  {text!r}\n  head of vector: [{preview}, ...]")

    if len(dims_used) != 1:
        print("[error] inconsistent dims — that should never happen from one model")
        sys.exit(1)

    dim = next(iter(dims_used))
    avg_norm = sum(norms) / len(norms)
    print(f"\n[ok] {model} -> dim {dim}, mean vector norm {avg_norm:.3f}")
    if abs(avg_norm - 1.0) > 0.05:
        print("NOTE: the NATIVE endpoint here returns un-normalized vectors.")
        print("Cosine search is unaffected by scale, but dot-product search is")
        print("not — normalize before mixing the two (Chapter 2). The /v1")
        print("endpoint of the same server (example 02) DOES ship unit-length.")

    print("This exact vector format is what lands in SQLite-vec (05) or Chroma (06).")


if __name__ == "__main__":
    main()
