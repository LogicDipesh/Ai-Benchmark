# Evaluation Evidence Capture — Release notes (steps 1–5)

## Design decision (standing)

Never reconstruct historical test counts from aggregate scores. Only
display counts that were actually captured during evaluation. Runs
1–26 have no per-test counts (not recorded, NULL never zero). A
gate-failed testing row shows mutant kills as "not measured", never
zero. The Groq 13/14 example is exempt only because it was
independently reproduced by execution — verified evidence, not
reconstruction.

## What shipped

| Step | What | Status |
| ---- | ---- | ------ |
| 1 | Score-equivalence regression test (22 fixtures, 4 dimensions: score, status, error type, gate outcome) | Done, confirmed on Linux harness and Windows/Python 3.14 |
| 2 | Sandbox evidence capture (same pytest run as the score; old interfaces preserved) | Done, installed + confirmed |
| 3 | Database persistence (14 nullable columns, auto-migration, read-back API) | Done, installed + migrated (1244 legacy rows, all NULL) |
| 4 | GUI v1.5 display (Test counts column, methodology section 07) | Done, installed + confirmed by dashboard screenshot |
| 5 | Regression + release (this note) | Regression suites green in combined harness; his-machine re-run pending |

## Invariants (all hold)

- Scoring invariance: no score, status, error type, or gate
  outcome changed at any step (proven by the step-1 test running
  unmodified against instrumented code).
- Historical integrity: migration adds columns only; no legacy
  score or row was modified (legacy scores verified intact).
- Backward compatibility: old readers (report, audit, GUI)
  work unchanged on the migrated schema (audit PASSES).
- Gate awareness: kills are structurally None when the gate did
  not pass, in the database and on screen.
- Baseline frozen: run 26 remains the audited baseline; v1.4's
  features and behavior are preserved inside v1.5.

## Verification (combined final files, one harness)

- `test_score_equivalence.py`: 4 tests OK.
- `verify_evidence.py`: 15 checks PASS.
- `verify_evidence_store.py`: all checks PASS, including the real
  `audit_report.py` PASSING on a migrated-schema fixture run.
- GUI tests (`tests/test_gui_v15.py`): 25 tests OK.

## What the next bench run produces

The first run on the installed code will be the first run whose
rows carry evidence: direct counts per problem, gate counts plus
kills/total per testing problem, None for provider failures and
plans. Confirm then on the dashboard and one run-detail page that
counts render for the new run and that any gate-failed row shows
kills as "not measured" live. Until that run, every row correctly
shows "not recorded".

## Known limits (by design, not defects)

- Timeout evidence is None: the killed run's partial output is
  discarded, so no count is claimed.
- Per-mutant evidence is outcomes only (killed/survived/not_run),
  not per-mutant counts.
- Token counts and per-attempt records are still not stored
  (retries collapse into one row, as before).
- Positive GUI display on a real run is pending the next bench
  run; harness fixtures prove the rendering.

## Installed files

- `aibenchmark/sandbox.py`, `aibenchmark/categories/coding.py`,
  `aibenchmark/categories/debugging.py`,
  `aibenchmark/categories/testing.py` (step 2)
- `aibenchmark/history.py`, `aibenchmark/engine.py` (step 3)
- `app.py`, `methodology.json`, `templates/` (GUI v1.5, step 4)
- `test_score_equivalence.py`, `score_equivalence_golden.json`,
  `verify_evidence.py`, `verify_evidence_store.py`,
  `migrate_evidence.py`, `tests/test_gui_v15.py` (verification)
