# AI-Benchmark v2 — Personal Model Selector — BUILD PLAN

STATUS: READ-ONLY SPEC. Do not add scope, features, or abstractions
beyond what is written here. If a task seems to require something
not listed in this document, STOP and ask the user — do not infer,
do not "future-proof," do not build a general framework where a
specific function would do.

This is a fresh build. Nothing is ported from any previous version
of this project. No file, module, or pattern from any prior codebase
should be referenced, copied, or used as inspiration.

---

## 1. Purpose

A CLI tool that answers one question with real, execution-based
numbers instead of reputation or vendor marketing: **which free-tier
LLM is currently best at coding, thinking/planning, debugging, and
testing** — so the answer can directly drive model assignments in a
separate 6-agent coding pipeline (Orchestrator, Code Writer, Test
Writer, Debugger, Docs Writer, Reviewer).

This tool exists to be run periodically (manually or via a simple
scheduled job) whenever new free-tier models are released, so the
user never has to manually re-evaluate models by hand.

## 2. Explicit non-goals

Do not implement any of the following, even partially, even as an
unused stub:

- No routing engine, fallback strategy framework, or circuit breaker
- No provider certification/tier system (platinum/gold/silver/etc.)
- No cost or token accounting of any kind (all providers are free tier)
- No calibration or bias-detection engine
- No parallel execution coordinator
- No config-generation for any third-party router (LiteLLM etc.)
- No plugin marketplace / dynamic plugin discovery beyond a simple
  Python dict registry
- No web UI, dashboard, or API server — CLI only
- No multi-format reports (JSON/CSV) unless a specific downstream
  consumer is named in a future revision of this document

## 3. Providers (5, fixed list)

Each provider is a small module implementing one function:
`run_prompt(model: str, prompt: str) -> ProviderResult` where
`ProviderResult` includes the raw text response, success/failure
status, latency, and error type if any.

- Ollama (local)
- OpenRouter
- Hugging Face Inference
- NVIDIA
- Groq

No abstract base class hierarchy is required — a `Protocol` or even
just a consistent function signature per module is sufficient.

## 4. Categories (4, fixed list)

- `coding` — generate a solution to a stated problem
- `debugging` — given broken code + a failing test, produce a fix
- `testing` — given a function, write tests that meaningfully cover it
- `thinking-planning` — reasoning/planning tasks with no single
  executable ground truth

Do not add categories. If the user wants a 5th category later, that
is a deliberate future decision, not something to anticipate now.

## 5. Evaluation method

- `coding`, `debugging`, `testing`: **execution-based only**. Run the
  model's output against a real test suite in a sandboxed subprocess.
  Score = pass rate (0.0–1.0). No LLM grading these three categories,
  ever — it must be possible to explain a score with no reference to
  any AI's opinion.
- `thinking-planning`: LLM-as-judge is acceptable here because there
  is no executable ground truth. Every report row for this category
  must be labeled `(subjective — LLM-judged)` so it is never confused
  with the objective scores above.

## 5a. Per-category execution logic

- coding / debugging: send the YAML's `prompt` field (for debugging,
  concatenate `prompt` + `broken_code`) to the provider along with a
  fixed instruction to return only a single Python code block, no
  prose. Extract the code, write it as solution.py, write the YAML's
  `test_file` as test_solution.py, run pytest in a subprocess, score =
  passed/total.
- testing: send only the YAML's `prompt` field to the model — never
  send `reference_implementation` or `mutants`, those are the answer
  key. Extract the returned test code as test_generated.py. Run it
  against `reference_implementation` first (must fully pass, else
  score = 0). Then run it against each entry in `mutants` in turn,
  swapping in that mutant's code as solution.py each time. Score =
  fraction of mutants that cause at least one test to fail.
- thinking-planning: send `prompt` to the model being benchmarked,
  take the raw text response, then send that response plus the YAML's
  `judge_rubric` to one fixed, separate judge model — never a model
  that is also being benchmarked, and never the same model family as
  the one being judged. Judge returns a 0.0–1.0 score.

## 6. Test data

- Hand-written problems only. Nothing scraped from public benchmark
  datasets (HumanEval, MBPP, etc.) — those are contamination risks
  and likely partially memorized already.
- Target: 15–20 problems per category to start. Quality over volume.
- Each problem lives as a YAML file under `problems/<category>/`
  containing: prompt text, starter/broken code (where applicable),
  test file, and a `created` date.
- Rotation policy: on each run, evaluate the full stable set plus
  flag any problem older than 6 months for review/replacement. Do
  not auto-delete — the user reviews and decides.
- If a model's score on problems added in the last month diverges
  sharply (>15 points) from its score on older problems, print a
  contamination warning in the report — do not silently average it away.

## 7. Data model (SQLite)

One database, `history.db`, two tables minimum:

```
runs(id, timestamp, notes)
results(id, run_id, provider, model, category, problem_id,
         score, latency_ms, status, error_type)
```

Keep it this flat. Do not normalize into a dozen tables before
there's a reason to.

## 8. CLI (Click), commands only as listed

- `bench run` — run all providers × models × categories against the
  current problem set, write to `history.db`, print the report
- `bench report [--last N]` — reprint a markdown report from a past
  run without re-executing
- `bench trend --category <name>` — show a model's score over time
  for one category, using history
- `bench doctor` — preflight check for Ollama reachability and API key presence

No other subcommands unless the user asks.

## 9. Output

A single Markdown report per run:

- One table per category: model, provider, score, latency, status
- One line per category: `Current pick: <model> (<provider>)`
- A contamination warning block if triggered (see §6)

That's the only report format. No CSV, no JSON, unless a specific
consumer needs it — see non-goals.

## 10. Directory layout

```
aibenchmark/
  providers/
    ollama.py
    openrouter.py
    huggingface.py
    nvidia.py
    groq.py
  categories/
    coding.py
    debugging.py
    testing.py
    thinking_planning.py
  engine.py          # runs providers x models x problems, collects results
  history.py         # SQLite read/write
  report.py          # markdown report generation
  cli.py             # click entrypoints
problems/
  coding/*.yaml
  debugging/*.yaml
  testing/*.yaml
  thinking_planning/*.yaml
tests/
history.db            # gitignored
```

## 11. Build order

1. Data model + `history.py` (empty DB, one test write/read)
2. One provider (Ollama, since it's local and free of API-key setup
   friction) wired end-to-end through `engine.py` for one category
   (`coding`) with 2–3 hand-written problems
3. Report generation for that single category
4. Add remaining 4 providers
5. Add remaining 3 categories
6. Add `bench trend`
7. Stop. Do not add anything from §2 after this point without the
   user explicitly asking.

## 12. Definition of done

A single command (`bench run`) produces a markdown report showing,
for each of the 4 categories, a ranked list of the 5 providers'
models with objective (or clearly-labeled subjective) scores, and
history persists across runs so `bench trend` works. Nothing more
is required for v1.

## 13. Execution sandboxing

- Every subprocess run of model-generated code gets a hard timeout
  (10 seconds).
- No network access from the sandboxed subprocess.
- Do not proceed to step 2 of the build order until this sandboxing
  is in place — a bad model response returning an infinite loop
  should not hang the whole benchmark run.

