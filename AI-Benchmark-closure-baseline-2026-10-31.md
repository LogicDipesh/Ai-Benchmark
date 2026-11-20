# AI-Benchmark — closure baseline (2026-10-31)

Preserved closure state for the two workstreams completed on
2026-10-31. Do not reopen either diagnosis without new
contradictory evidence.

## Closed workstreams

| Workstream | Final status |
|---|---|
| OpenRouter token accounting (DIAGNOSES.md entry 6) | Resolved |
| Failure-attribution labels and implementation | Resolved |
| Quota fail-fast regression | 60/60 passed |
| Display mapping regression | 13/13 passed |
| Audit chain — Runs 23–26 | All passing (50 rows each) |
| Demo baseline | Run 14 — unchanged |

## Token-accounting diagnosis (evidence-based, with its limit)

- Approximately 5,000 reasoning tokens per call count toward the
  8,192-token budget (probe v1.1, 2026-10-31 09:59 IST:
  reasoning_tokens 5005, completion_tokens 4959, prompt_tokens 120;
  record probe_output_20261031-042756.json).
- A fresh generation completed cleanly (finish_reason stop, stored
  response identical to raw at 1000 chars, extracted code parses
  and passes all 7 coding_001 problem tests).
- Run 26's individual reasoning-token count was not stored, so its
  failure is strongly consistent with this mechanism but cannot be
  directly proven retrospectively.
- The 8,192 cap remains unchanged.
- Capturing usage metadata going forward is a potential new
  feature, not unfinished investigation.

## Failure-attribution implementation

- Report-side display mappings only (report.py overwrite; no new
  table column — the audit parser requires exactly 5 cells — detail
  bullets instead).
- Stored error types unchanged; audit classification unchanged.
- Verified live: 13/13 mapping cases, 60/60 fail-fast checks,
  audit PASS on run 26.

## Standing configuration at closure

- Audited baseline: run 26 (270.9 s); GLM cap 1 is the standard
  configuration; code caps 8192, thinking-planning 4096; default
  temperature; run-22 stricter code-only prompt; judge
  gemini-3.5-flash-lite with zero judge errors (runs 20–26).
- Picks at run 26: coding groq, debugging groq, testing gemma,
  TP groq. Demo stays on run 14.

## Reopen rule

Reopen either diagnosis only on NEW CONTRADICTORY EVIDENCE (for
example, a fresh probe showing reasoning tokens NOT counted toward
the cap, or a display-mapping failure on a live report). Routine
later runs, single-occurrence variance, and the known unrecoverable
run-26 record do not reopen them.
