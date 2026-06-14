# Tests

A pytest suite for the Japanese SRS study app. It exercises both the Python
build logic and the single-file app it generates.

## Running

```bash
cd study-app
pip install -r requirements-dev.txt   # first time only
pytest                                # runs the whole suite
pytest tests/test_conjugation.py -v   # one file, verbose
```

`node` is used (if present) to syntax-check the generated JavaScript. If `node`
isn't installed, that one test is skipped; everything else still runs.

## What's covered

| File | Focus |
|------|-------|
| `test_conjugation.py` | The い/な-adjective conjugation logic. Hand-verified ground truth for ~14 words, the かわいい-vs-かっこいい distinction, synthetic/未知 inputs, slash forms, plus a full audit of every generated conjugation card against an independent reference. Also asserts none of the old buggy forms (e.g. `あたまがくない`) survive. |
| `test_data_integrity.py` | Every source JSON parses and matches its schema (vocab, adjectives, verbs, weekly recaps); no duplicate IDs within a file; i-adjectives end in い. |
| `test_build.py` | The build runs; every card has the full field shape; all card IDs are globally unique and follow the documented prefixes; load-bearing IDs are present (renaming them would wipe user progress); the build is deterministic (byte-identical on re-run). |
| `test_app_features.py` | The generated app embeds the wiring for search, browse + single-card practice, favorites, and report-an-issue; the JS is syntactically valid; the report email is exactly the configured address. |

## How it works

- **Unit tests** of pure functions (e.g. `i_adj_info`) extract just those
  definitions from `build_app.py` with `ast` and exec them in an isolated
  namespace — so importing them never triggers a build or overwrites
  `index.html`.
- **Integration tests** copy `study-app/` and its sibling `flashcards/` into a
  temp directory, run `build_app.py` there, and assert on the real generated
  `index.html`. Your working copy of `index.html` is never modified.

When you add vocabulary or change `build_app.py`, run the suite before shipping.
