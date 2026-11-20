# AI-Benchmark GUI v1.7

A display-only upgrade to the existing Flask/Bootstrap GUI.

## Install

From the AI-Benchmark project root, back up the existing `app.py` and
`templates/` directory. Copy these bundle contents into that root:

- `app.py`
- `methodology.json`
- `templates/` (the complete updated template directory)
- `requirements.txt`

Then run:

```powershell
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`. The application continues to read the
existing `history.db`; it does not create or modify benchmark scores.

## What changed

- GUI version is 1.7 (Score Breakdown).
- Scores are clickable; no new columns. A problem score in the
  run-detail table links to its test-detail page, which gains a
  "How this score was calculated" block: test-based division
  (passed ÷ counted, skipped and xfail/xpass shown separately)
  for coding/debugging, the two-stage gate-then-kills
  derivation for testing, and the judge score with an explicit
  "no criterion-level marks stored" note for
  thinking-planning. Zero scores carry a plain-language reason
  distinguishing request failures, gate failures, timeouts,
  collection/execution errors, and all-tests-failed. The detail
  page also states how the problem contributes to its category
  mean, with a link to the full breakdown.
- A category score on the dashboard links to a new breakdown
  page: every problem score for that provider in that category
  with its basis, the averaging formula with the actual numbers,
  and the capability split alongside the blended mean. The
  breakdown mean is computed the same way as the dashboard's
  (request failures count as 0).
- Run detail gains a "Tests" column linking to a per-evaluation
  test-detail page: for runs with per-test capture, it lists which
  tests passed and failed as captured during that evaluation
  itself, with the full stored node ID on hover and the file
  prefix stripped for display. Rows without captured identities
  show "not recorded" with the reason (predates capture, failed
  before evaluation, or a plan score) or "no tests ran" with the
  error type — never invented names. Testing rows label the list
  as the reference-gate run. A failure-artifact link appears when
  a matching artifact exists (same 24-hour heuristic as the
  Evidence column).
- The methodology page gains a fourth "What this dashboard cannot
  show" block stating that test identities exist only for runs
  made after per-test capture.
- `/methodology` explains category scoring, blended score, capability,
  reliability, selection, latency, failure classification, historical
  comparability, and unavailable drill-down data.
- `methodology.json` is the shared source for the method page and the
  dashboard's inline legends.
- Dashboard, runs list, and run detail use request-failure counts derived
  from `not aibenchmark.report._is_valid_evaluation(error_type)`.
- `/evidence` browses read-only Markdown artifacts from `failure_artifacts/`; run-detail links use problem/provider/nearest timestamp within 24 hours because artifacts have no run ID; this is explicitly a heuristic.
- Category-level failure-class counts distinguish reference-gate failures, execution errors, truncations, request failures, and other valid-output failures.
- The methodology page includes the verified Run 26 Groq testing_002 worked example.
- The `/evidence` browser reads matching `*.md` files only; it never creates or edits artifacts. Configure `AIBENCHMARK_FAILURE_ARTIFACTS_DIR` if the directory is not `<project-root>/failure_artifacts`.
- Stored error types continue to be rendered through the existing
  `_display_error_type` helper.
- No scoring engine, database schema, report classifier, provider,
  evaluator, or audit code is included in this GUI bundle.

## Validation

Run from the project root:

```powershell
del tests\test_gui_v16.py
python -m unittest discover -s tests -v
```

Delete the stale `tests\test_gui_v16.py` first: it asserts v1.6
expectations (footer "GUI 1.6") that v1.7 intentionally changes.
The integration tests require Flask and the existing `aibenchmark`
package to be importable. The definition tests can run independently.
