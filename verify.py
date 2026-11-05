#!/usr/bin/env python3
"""verify.py — one-command checklist for the whole repo.

Runs, in order:
  1. docs present + no obvious secret patterns
  2. python examples compile
  3. pytest suite
  4. every numbered demo runs (offline ones for real; optional ones skip
     calmly when their tool isn't present — a skip is a PASS here)
  5. site checks (JS syntax via node if available; referenced ids present)

Exit 0 only if everything passes.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

REQUIRED_DOCS = [
    "docs/README-reading-guide.md",
    "docs/01-what-embeddings-are.md",
    "docs/02-similarity-search.md",
    "docs/03-vector-stores.md",
    "docs/04-chunking.md",
    "docs/05-local-toolkit.md",
    "docs/06-when-rag-is-overkill.md",
    "docs/07-cheat-sheet-glossary.md",
]
REQUIRED_SITE = ["site/index.html", "site/styles.css", "site/app.js"]

DEMO = ["examples/01-word-overlap-embeddings.py",
        "examples/02-openai-compatible-client.py",
        "examples/03-minivec-demo.py",
        "examples/04-ollama-embeddings.py",
        "examples/05-sqlite-vec-demo.py",
        "examples/06-chroma-demo.py"]

# crude secret-pattern scan (defense in depth; nothing here should match)
SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9]{20,}",          # OpenAI-style key
    r"(?i)api[_-]?key\s*=\s*['\"][A-Za-z0-9]{16,}",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
]


def check(label: str, ok: bool, detail: str = "") -> bool:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f" — {detail}" if detail else ""))
    return ok


def step_docs() -> bool:
    print("[1/5] docs")
    ok = True
    for path in REQUIRED_DOCS:
        full = os.path.join(ROOT, path)
        present = os.path.isfile(full) and os.path.getsize(full) > 2000
        ok &= check(f"{path} present & substantive", present)
    return ok


def step_no_secrets() -> bool:
    print("[2/5] secret-free check")
    ok = True
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in
                       (".git", "__pycache__", "node_modules", ".pytest_cache")]
        for name in filenames:
            if not re.search(r"\.(py|md|html|js|css|json)$", name):
                continue
            full = os.path.join(dirpath, name)
            try:
                text = open(full, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            for pat in SECRET_PATTERNS:
                if re.search(pat, text):
                    ok &= check(f"{os.path.relpath(full, ROOT)}", False,
                                f"matches secret pattern {pat}")
    check("no secret-like patterns anywhere", ok)
    return ok


def step_py() -> bool:
    print("[3/5] python: compile + tests + demos")
    ok = True
    for path in DEMO:
        full = os.path.join(ROOT, path)
        r = subprocess.run([sys.executable, "-m", "py_compile", full],
                           capture_output=True, text=True)
        ok &= check(f"{path} compiles", r.returncode == 0, r.stderr.strip()[:120])

    r = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q"],
                       capture_output=True, text=True,
                       cwd=ROOT, env={**os.environ, "PYTHONPATH": os.path.join(ROOT, "examples")})
    ok &= check("pytest tests/", r.returncode == 0,
                (r.stdout.strip().splitlines() or [""])[-1])

    for path in DEMO:
        r = subprocess.run([sys.executable, path], capture_output=True, text=True, cwd=ROOT)
        note = (r.stdout.strip().splitlines() or [""])[-1][:100]
        ok &= check(f"{os.path.basename(path)} runs", r.returncode == 0, note)
    return ok


def step_site() -> bool:
    print("[4/5] site")
    ok = True
    for path in REQUIRED_SITE:
        ok &= check(f"{path} present", os.path.isfile(os.path.join(ROOT, path)))

    app = os.path.join(ROOT, "site", "app.js")
    html = open(os.path.join(ROOT, "site", "index.html"), encoding="utf-8").read()

    # every script-referenced static id must exist in the HTML
    ids = set(re.findall(r'\$\("([A-Za-z]+)"\)', open(app, encoding="utf-8").read()))
    missing = [i for i in ids if f'id="{i}"' not in html and i != "btnBack"]
    ok &= check("static ids used by JS exist in HTML", not missing, ", ".join(missing))

    if subprocess.run(["which", "node"], capture_output=True).returncode == 0:
        r = subprocess.run(["node", "--check", app], capture_output=True, text=True)
        ok &= check("site/app.js parses (node --check)", r.returncode == 0,
                    r.stderr.strip()[:120])
    else:
        check("node not found — skipping JS syntax check", True, "non-fatal")
    return ok


def step_docs_text() -> bool:
    print("[5/5] handbook text hygiene")
    ok = True
    license_text = open(os.path.join(ROOT, "LICENSE"), encoding="utf-8").read()
    ok &= check("LICENSE carries the exact copyright line",
                "Copyright (c) 2026 Asdale Dynamics, LLC" in license_text)
    readme = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    ok &= check("README credits Asdale Dynamics, LLC",
                "Asdale Dynamics, LLC" in readme)
    readme_ok = all(s in readme for s in ["docs/", "site/", "examples/", "tests/"])
    ok &= check("README links the main folders", readme_ok)
    return ok


def main() -> None:
    os.chdir(ROOT)
    steps = [step_docs, step_no_secrets, step_py, step_site, step_docs_text]
    results = [step() for step in steps]
    all_ok = all(results)
    print()
    print("ALL CHECKS PASSED" if all_ok else "SOME CHECKS FAILED")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
