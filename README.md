# AI-Benchmark

A personal model selector: it benchmarks free-tier LLMs on coding,
debugging, testing, and thinking/planning, using execution-based
numbers, so you can see which model is currently best at each job
instead of guessing from marketing.

Everything here runs on free tiers only. No provider in this project
is ever switched to a paid model, and no billing is enabled anywhere.

## What it measures

10 problems in 4 categories (spec target is 15–20 per category; the
set is still growing):

| Category | Problems | How it is scored |
|---|---|---|
| Coding | 3 | Model code run against a pytest suite: passed ÷ (passed + failed + errors) |
| Debugging | 3 | Same execution-based pass rate on buggy code |
| Testing | 2 | Reference gate first (suite must pass a known-correct reference, or the whole problem scores 0.0), then mutants killed ÷ 3 |
| Thinking / Planning | 2 | Scored by a separate judge model (never the same family as the models under test) |

Per provider, three numbers are reported: **blended** (mean over all
attempted, request failures count as 0), **capability** (mean over
valid evaluations only), and **reliability** (valid ÷ attempted).
The current pick per category is the highest blended score, with
lowest mean latency as the tiebreak. Latency never enters a score.

The full measurement rules, including the four kinds of 0.0 and the
testing gate cliff, are in `plan.md` and on the dashboard's
methodology page.

## Current configuration

| Provider | Model | Notes |
|---|---|---|
| Ollama Cloud | `gemma4:31b-cloud` | Concurrency 1 |
| OpenRouter | `nvidia/nemotron-3.5-lightning:free` | Concurrency 2; experimental, promotion withheld (see below) |
| NVIDIA | `nvidia/nemotron-3-ultra-550b-a55b` | Concurrency 2 |
| Groq | `openai/gpt-oss-120b` | Concurrency 2 |
| Zhipu | `glm-4.7-flash` | Concurrency 1 (free-tier rate limit) |
| Judge | `gemini-3.5-flash-lite` | Separate model family from the models under test |

Code completions are capped at 8,192 tokens, thinking/planning at
4,096. Providers retry only on 429/502/503 (max 3 attempts).
Hugging Face was removed on 2026-10-27 (402 / no credits).

## Quickstart

Requires Python 3.10+.

```powershell
pip install -e .
```

Set the provider keys as environment variables (never in a file):

```powershell
$env:OPENROUTER_API_KEY = '...'
$env:NVIDIA_API_KEY = '...'
$env:GROQ_API_KEY = '...'
$env:ZAI_API_KEY = '...'
$env:GEMINI_API_KEY = '...'
```

Then:

```powershell
bench doctor    # checks keys and the local setup
bench run       # one full run across all providers and problems
bench report    # latest run as a table
bench trend     # how picks moved across runs
```

Results land in `history.db` (SQLite). The committed `history.db`
holds 31 runs / 1,494 result rows, so the dashboard works immediately
with real data. Run 14 is the demo run, run 26 is the audited
baseline, run 31 is the latest run and the first with
thinking/planning evidence captured.

## Dashboard

```powershell
pip install -r requirements-gui.txt
python app.py
```

Open http://127.0.0.1:5000. Read-only: it never writes scores. All
styling is bundled locally in `static/`, so it works with no
internet connection. Details in `docs/GUI-v1.7.md`.

## Layout

```
aibenchmark/        engine, providers, evaluators, history, sandbox
problems/           the 10 problem definitions + their pytest suites
app.py, templates/  Flask dashboard (GUI v1.7, Score Breakdown)
static/             Bootstrap + Chart.js, bundled locally
tests/              pytest tests (tests/test_history.py, test_gui_v17.py)
scripts/            manual scratch / diagnostic scripts, not pytest tests
failure_artifacts/  failure evidence the dashboard browses
tp_artifacts/       captured thinking/planning evidence (run 31)
history.db          31 runs of results (committed sample data)
plan.md             the read-only spec the implementation follows
DIAGNOSES.md        what went wrong, what was proved, what is still open
CHANGES.md          change log
```

`scripts/` is history, not product: its own README explains the
rules (run from the project root; never move its `test_*.py` files
into `tests/`, or pytest will collect scripts that call providers).

## Status and honest limits

- Run 31 (2026-11-02) is the latest run; the audit chain for runs
  23–31 passes.
- OpenRouter's Lightning model swept all four categories in runs
  29–31 but its promotion is **withheld**: only two sweeps plus one
  partial, and its thinking/planning 1.00s rest on truncated plans.
  It stays experimental.
- Problem set is 10, not the spec target of 15–20 per category.
- Runs 11–26 have no per-test counts and runs 11–27 no per-test
  identities — the dashboard shows those as "not recorded", never
  as zero.
- Single machine, single author, free tiers: a clean run is not
  statistically established reliability.

`DIAGNOSES.md` is the running record of what was measured, what was
inferred, and what can actually be proved.
