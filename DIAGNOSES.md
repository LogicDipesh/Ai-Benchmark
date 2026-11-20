# AI-Benchmark — verified failure diagnoses

This file records failure diagnoses that were verified by execution,
not inferred from error strings alone. Each entry names the run, the
task, the provider, the failure stage, the reproducible evidence, and
the diagnosis confidence, so a future run does not require repeating
the investigation.

How an entry was verified: the failure artifact's executed code was
run under pytest against the reference (testing) or the problem's
test file (coding), and the failing assertions / collection errors
below are the observed outputs of those runs.

Baseline context for every entry below: Run 26 (2026-10-30, wall
270.9 s, notes "GLM cap-1 confirmation + failure artifacts live")
is the audited baseline — `python audit_report.py 26` passes on all
50 history.db rows. Configuration at that run: GLM semaphore cap 1
(promoted from experimental to the standard configuration after
this run); code evaluators at max_tokens 8192; thinking-planning
at 4096; default temperature; run-22 stricter code-only prompt;
judge gemini-3.5-flash-lite with zero judge errors. This was the
first run with the failure-artifacts patch live, which is why these
artifacts exist.

## 1. testing_002 (dedupe_preserve_order) — NVIDIA — reference_impl_failed

- Run: 26. Provider/model: nvidia / nvidia/nemotron-3-ultra-550b-a55b.
  Row: score 0.0, latency 67,388 ms. Artifact:
  `testing_002_dedupe_preserve_order__nvidia__20261030-175054.md`.
- Failure stage: reference validation. The generated test suite did
  not pass cleanly against the reference implementation, so the
  strict reference gate rejected the suite before any mutant was
  evaluated (score 0.0, no mutant-kill measurement).
- Reproduced evidence (pytest on the artifact's executed suite
  against the reference): 17 passed, 2 failed.
  - `test_with_mixed_types`: expects `dedupe([1, "1", 1.0, "1"])` to
    equal `[1, "1", 1.0]`, but 1.0 equals 1 (equal hash), so the
    reference returns `[1, "1"]`. It also expects all four of
    `[True, 1, False, 0]` to survive, but True equals 1 and False
    equals 0, so the reference returns `[True, False]`.
  - `test_with_floats`: the NaN assertion expects
    `[float("nan"), 1.0, float("nan")]` to equal itself, but the two
    NaN values are distinct objects kept by the reference (NaN
    never equals anything, including itself), and list equality
    fails for the same reason (NaN != NaN).
- Diagnosis: suite contains incorrect expectations under Python's
  equality and hashing semantics. The reference is not implicated:
  it implements exactly the contract shown in the prompt
  (set-membership dedupe, order of first occurrence).
- Confidence: high — verified by execution.

## 2. testing_002 (dedupe_preserve_order) — Groq — reference_impl_failed

- Run: 26. Provider/model: groq / openai/gpt-oss-120b. Row: score
  0.0, latency 2,088 ms. Artifact:
  `testing_002_dedupe_preserve_order__groq__20261030-174950.md`.
- Failure stage: reference validation (same gate as entry 1).
- Reproduced evidence (pytest): 13 passed, 1 failed. The single
  failure is the falsy parametrized case: the suite expects
  `dedupe([None, None, 0, False, 0])` to equal `[None, 0, False]`,
  but False equals 0, so the reference returns `[None, 0]`. All
  other cases pass, including the unhashable-input TypeError cases
  and the custom-hashable-object case.
- Diagnosis: suite contains one incorrect expectation (False == 0).
  Same underlying misconception as entry 1, different instance.
- Confidence: high — verified by execution.

## 3. testing_002 (dedupe_preserve_order) — GLM — reference_impl_failed

- Run: 26. Provider/model: zhipu / glm-4.7-flash. Row: score 0.0,
  latency 6,712 ms. Artifact:
  `testing_002_dedupe_preserve_order__zhipu__20261030-174958.md`.
- Failure stage: reference validation (same gate as entries 1–2).
- Reproduced evidence (pytest): 8 passed, 1 failed. The single
  failure is `test_mixed_types`, second assertion: the suite
  expects `dedupe([None, 0, False, None])` to equal
  `[None, 0, False]`, but False equals 0, so the reference returns
  `[None, 0]`.
- Diagnosis: suite contains one incorrect expectation (False == 0).
  Same underlying misconception as entries 1–2, different
  instance.
- Confidence: high — verified by execution.

## 4. testing_002 — shared finding: the reference is exonerated

- The three failing suites disagree with the reference on Python
  equality semantics (1 == 1.0, True == 1, False == 0, NaN != NaN).
  The reference implements the shown contract; the suites'
  expectations contradict the language, not the reference.
- Gemma's and OpenRouter's suites pass the same reference in the
  same runs, which corroborates that the reference and harness
  work.
- Strict-gate consequence (by design, not a flaw): one wrong
  assertion zeroes the whole suite (score 0.0, no mutant
  evaluation). A 0.00 testing row can therefore mean "one assertion
  wrong in an otherwise good suite" — read the artifact to tell
  which. This explains testing score swings between runs.
- No task or reference change is warranted by these three entries.

## 5. coding_001 (palindrome linked list) — GLM — execution_error

- Run: 26. Provider/model: zhipu / glm-4.7-flash. Row: score 0.0,
  status error, latency 4,206 ms. Artifact:
  `coding_001_palindrome_linked_list__zhipu__20261030-174836.md`.
- Failure stage: collection (import). The test file imports
  module-level `is_palindrome` and `ListNode`, but the submission
  defines a LeetCode-style `class Solution` with `is_palindrome`
  as a method, and its `ListNode` definition is commented out.
  Neither imported name exists, so pytest fails at collection
  before any test runs: `ImportError: cannot import name
  'is_palindrome'`.
- Algorithm vs interface (measured, not just inspected): the
  submitted code verbatim, with ONLY an interface fix applied
  (uncommented `ListNode` block plus a module-level
  `is_palindrome` delegating to `Solution().is_palindrome`, no
  algorithm logic changed), passes all 7 problem tests. So the
  algorithm (slow/fast pointers plus second-half reversal) is
  correct, and the failure is purely interface/contract compliance.
- Verdict: model-side interface failure. The submission still
  scores 0 — the required interface is part of the task, and a
  correct algorithm that cannot be imported by the prescribed
  harness is not a working solution for that task. No passing
  score is awarded for the as-submitted code.
- Confidence: high — failure verified by execution; algorithm
  correctness measured by the adapted run.

## 6. coding_001 (palindrome linked list) — OpenRouter — execution_error; truncated_at_cap

- Run: 26. Provider/model: openrouter / cohere/north-mini-code:free.
  Row: score 0.0, status error, latency 64,754 ms. Artifact:
  `coding_001_palindrome_linked_list__openrouter__20261030-174937.md`.
- Failure stage: collection (syntax error), caused by two
  compounding problems.
  - Primary: incomplete output. The response was cut at the 8192
    token cap mid-signature (the model re-emitted the `ListNode`
    definition and ran out of budget). The stored response ends
    with `def __init__(self, val=0, next=None` and contains no
    `is_palindrome` at all, so no extraction could have satisfied
    the task.
  - Secondary: extraction fallback. The code extractor requires a
    closing Markdown fence; on an unclosed fence it returns the
    response as-is, fence marker included, so the executed file
    starts with a literal ```` ```python ```` line and fails to
    parse. Verified: the true fence-included truncated content
    produces a SyntaxError at collection. The fence issue is
    secondary — the code is incomplete regardless.
- Token accounting — RESOLVED 2026-10-31 by live probe
  (probe_openrouter_tokens.py v1.1; record
  probe_output_20261031-042756.json): the model spends roughly
  5000 reasoning tokens per call (probe call: reasoning_tokens
  5005, completion_tokens 4959, prompt_tokens 120), and reasoning
  tokens count toward the same 8192 max_tokens budget as visible
  output. The fresh probe generation finished cleanly
  (finish_reason stop, stored response identical to raw at 1000
  chars, extracted code parses and passes all 7 problem tests).
  Run 26's shape — length flag plus 65 visible characters — is
  exactly what this mechanism predicts when reasoning runs long
  and exhausts the budget before the answer finishes.
  Limit, stated honestly: run 26's own reasoning count was never
  stored (provider results carry no usage field), so the run-26
  instance is strongly consistent with the mechanism, not directly
  proven. No further action; the 8192 cap is unchanged, and
  capturing usage going forward would be a new feature, not a
  reopening of this item.
- Confidence: failure verified by execution (high);
  token-accounting mechanism demonstrated by live probe (high);
  run-26 instance consistent but unproven (stated limit).

## Run 27 entries

Run 27 context (applies to entries 7–13): Run 27 (2026-10-31,
wall 431.0 s, notes "First evidence-capture run (steps 2-4
live)") is the first evidence-carrying run. Its evidence check
passed (coding 14/15 rows carry evidence, debugging 15/15,
testing 9/10, plans 0/10 as designed — the two missing rows are
GLM request failures; gate-failed kills NULL; gate-passed kills
3/3), and `python audit_report.py 27` passes on all 50 rows.
Configuration unchanged from run 26 (GLM cap 1 standard, code
caps 8192, plans 4096, default temperature, run-22 prompt, judge
gemini-3.5-flash-lite, zero judge errors).

## 7. testing_001 (valid parentheses) — Groq — reference_impl_failed

- Run: 27. Provider/model: groq / openai/gpt-oss-120b. Row:
  score 0.0, latency 1,679 ms. Artifact:
  `testing_001_valid_parentheses__groq__20261031-144133.md`.
- Failure stage: reference validation (same gate as entries 1–3).
- Reproduced evidence (pytest): 27 passed, 1 failed. The single
  failure is a deep-nesting "valid" case:
  `'(((([[[{{{}}}]]] ))))'` is expected True, but the reference
  returns False — the string contains a space, and any
  non-bracket character hits the reference's reject branch
  (`else: return False`).
- Diagnosis: suite defect (stray whitespace changes the input's
  validity). The reference is not implicated.
- Confidence: high — verified by execution.

## 8. testing_001 (valid parentheses) — NVIDIA — reference_impl_failed

- Run: 27. Provider/model: nvidia /
  nvidia/nemotron-3-ultra-550b-a55b. Row: score 0.0, latency
  45,850 ms. Artifact:
  `testing_001_valid_parentheses__nvidia__20261031-144209.md`.
- Failure stage: reference validation (same gate).
- Reproduced evidence (pytest): 14 passed, 46 subtests passed,
  1 subfailed. The failure is `test_complex_valid` with
  `s='(((((([[[[]]]))))))'`: the string has 4 `[` but only 3
  `]`, one closing bracket short, so it is unbalanced and the
  reference returns False where the suite expects True.
- Diagnosis: suite defect (mistyped valid example). The
  reference is not implicated.
- Confidence: high — verified by execution.

## 9. testing_001 (valid parentheses) — GLM — reference_impl_failed

- Run: 27. Provider/model: zhipu / glm-4.7-flash. Row: score
  0.0, latency 6,052 ms. Artifact:
  `testing_001_valid_parentheses__zhipu__20261031-144241.md`.
- Failure stage: reference validation (same gate).
- Reproduced evidence (pytest): 5 passed, 1 failed. The single
  failure is `test_single_character`, which asserts
  `assertTrue(is_valid("a"))`; the reference returns False for
  `"a"` (non-bracket character, reject branch). The suite's own
  comment ("Non-parenthesis characters are invalid") contradicts
  its assertion.
- Diagnosis: suite defect (assertion contradicts the documented
  contract). The reference is not implicated.
- Confidence: high — verified by execution.

## 10. testing_001 (run 27) — no shared cause

- The three run-27 testing_001 failures are independent
  mistakes: whitespace (entry 7), an unbalanced example
  (entry 8), a contract contradiction (entry 9). Their common
  outcome is a failed reference gate, not a common underlying
  defect. Do not group them under one root cause.
- Contrast with entry 4 (run 26 testing_002), where the three
  suites did share one misconception class (equality semantics).
  Run 27 testing_001 does not.

## 11. testing_002 (dedupe_preserve_order) — Groq — reference_impl_failed

- Run: 27. Provider/model: groq / openai/gpt-oss-120b. Row:
  score 0.0, latency 3,684 ms. Artifact:
  `testing_002_dedupe_preserve_order__groq__20261031-144209.md`.
- Failure stage: reference validation (same gate).
- Reproduced evidence (pytest): 11 passed, 1 failed. The single
  failure is the parametrized bool/int case: the suite expects
  `[True, False, 0, 1]` for `[True, False, True, 0, 1]`, but
  True equals 1 and False equals 0, so the reference returns
  `[True, False]`.
- Diagnosis: suite defect — the same bool/int equality blind
  spot as run 26 entry 2, in a newly generated suite. This is
  the fourth consecutive run (24–27) with a groq testing_002
  gate failure on this concept class: a persistent
  test-generation weakness, not a scoring defect.
- Monitoring item (carries forward): watch future groq
  testing_002 suites for bool/int equality cases.
- Confidence: high — verified by execution.

## 12. coding_001 (palindrome linked list) — Groq — execution_error

- Run: 27. Provider/model: groq / openai/gpt-oss-120b. Row:
  score 0.0, status error, latency 4,189 ms. Artifact:
  `coding_001_palindrome_linked_list__groq__20261031-143938.md`.
- Failure stage: collection (import). The test file imports
  module-level `is_palindrome` and `ListNode`, but the
  submission defines only `is_palindrome`; `ListNode` is absent,
  so pytest fails at collection: `ImportError: cannot import
  name 'ListNode'`.
- Algorithm vs interface (measured, not just inspected): with
  ONLY a `ListNode` definition added and the algorithm
  untouched, all 7 problem tests pass. Same shape as entry 5
  (GLM, run 26).
- Verdict: model-side interface failure. The submission still
  scores 0 — the required interface is part of the task.
- Confidence: high — failure verified by execution; algorithm
  correctness measured by the adapted run.

## 13. debugging — OpenRouter — execution_error; truncated_at_cap

- Run: 27. Provider/model: openrouter /
  cohere/north-mini-code:free. Two rows, both score 0.0, status
  error: debug_001 (latency 62,664 ms, artifact
  `debug_001_binary_search_off_by_one__openrouter__20261031-144116.md`)
  and debug_003 (latency 74,399 ms, artifact
  `debug_003_race_condition__openrouter__20261031-144145.md`).
- Failure stage: collection (import). Both stored responses
  are EMPTY (zero visible characters) with the truncation flag
  set, so the executed modules define nothing: `ImportError:
  cannot import name 'binary_search'` and `ImportError: cannot
  import name 'Counter'` respectively.
- Relation to entry 6: a stronger instance of the same
  mechanism. Run 26 left 65 visible characters; run 27 left
  none — exactly what the probe-demonstrated reasoning-budget
  mechanism predicts when reasoning consumes the full 8192
  budget. Same stated limit: run 27's own reasoning counts
  were never stored, so these instances are strongly
  consistent, not directly proven.
- Monitoring item (carries forward): repeated reasoning-budget
  truncation (run 26 fragment, run 27 two empty responses).
  Per-attempt proof needs future token-usage capture (a
  ProviderResult extension — a new feature, not a reopening).
  No cap change is justified by this evidence.
- Confidence: failure verified by execution (high); mechanism
  consistent but unproven per attempt (stated limit).

## Run 27 integrity note

- No benchmark defect is identified by any run-27 artifact.
  Strict-gate behavior is confirmed as designed: a gate
  failure scores 0 with mutants unrun and kills NULL;
  interface failures remain model-output failures;
  truncations remain valid evaluations with potentially zero
  scores, not request failures. Model failure, defective
  suite, and infrastructure failure remain three distinct
  events in reporting.
- Nothing in entries 7–13 changes any score, classification,
  provider configuration, or the run-26 baseline.

## Items closed (previously open)

- OpenRouter token accounting (entry 6): CLOSED 2026-10-31 by
  probe v1.1 evidence (see entry 6). Mechanism demonstrated;
  run-26 instance consistent but unproven by the unrecoverable
  record; no further action.
- Failure-attribution labels: CLOSED 2026-10-31. Decision adopted
  (report-side display mappings only) and implemented: the report
  display-mapping patch was built, installed (overwrite report.py
  only), and verified live (13/13 mapping cases, 60/60 fail-fast
  checks, audit PASS on run 26). Stored error types and audit
  classification unchanged. Note: `reference_impl_failed` already
  IS the reference-validation-failure label; mutation-not-run is a
  consequence of the gate failing, not a separate failure kind.
- Audit chain: runs 23, 24, 25, 26, 27 audited (all PASS; run
  27 confirmed 2026-10-31). Demo stays on run 14.

## How to add an entry

Copy the per-entry format: run, task, provider/model, row
(score/status/latency), artifact filename, failure stage,
reproduced evidence (pytest counts and exact failing assertions
or collection errors), diagnosis, confidence. Mark confidence
"verified by execution" only when the artifact's code was actually
run; otherwise say "inspection" and say what would verify it.
