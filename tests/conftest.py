"""
Shared pytest fixtures and helpers for the Japanese SRS study-app test suite.

Two layers of testing are supported:

1. **Unit** — the pure helper functions inside ``build_app.py`` (e.g. ``i_adj_info``)
   are extracted with ``ast`` and exec'd in an isolated namespace.  This lets us
   call them directly *without* running the build (importing ``build_app`` would
   otherwise read every data file and overwrite ``index.html`` as a side effect).

2. **Integration** — ``build_app.py`` is run as a subprocess inside a throwaway
   copy of the project (``study-app`` + sibling ``flashcards``), and the tests
   assert on the real generated ``index.html`` / embedded ``DECKS`` data.  The
   user's actual ``index.html`` is never touched.
"""

from __future__ import annotations

import ast
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

# ── Paths ─────────────────────────────────────────────────────────
TESTS_DIR      = Path(__file__).resolve().parent
STUDY_APP_DIR  = TESTS_DIR.parent
PROJECT_ROOT   = STUDY_APP_DIR.parent
FLASHCARDS_DIR = PROJECT_ROOT / "flashcards"
DATA_DIR       = STUDY_APP_DIR / "data"
BUILD_PATH     = STUDY_APP_DIR / "build_app.py"
ADJ_JSON       = FLASHCARDS_DIR / "adjectives_vocab.json"


# ── DECKS extraction ──────────────────────────────────────────────
def extract_decks(html: str):
    """Pull the embedded ``const DECKS = [...]`` array out of generated HTML."""
    m = re.search(r"const DECKS = (.*?);\nconst RECAP_IDS", html, re.S)
    assert m, "Could not find `const DECKS = ...;` in generated index.html"
    return json.loads(m.group(1))


def extract_script(html: str) -> str:
    """Return the contents of the single <script> block."""
    m = re.search(r"<script>(.*)</script>", html, re.S)
    assert m, "Could not find <script> block in generated index.html"
    return m.group(1)


# ── ast extraction of pure build_app symbols ──────────────────────
def load_build_symbols(names):
    """Exec only the named top-level defs / assignments from build_app.py.

    Preserves source order so functions can reference constants defined above
    them (e.g. i_adj_info -> REGULAR_II_ADJECTIVES).  Has no build side effects.
    """
    src = BUILD_PATH.read_text(encoding="utf-8")
    tree = ast.parse(src)
    keep = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            keep.append(node)
        elif isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if any(t in names for t in targets):
                keep.append(node)
    module = ast.Module(body=keep, type_ignores=[])
    ns: dict = {}
    exec(compile(module, str(BUILD_PATH), "exec"), ns)
    return ns


# ── Fixtures ──────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def build_symbols():
    """Pure conjugation helpers extracted from build_app.py (no build run)."""
    return load_build_symbols({"REGULAR_II_ADJECTIVES", "i_adj_info"})


@pytest.fixture(scope="session")
def i_adj_info(build_symbols):
    return build_symbols["i_adj_info"]


def _ignore(_dir, names):
    drop = {".git", "__pycache__", ".pytest_cache", "tests", ".DS_Store", "node_modules"}
    return [n for n in names if n in drop]


@pytest.fixture(scope="session")
def built(tmp_path_factory):
    """Run build_app.py hermetically in a temp copy; return html + decks.

    The real project files are never modified.
    """
    root = tmp_path_factory.mktemp("japaneseapp")
    shutil.copytree(STUDY_APP_DIR, root / "study-app", ignore=_ignore)
    shutil.copytree(FLASHCARDS_DIR, root / "flashcards", ignore=_ignore)

    proc = subprocess.run(
        [sys.executable, "build_app.py"],
        cwd=root / "study-app",
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"build_app.py failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"

    out_html = root / "study-app" / "index.html"
    assert out_html.exists(), "build did not produce index.html"
    html = out_html.read_text(encoding="utf-8")

    return SimpleNamespace(
        root=root,
        study_app=root / "study-app",
        html=html,
        decks=extract_decks(html),
        script=extract_script(html),
        stdout=proc.stdout,
    )


@pytest.fixture(scope="session")
def decks(built):
    return built.decks


@pytest.fixture(scope="session")
def all_cards(decks):
    return [c for d in decks for c in d["cards"]]


@pytest.fixture(scope="session")
def adj_data():
    return json.loads(ADJ_JSON.read_text(encoding="utf-8"))


# ── Independent reference conjugation (re-derived, not imported) ───
# Linguistic rules, written from scratch so the audit catches any drift in
# build_app.py rather than tautologically mirroring it.
REGULAR_II = {"かわいい"}  # ends in いい but is a normal i-adjective


def reference_i_adj(hira: str) -> dict:
    primary = hira.split("/")[0].strip()
    is_good = primary in ("いい", "よい") or (
        primary.endswith(("いい", "よい")) and primary not in REGULAR_II
    )
    if is_good:
        stem = (primary[:-2] if len(primary) >= 2 else "") + "よ"
    else:
        stem = primary[:-1] if primary.endswith("い") else primary
    return {
        "neg_cas": stem + "くない",
        "past_cas": stem + "かった",
        "negpast_cas": stem + "くなかった",
    }
