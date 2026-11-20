# TP observational capture — fix note (2026-11-02, for Run 31)

Approved design, implemented against the acceptance conditions set
2026-11-02 ~01:12 IST. No change to the frozen scoring methodology,
no change to any historical run, no change to prompts, caps, judge
model, retry behaviour, or ranking.

## Data flow (as approved)

```
Provider response (finish_reason + usage, as supplied)
      ↓
TP evaluator (categories/thinking_planning.py)
      ├── Score / status / error  (unchanged logic)
      └── Capture dictionary ("tp_capture" key)
                ↓
             Engine (engine.py, main thread, AFTER the row is saved)
                ├── Knows run ID
                └── Writes tp_artifacts/<problem>__<provider>__run<id>__<UTC stamp>.json
```

The evaluator remains run-ID unaware. No timestamp-based substitute
for run-ID association is used. Artifacts live in files, separately
from scoring records (no new database columns).

## What changed

- `aibenchmark/providers/*.py` (all five): `ProviderResult` gains
  `finish_reason` and `usage` (both default None). Cloud providers
  record `choice.finish_reason` and the `usage` object verbatim
  (reasoning-token details preserved when supplied). Ollama records
  `done_reason` and maps its supplied eval counts to the token
  keys when present. Failure paths return the defaults (None).
  Missing metadata stays missing: `total_tokens` is never summed
  from prompt + completion, and an absent usage object stays None.
  The `truncated` flag is unchanged (still derived from
  finish/done "length"); it is not a substitute for finish_reason.
- `aibenchmark/categories/thinking_planning.py`: new
  `judge_response_with_raw` returning (score, raw text, finish
  reason, usage, error string). Transport behaviour is unchanged
  (same spacing, same 502/503 retries, same fail-fast 429); only
  the return shape is new. The raw judge text is returned even
  when parsing fails. `judge_response` is kept as a wrapper
  returning the float (one message nuance: on failure it now
  raises ValueError carrying the formatted error string, where the
  old code raised the raw message; the evaluator's recorded
  `judge_error` strings are identical either way, because the
  evaluator formats from the same error). The evaluator returns
  its existing dict plus a `"tp_capture"` key on BOTH paths
  (provider failure: prompt + failure recorded, judge None).
  The judge call keeps its catch-all: an unforeseen judge-path
  exception still becomes a judge_error row, never a crash.
- `aibenchmark/tp_artifacts.py` (new): JSON artifact writer.
  Never raises; returns the path or None. Filename carries
  problem, provider, run ID, and a UTC stamp (collision suffix
  -2, -3 like failure artifacts).
- `aibenchmark/engine.py`: new `_maybe_write_tp_artifact`, called
  in the main thread after each `insert_result`. The import is
  lazy, so a partial install degrades to a stderr warning instead
  of breaking the run. A failed write warns and never changes the
  saved result.
- `test_tp_capture_equivalence.py` (new, project root): the
  mandatory regression (see below).

## What did NOT change

Scoring, status rules, error classification, the capability/
reliability allowlist, report/audit/GUI code, the TP prompt, the
TP cap (4096), the judge model (gemini-3.5-flash-lite), provider
retry sets, concurrency caps, or any stored row. The old
score-equivalence test is untouched (it covers sandbox wrappers
only, which this patch does not modify).

## Equivalence regression (mandatory before Run 31)

Saved-input fixtures only — no live provider or judge calls. The
provider and judge transports are stubbed; everything else is the
real shipped code. Eight tests, all passing in harness:

1. Non-truncated + full metadata → score/status/error identical
   on/off; artifact matches prompt, response, finish "stop",
   usage, judge raw + parsed score, run ID 999.
2. Truncated + reasoning usage → identical on/off; artifact
   finish "length", truncated true, reasoning detail preserved.
3. Missing metadata → finish None; usage without total_tokens
   stays without it (never summed).
4. Unparseable judge prose → judge_error row, artifact keeps the
   raw prose with score None.
5. Judge 429 fail-fast → judge_error row, artifact judge raw None.
6. Provider failure → connection_error row, artifact with empty
   response and judge None.
7. Legacy provider result (no finish/usage attributes) → NULLs,
   no crash, no invented values.
8. Artifact write deliberately broken (writer pointed at a file)
   → evaluator outcome exactly unchanged, no exception.

## Bases (read before overwriting)

This package was built from the last known-good trees, verified
marker by marker (daily-quota fail-fast, retry (429, 502, 503),
500-char snippets, session reuse, finish_reason flag, judge
Flash-Lite): providers from the api-optimize tree, the TP
evaluator from the judge-flashlite tree, the engine from the
evidence-step-3 tree. No patch after those trees touched these
files (later work was registry, report, sandbox, history, GUI).
If you hand-edited any of these files outside my patches, tell me
before overwriting — a full-file overwrite would lose your edit.

## Install

From `E:\AI-Benchmark`, back up first:

    copy aibenchmark\providers\openrouter.py aibenchmark\providers\openrouter.py.tpcapture-backup
    copy aibenchmark\providers\groq.py aibenchmark\providers\groq.py.tpcapture-backup
    copy aibenchmark\providers\nvidia.py aibenchmark\providers\nvidia.py.tpcapture-backup
    copy aibenchmark\providers\zhipu.py aibenchmark\providers\zhipu.py.tpcapture-backup
    copy aibenchmark\providers\ollama.py aibenchmark\providers\ollama.py.tpcapture-backup
    copy aibenchmark\categories\thinking_planning.py aibenchmark\categories\thinking_planning.py.tpcapture-backup
    copy aibenchmark\engine.py aibenchmark\engine.py.tpcapture-backup

Then overwrite with the package files (same relative paths), copy
`aibenchmark\tp_artifacts.py` (new) and
`test_tp_capture_equivalence.py` (project root), and run:

    python test_tp_capture_equivalence.py

Expect: 8 tests, all OK. Only then run Run 31. After the run,
`tp_artifacts\` holds one JSON per TP evaluation (10 files),
each named with its run ID. The GUI does not display these yet;
open the JSON files directly. That display step, if wanted, is a
separate later change.

## Rollback

Restore the seven `.tpcapture-backup` files, delete
`aibenchmark\tp_artifacts.py` and
`test_tp_capture_equivalence.py`. No database change to undo
(capture writes files only).

## Run 31 documentation (pre-agreed)

Two separately documented changes: model continuity (Lightning
remains in the OpenRouter slot, still experimental, not
promoted) and instrumentation change (TP capture introduced and
verified by this regression). Run 31 is not a perfectly
unchanged repeat, but the instrumentation must not move any
outcome — the regression above is the evidence for that claim.
