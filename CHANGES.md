# AI-Benchmark — critical fixes (2026-10-24)

This zip contains ONLY the files that changed, plus the reorganised
scratch scripts. Everything else in your project is untouched — do not
replace your whole project with this zip, just copy these files over
the matching paths (see "How to apply" below).

## What was fixed, and why

### 1. `aibenchmark/sandbox.py` — isolation, and honest limits
- BEFORE: the sandboxed subprocess got `env=os.environ.copy()` — full
  environment, including API keys — and had no network restriction at
  all. Only the 10-second timeout was real.
- AFTER: the subprocess gets a minimal environment (PATH, plus
  SYSTEMROOT/TEMP on Windows only). No API keys, no HOME, no proxy
  variables. A generated `sitecustomize.py` in the temp directory
  blocks Python-level network access (`socket.connect`,
  `create_connection`, `getaddrinfo`, `gethostbyname` raise OSError),
  so ordinary model code using `requests` / `urllib` / `socket` fails
  fast instead of reaching the network.
- LIMIT, stated plainly: this is NOT an OS-level security boundary.
  Model code still runs as your OS user, so deliberately malicious
  code could read files outside the temp directory or shell out to
  `curl`. If you ever need protection against malicious code, the
  next step is a container with `--network=none` (e.g. Docker), not a
  bigger Python patch. For scoring ordinary model output, the two
  gaps that actually existed — leaked secrets and unrestricted Python
  network access — are now closed.
- Also fixed in the same file:
  - Pytest output is now parsed line-by-line (`file::test STATUS`),
    not by counting the substring `" PASSED"` anywhere in the output.
    Printed test output can no longer inflate the score, and skipped
    tests no longer count.
  - `run_tests_sandboxed` now returns `"failed"` (not `"partial"`)
    when nothing passes, counts pytest ERRORs as failures, and returns
    `"test_file_missing"` instead of crashing if the test file is gone.
  - A missing `problem_dir` argument is unchanged in signature for
    compatibility, but it was never used; that is now documented in
    the code instead of silently ignored.

### 2. `aibenchmark/sandbox.py` — mutant reference gate (verified bug)
- BEFORE: the reference gate only rejected a test suite when it
  counted a `FAILED` line. A suite that errored on import/collection
  (0 FAILED lines, non-zero exit code) slipped through, and then every
  mutant that also errored was counted as killed. Verified: the old
  code scored a broken, import-error test suite as **1.0**.
- AFTER: the reference suite must pass cleanly — exit code 0, at
  least one test, no failures, no errors — otherwise the function
  returns `0.0, "reference_impl_failed"` (or `"no_tests_ran"` if
  nothing was collected) and never scores mutants. The broken suite
  above now scores **0.0**. In the mutant loop, a timeout still
  counts as killed (a mutant that hangs is detected), a run with no
  tests counts as NOT killed, and a harness error (not a test
  failure) also counts as NOT killed, so scores can no longer inflate
  from harness problems.

### 3. `aibenchmark/categories/testing.py` — import fixing
- BEFORE: the auto-added import was hardcoded to `is_valid` (wrong
  for the dedupe problem), and substring replacements corrupted
  `from parentheses import` into `from solutiontheses import`
  (replacing `from paren` first).
- AFTER: the function name(s) are parsed from that problem's own
  reference implementation with `ast` (`_ref_function_names`), and
  imports are rewritten with regexes that match whole module names
  only (`_fix_imports`). `from parentheses import is_valid` now
  becomes `from solution import is_valid`; a dedupe test with no
  import now gets `from solution import dedupe_preserve_order`; and
  `import paren_check` still becomes `import solution as paren_check`
  so later `paren_check.is_valid` uses keep working.
- No other behaviour in this file changed (prompt, scoring, and the
  `passed if score > 0` status rule are untouched — see "Not fixed
  in this batch").

### 4. `problems/coding/test_coding_002.py` — LRU test (verified bug)
- BEFORE: `test_update_existing` asserted that updating an existing
  key evicts another key. A textbook LRU passed 3/4 and failed only
  that test — capping every correct solution at 0.75, exactly the
  score Groq and Ollama got for this problem in every run.
- AFTER: updating an existing key is asserted to keep both keys
  (`get(1) == 100`, `get(2) == 2`), and a NEW test,
  `test_update_marks_recent`, checks the behaviour the old test was
  actually trying to check: after updating key 1, inserting key 3
  evicts key 2, not key 1. A correct LRU now scores 5/5 = 1.0.
- Note: old run history in `history.db` is NOT rewritten. Those
  0.75 rows for `coding_002` remain wrong in history; only future
  runs will score correctly. Do not compare old and new LRU scores
  as if they were measured the same way.

### 5. `aibenchmark/engine.py` — one crash no longer kills a run
- BEFORE: any exception in one evaluation (or in listing one
  category's problems, or in the contamination check) aborted the
  whole `bench run`, leaving a partial run in the DB.
- AFTER: a failed problem listing skips that category with a warning;
  a failed evaluation becomes one error row (`score 0.0, status
  "error", error_type "error: <Type>"`) and the run continues; a
  failed contamination check prints a warning and the run still
  returns its run ID so the report can be generated. Database insert
  failures are deliberately NOT swallowed — if history itself is
  broken, aborting is the honest outcome.

### 6. `aibenchmark/contamination.py` — two small crash / lookup fixes
- Thinking-planning: the DB category is `thinking-planning` (hyphen)
  but the folder is `thinking_planning` (underscore). The lookup now
  maps between them, so contamination can actually see those problems.
- Date parsing: an unquoted YAML `created:` value loads as a `date`
  object, and the old code called `.tzinfo` on it and crashed. Dates,
  datetimes, and strings are now all handled, and an unparseable
  value falls back to "now" instead of crashing the run.

### 7. `pyproject.toml` — pytest is now a declared runtime dependency
- Added `"pytest>=8.0"`. This is not just a dev dependency: the
  sandbox runs `python -m pytest` for every execution-based score,
  so a fresh install without pytest scored everything as an error.
  After applying, reinstall (see below) so the generated egg-info
  picks this up. Do NOT hand-edit `aibenchmark.egg-info/` — it is
  generated and will be rewritten by the reinstall.

### 8. `.gitignore` — two lines added
- Added `.pytest_cache/` and `test_history.db` (the throwaway DB that
  `tests/test_history.py` creates). Everything else is unchanged.

### 9. `scripts/` — project structure, reorganised (not deleted)
- The 25 root scratch files (`check_db.py`, `check_secrets.py`,
  `debug_sandbox*.py`, `debug_scorer*.py`, and the root `test_*.py`
  scripts) are now in `scripts/`, with a `scripts/README.md`
  explaining why they must NOT be moved into `tests/` (pytest would
  collect and execute them on import).
- One change inside `scripts/check_secrets.py` only: it no longer
  prints matched secret values, only the file, pattern type, and
  count. The original printed matches, which would leak a key into
  terminal output if one was ever found. It also now defaults to the
  project root (two levels up from `scripts/`) instead of a hardcoded
  `E:\AI-Benchmark` path, and skips generated folders.
- Everything else in `scripts/` is byte-for-byte the original files,
  including their old bugs and old API assumptions — they are history,
  not the product. If a script contradicts `aibenchmark/`, trust
  `aibenchmark/`.

## How to apply (read before copying)

1. Back up your project folder first (a plain copy of `E:\AI-Benchmark`
   somewhere else is enough).
2. Extract this zip into a TEMP folder, not directly over your project.
3. From the temp folder, copy these files over the matching paths in
   your project (overwriting the old versions):
   - `aibenchmark/sandbox.py`, `aibenchmark/engine.py`,
     `aibenchmark/contamination.py`
   - `aibenchmark/categories/testing.py`
   - `problems/coding/test_coding_002.py`
   - `pyproject.toml`, `.gitignore`
   - the whole `scripts/` folder (new folder in your project)
4. After you have verified that `scripts/` contains copies of all 25
   root scratch files, delete the OLD copies from the project root
   (the `check_*.py`, `debug_*.py`, and `test_*.py` files listed in
   `scripts/README.md`'s scope — do NOT delete `tests/test_history.py`,
   `problems/*/test_*.py`, or `history.db`). If you are unsure about a
   file, leave it in the root for now — a duplicate is harmless, a
   mistaken deletion is not. There is no script in this zip that
   deletes anything for you, on purpose.
5. Reinstall so the new dependency and entry point are picked up, from
   the project root: `pip install -e .`
   (If you use a virtual environment, activate it first. This will
   regenerate `aibenchmark.egg-info/` — that is expected.)
6. Verify, from the project root:
   - `python -m pytest tests/test_history.py -q`  (expect 5 passed)
   - `bench doctor`  (expect the providers you actually have keys
     for to show ready; missing keys will still show MISSING, which
     is correct — it is not a code error)
   - Do NOT expect old `history.db` rows to change. Old LRU 0.75 rows
     and old mutant scores stay as they were recorded.

## What was verified before sending this
All of the following were run against the fixed code (not just read):
- Correct LRU + fixed test file -> 1.0 / passed (was 0.75).
- Missing test file -> `test_file_missing`, no crash.
- Sandboxed code that reads an environment secret and tries a socket
  connection -> secret reads as missing, socket raises OSError, and
  the (correct) test asserting that behaviour passes.
- Broken (import-error) test suite against the mutant scorer ->
  0.0 with the old code scoring the same suite as 1.0.
- Failing reference test -> `reference_impl_failed`, 0.0.
- Good mutant tests -> 1.0 (all 3 mutants killed); always-pass tests
  -> 0.0 (none killed).
- Import rewrites: `parentheses`, `paren_check`, alias preservation,
  dedupe auto-import, generic wrong-module rewrite, and already-
  correct imports all produce the expected output.
- Thinking-planning contamination lookup now finds the real
  `2026-09-20` date instead of "now", and an unquoted YAML date no
  longer crashes.
- Engine: one evaluator raising `RuntimeError` becomes one error row
  and the run continues; a raising contamination check does not stop
  the run returning.
- `tests/test_history.py`: 5 passed, unchanged.

## Not fixed in this batch (major issues, intentionally left for next)
These were in the earlier overview but are NOT critical-path fixes,
so they are listed here rather than silently changed:
- Report status is still last-problem-wins, and "Current pick" ties
  are still broken arbitrarily (report.py, untouched).
- The thinking-planning judge still returns 0.0 silently on any
  failure, and its `JUDGE_MODEL` constant is still unused.
- Provider errors are still collapsed to `error: HTTPError` with no
  status code/body, and the five providers are still near-identical
  copies.
- All paths are still relative to the working directory; `bench`
  must still be run from the project root.
- Problem coverage is still 10 problems, not 15–20 per category,
  and only one model per provider is registered.
- The 6-month problem-review flag from the spec is still not
  implemented (only the recent-vs-old contamination warning is).
