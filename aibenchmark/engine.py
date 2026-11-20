"""Benchmark engine — provider-parallel version (latency fix).

WHAT CHANGED AND WHY (run 14 proved the old design was the bottleneck):
  The old engine ran evaluations one at a time — category, then
  problem, then provider — so a full run's wall time was the SUM of
  all 50 provider latencies. Run 14's provider latencies alone sum
  to ~49 minutes (coding 17, debugging 10, testing 7, thinking-
  planning 15), before judge calls and sandbox time. No single
  provider was that slow; the sequence was.

  This version runs one worker thread PER PROVIDER (up to 5). Each
  provider's evaluations still run SEQUENTIALLY inside its own
  worker, in the same category/problem order as before, so:
    * a provider never calls itself concurrently (GLM's ~1 req/sec
      free tier, Ollama's single local CPU, and per-provider rate
      limits are all respected);
    * different providers run concurrently, because they are
      different services — Groq waiting does not block NVIDIA.
  Wall time becomes roughly the SLOWEST provider's total, not the
  sum of all five. With run-14 numbers that is roughly a 2–3x
  improvement, dominated by Ollama's local CPU time.

WHAT DID NOT CHANGE (fairness):
  * Same categories, problems, order, prompts, models, scoring and
    containment as the old engine: one crashing evaluation still
    becomes one error row, never an aborted run.
  * Database inserts still happen one row at a time, but now in the
    MAIN thread as evaluations complete, so there is no concurrent
    SQLite writing and no "database is locked" risk. If the run
    crashes part-way, completed evaluations are already saved.
  * Result order in the database is completion order, not the old
    fixed order. Nothing that reads results depends on row order:
    the report groups by provider, the GUI sorts by problem and
    provider, and the contamination check groups by provider/model/
    category. Scores, latencies and error strings are untouched.
  * Judge calls are serialised by a lock in thinking_planning.py,
    so 5 provider threads cannot burst Gemini's free-tier rate
    limit at once (the run-13 judge-429 lesson).

  2026-10-30 API OPTIMISATION (within-provider parallelism):
  Each provider may now run up to MAX_CONCURRENT_PER_PROVIDER
  calls at once (2 for cloud providers, 1 for ollama). This is
  implemented as a per-provider Semaphore, not a restructure:
  the worker code is unchanged except for acquiring a semaphore
  slot instead of a lock. Database inserts still happen in the
  MAIN thread as evaluations complete, and judge calls are still
  serialised by their lock. Lock ordering is consistent
  (provider slot -> judge lock, never reversed), so no deadlock.
  Pool size is the sum of caps, so a task waiting on a slot can
  never starve the pool. Expected effect (run-21 numbers, if no
  429s): NVIDIA ~599s -> ~320s, wall ~627s -> ~350s. If run 22
  shows new 429s for a provider, drop that provider's cap to 1.
"""
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from aibenchmark.categories.coding import evaluate_coding, list_coding_problems
from aibenchmark.categories.debugging import evaluate_debugging, list_debugging_problems
from aibenchmark.categories.testing import evaluate_testing, list_testing_problems
from aibenchmark.categories.thinking_planning import evaluate_thinking_planning, list_thinking_planning_problems
from aibenchmark.providers import PROVIDERS
from aibenchmark.history import create_run, insert_result
from aibenchmark.contamination import check_contamination


CATEGORY_MODULES = {
    "coding": (evaluate_coding, list_coding_problems),
    "debugging": (evaluate_debugging, list_debugging_problems),
    "testing": (evaluate_testing, list_testing_problems),
    "thinking-planning": (evaluate_thinking_planning, list_thinking_planning_problems),
}


# 2026-10-30 API optimisation: max concurrent calls per provider.
# ollama stays at 1 (Ollama Cloud Free allows 1 concurrent request,
# documented). Cloud providers run at 2 as an experiment: their
# free-tier RPM/concurrency limits are unpublished, so 2 is a
# starting point, not a proven-safe value — retries still protect
# 429s, and any provider that 429s in run 22 drops back to 1.
# Unknown providers default to 1 (safe). Revert everything to the
# old sequential behaviour by setting every cap to 1.
MAX_CONCURRENT_PER_PROVIDER = {
    "ollama": 1,
    "openrouter": 2,
    "nvidia": 2,
    "groq": 2,
    # GLM cap-1 experiment (was 2): controlled test of the 1302 /
    # 7-429 pattern in runs 23+24. If 1302 persists at cap 1, it is
    # Zhipu-side, not concurrency. Revert to 2 to restore run-24 rates.
    "zhipu": 1,
}


def _evaluate_one(category_name, evaluate_fn, problem, provider_name, model):
    """One evaluation, with the old engine's containment. Returns
    (result_dict, warning_or_None). Runs inside a provider worker."""
    problem_id = (
        problem.get("id", "unknown")
        if isinstance(problem, dict)
        else "unknown"
    )
    try:
        result = evaluate_fn(problem, provider_name, model)
        return result, None
    except Exception as e:
        result = {
            "problem_id": problem_id,
            "model": model,
            "provider": provider_name,
            "category": category_name,
            "score": 0.0,
            "latency_ms": 0,
            "status": "error",
            "error_type": f"error: {type(e).__name__}",
        }
        warning = (
            f"Warning: {category_name}/{problem_id} "
            f"{provider_name}/{model} crashed "
            f"({type(e).__name__}: {e}); recorded as error."
        )
        return result, warning



def _maybe_write_tp_artifact(run_id, result):
    """Observational TP capture (2026-11-02, run 31). Runs AFTER the
    result row is saved, in the main thread, so a failure here can
    never change the benchmark outcome, the stored row, or any
    score/classification/ranking. The import is lazy so a partial
    install (tp_artifacts.py missing) degrades to a stderr warning
    instead of breaking the whole run."""
    capture = result.get("tp_capture")
    if capture is None:
        return
    try:
        from aibenchmark.tp_artifacts import write_tp_artifact
        path = write_tp_artifact(run_id, result, capture)
    except Exception as e:
        print(
            f"Warning: TP artifact write failed for run {run_id} "
            f"({type(e).__name__}: {e}); result is still saved.",
            file=sys.stderr,
        )
        return
    if path is None:
        print(
            f"Warning: TP artifact write failed for run {run_id} "
            f"(writer returned None); result is still saved.",
            file=sys.stderr,
        )


def run_all(notes: str = "") -> int:
    started = time.time()
    run_id = create_run("history.db", notes)

    # Build the task list in the old deterministic order first.
    tasks = []
    for category_name, (evaluate_fn, list_fn) in CATEGORY_MODULES.items():
        try:
            problems = list_fn()
        except Exception as e:
            print(
                f"Warning: could not list {category_name} problems "
                f"({type(e).__name__}: {e}); skipping category.",
                file=sys.stderr,
            )
            continue
        for problem in problems:
            for provider_name, provider_info in PROVIDERS.items():
                for model in provider_info["models"]:
                    tasks.append((category_name, evaluate_fn, problem,
                                  provider_name, model))

    # One semaphore per provider, sized by MAX_CONCURRENT_PER_PROVIDER.
    # At most that many in-flight evaluations per provider, any
    # number of providers in flight at once.
    provider_slots = {
        provider_name: threading.Semaphore(
            MAX_CONCURRENT_PER_PROVIDER.get(provider_name, 1)
        )
        for provider_name in PROVIDERS
    }

    def worker(task):
        category_name, evaluate_fn, problem, provider_name, model = task
        with provider_slots[provider_name]:
            return _evaluate_one(category_name, evaluate_fn, problem,
                                 provider_name, model)

    all_results = []
    max_workers = sum(
        MAX_CONCURRENT_PER_PROVIDER.get(name, 1) for name in PROVIDERS
    )
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(worker, task) for task in tasks]
        for future in as_completed(futures):
            result, warning = future.result()
            if warning:
                print(warning, file=sys.stderr)
            # Single-threaded insert: no concurrent SQLite writes.
            insert_result(
                "history.db",
                run_id,
                result["provider"],
                result["model"],
                result["category"],
                result["problem_id"],
                result["score"],
                result["latency_ms"],
                result["status"],
                result.get("error_type"),
                result.get("evidence"),
            )
            # Observational TP capture: the row above is already
            # saved; this write cannot change it.
            _maybe_write_tp_artifact(run_id, result)
            all_results.append(result)

    try:
        check_contamination(run_id, all_results)
    except Exception as e:
        print(
            f"Warning: contamination check failed "
            f"({type(e).__name__}: {e}); run results are still saved.",
            file=sys.stderr,
        )
    wall_s = time.time() - started
    print(f"Run #{run_id} wall time: {wall_s:.1f}s "
          f"({len(all_results)} evaluations).")
    return run_id
