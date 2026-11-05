"""02-openai-compatible-client.py — TOY TOOL: a /v1/embeddings client that
works against any local OpenAI-compatible server (Chapter 5).

Supported local servers (all keyless, all on your machine):
  * LM Studio         http://localhost:1234/v1
  * llama.cpp server  http://localhost:8080/v1
  * vLLM              http://localhost:8000/v1
  * Ollama            http://localhost:11434/v1   (model: nomic-embed-text)

This script DOES NOT require any of them. If none is running it exits
calmly with instructions — it's not a test failure, it's optional.

Run:  python3 examples/02-openai-compatible-client.py
      BASE_URL=http://localhost:1234/v1 MODEL=gte-7b python3 ...
(Env vars are read from the SHELL, never from a file: no secrets here.)
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "nomic-embed-text"
TIMEOUT = 30


def embed_texts(
    texts: list[str],
    base_url: str = DEFAULT_BASE_URL,
    model: str = DEFAULT_MODEL,
    timeout: int = TIMEOUT,
) -> list[list[float]]:
    """POST /v1/embeddings — the one wire format Chapter 5 cares about."""
    body = json.dumps({"input": texts, "model": model}).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/embeddings",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read())
    return [item["embedding"] for item in payload["data"]]


def server_alive(base_url: str, timeout: int = 5) -> bool:
    """Any HTTP response at all (even 404) means a server is listening."""
    try:
        urllib.request.urlopen(base_url.rstrip("/").rsplit("/", 1)[0], timeout=timeout)
    except urllib.error.HTTPError:
        return True
    except (urllib.error.URLError, ConnectionError, OSError):
        return False
    return True


def main() -> None:
    base_url = os.environ.get("BASE_URL", DEFAULT_BASE_URL)
    model = os.environ.get("MODEL", DEFAULT_MODEL)

    if not server_alive(base_url):
        print(f"[skip] nothing listening at {base_url}")
        print("This demo needs a local embeddings server, e.g.:")
        print("  ollama serve                    # then: ollama pull nomic-embed-text")
        print("  -- or LM Studio / vLLM / llama-server on their defaults")
        sys.exit(0)

    texts = ["refund window is 30 days", "apnea event at 0300"]
    try:
        vecs = embed_texts(texts, base_url=base_url, model=model)
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", "replace")[:200]
        except Exception:
            pass
        if exc.code in (404, 400) and ("not found" in detail.lower()
                                       or "embeddings" in detail.lower()):
            print(f"[skip] server at {base_url} answered {exc.code}: {detail.strip()}")
            print("Likely fixes: pull/load an embedding model, e.g.:")
            print(f"  ollama pull {model}     # and/or start the server with embeddings enabled")
            sys.exit(0)
        print(f"[error] server reachable at {base_url} but /embeddings failed:")
        print(f"  HTTP {exc.code} {detail.strip()}")
        sys.exit(1)
    except (urllib.error.URLError, ConnectionError, OSError, json.JSONDecodeError,
            KeyError, ValueError) as exc:
        print(f"[error] server reachable at {base_url} but /embeddings failed: {exc}")
        print("Check: is an embedding model loaded/pulled? Is MODEL spelled right?")
        sys.exit(1)

    dims = {len(v) for v in vecs}
    if len(dims) != 1:
        print(f"[error] server returned inconsistent dims {dims}")
        sys.exit(1)

    dim = dims.pop()
    print(f"[ok] {base_url} model={model} produced {len(vecs)} vectors of dim {dim}")
    # Same-model rule (Ch. 3): never mix these with vectors from another model.
    print("Vectors are deterministic per model; record model + dim in your metadata.")


if __name__ == "__main__":
    main()
