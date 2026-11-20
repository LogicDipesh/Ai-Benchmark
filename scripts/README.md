# scripts/ — manual scratch, not automated tests

These files used to sit in the project root, mixed in with the real
project (`plan.md`, `pyproject.toml`, the `aibenchmark/` package, and
`problems/`). They are now grouped here so the root stays clean:

- `check_db.py`, `check_secrets.py` — small inspection utilities.
- `debug_sandbox*.py`, `debug_scorer*.py` — the step-by-step debugging
  trail that led to the current `aibenchmark/sandbox.py`.
- `test_*.py` in this folder — manual smoke / debugging scripts that
  print results and call providers directly. They are NOT pytest tests.

Rules for this folder:

1. Run everything from the project root (e.g. `python scripts/test_smoke.py`),
   not from inside `scripts/`. The scripts use relative paths like
   `problems/coding` and `history.db`, which only work from the root.
2. Do NOT move these files into `tests/`. Pytest collects `test_*.py`
   files, and these scripts execute provider calls and print output on
   import — they would run (and fail, or spend API calls) as part of
   `pytest`. The only real pytest test in this project is
   `tests/test_history.py`, and it stays there.
3. These files are history, not the product. If a script contradicts the
   fixed code in `aibenchmark/`, trust `aibenchmark/` — several of these
   scripts were written against older versions of the sandbox API
   (for example, some unpack `run_mutant_tests_sandboxed` as one value
   and some as two; the current function returns two).
