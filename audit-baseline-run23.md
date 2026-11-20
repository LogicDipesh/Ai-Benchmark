# AI-Benchmark reporting baseline — Run 23 (validated)

Preserved 2026-10-30: the first run whose report was verified against
the real database end to end. Future runs compare against this
baseline; any scoring, classification, cap, or prompt change gets a
NEW labeled baseline, never a silent edit of this one.

## Audit result

- Command: `python audit_report.py` (latest run) on the real
  `history.db` — **PASS, all checks passed for run 23 (50 rows)**.
- What the audit verified: blended Score, Capability, Reliability,
  Valid counts, mean Latency, Current picks, the invariant S = C x R
  (full precision), and model/category coverage, recomputed from raw
  rows and compared against the generated report text.
- Caveat (printed by the audit itself): this validates the report
  GIVEN the classification rule below; the rule is a reviewed design
  decision, not something the audit independently proves.

## Report version and policy (as validated)

- Report: capability/reliability tables + clarity legend + allowlist
  classifier (audit bundle).
- Classification (allowlist): a row is a VALID evaluation when its
  score was measured from model output — empty error, or
  `truncated_at_cap`, `execution_error`, `reference_impl_failed`,
  `no_tests_ran`, `sandbox_timeout`. Everything else (HTTP errors,
  connection errors, timeouts, judge errors, missing keys,
  retry-exhausted, unknown names) is a request failure excluded from
  capability.
- Blended Score counts request failures as 0. Current pick = highest
  blended Score (expected value per attempted task) — the pick serves
  pipeline assignment, where a non-answer is a failure to deliver.
- Latency = mean across attempted tasks in the category, each task's
  latency including retry waits; wall time is measured separately.

## Run 23 configuration (what these numbers were measured under)

- Caps 4096 (code categories + plans); default temperature; stricter
  code-only prompt (the run-22 prompt baseline); within-provider
  parallelism (ollama cap 1, others cap 2); session reuse.
- Judge: gemini-3.5-flash-lite, zero judge errors (4th straight run).
- Ollama slot: gemma4:31b-cloud (runs 21+; runs 11–20 used the local
  3B model and are NOT comparable for that slot).
- TP is under the Lite judge (new baseline vs runs 11–19, which used
  gemini-2.5-flash — do not compare TP means across the switch).
- Wall time 323.6 s (5.4 min).

## Run 23 results (blended / capability / reliability / valid)

Picks: Coding Groq, Debugging Groq, Testing Gemma, Thinking-Planning Gemma.

### Coding (mean latency ms in brackets)

- groq: 1.00 / 1.00 / 100% / 3/3 [2335]
- gemma (ollama): 1.00 / 1.00 / 100% / 3/3 [2382]
- openrouter: 1.00 / 1.00 / 100% / 3/3 [25260]
- nvidia: 0.67 / 0.67 / 100% / 3/3 [28433]
- glm (zhipu): 0.33 / 1.00 / 33% / 1/3 [91565]

### Debugging

- groq: 1.00 / 1.00 / 100% / 3/3 [1193]
- gemma: 1.00 / 1.00 / 100% / 3/3 [1719]
- nvidia: 1.00 / 1.00 / 100% / 3/3 [14151]
- openrouter: 0.33 / 0.33 / 100% / 3/3 [29868]
- glm: 0.00 / — / 0% / 0/3 [47537]

### Testing

- gemma: 1.00 / 1.00 / 100% / 2/2 [2471]
- groq: 1.00 / 1.00 / 100% / 2/2 [2517]
- openrouter: 1.00 / 1.00 / 100% / 2/2 [12783]
- nvidia: 0.50 / 0.50 / 100% / 2/2 [64012]
- glm: 0.33 / 0.67 / 50% / 1/2 [49754]

### Thinking-Planning (subjective — LLM-judged)

- gemma: 1.00 / 1.00 / 100% / 2/2 [7333]
- groq: 1.00 / 1.00 / 100% / 2/2 [9285]
- openrouter: 1.00 / 1.00 / 100% / 2/2 [60274]
- nvidia: 1.00 / 1.00 / 100% / 2/2 [132415]
- glm: 0.50 / 1.00 / 50% / 1/2 [32511]

## Standing notes

- GLM is the only provider in run 23 where capability differs from
  blended — every other provider is 100% reliable here, so their
  scores were already clean.
- OpenRouter debugging 0.33 is genuine capability/behavioural
  weakness (one sandbox-timeout hang + one truncation, both valid),
  not an infrastructure artifact.
- NVIDIA testing_002 `reference_impl_failed` is a model failure (its
  suite fails against the known-correct reference); proven by other
  providers passing the same problem in the same run.
