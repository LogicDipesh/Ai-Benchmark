"""One-minute test for the new judge model (Gemini 3.5 Flash Lite).

Save in the project root (E:\\AI-Benchmark), run it, then delete or
move to scripts/. Burns exactly ONE judge request on the new model's
fresh 500/day budget. No keys in this file: the judge module reads
GEMINI_API_KEY from the environment, as always.

If the model ID is wrong, the API returns 404 and this script prints
the full error at once — that is the signal to switch JUDGE_MODEL to
the fallback "gemini-3.1-flash-lite" (identical limits) and re-test.
If it prints a score, the new judge works and a full run is safe to
start (TP scores under this judge are a new baseline — they are NOT
comparable to the old Gemini 2.5 Flash judge's TP scores).
"""
import os
import sys

if not os.environ.get("GEMINI_API_KEY"):
    print("GEMINI_API_KEY is MISSING in this window. Set it (persistently, "
          "as for the other provider keys) and run this again.")
    sys.exit(1)

from aibenchmark.categories.thinking_planning import (
    JUDGE_MODEL,
    judge_response,
)

SAMPLE_PLAN = """Plan: add a cache layer in front of the database.
1. Put an in-memory cache (Redis) between the API and the database.
2. Cache reads by key with a 5-minute TTL; invalidate on writes.
3. Roll out behind a flag, monitor hit rate and latency, roll back
   by disabling the flag if errors rise."""

RUBRIC = """Score 1.0 if the plan names a caching layer, an invalidation
strategy, and a rollback step. Score 0.5 if one element is missing.
Score 0.0 otherwise."""

print(f"Judge model: {JUDGE_MODEL}")
try:
    score = judge_response(SAMPLE_PLAN, RUBRIC)
    print(f"Judge OK — score: {score}")
    print("The new judge works. A full bench run is safe to start.")
except Exception as e:  # noqa: BLE001 — test script: show the whole error
    print(f"Judge FAILED — {type(e).__name__}: {e}")
    print("If this is a 404 for the model ID, switch JUDGE_MODEL to "
          '"gemini-3.1-flash-lite" and re-test. Do NOT start a full run '
          "on a failing judge — every plan would record judge_error.")
    sys.exit(1)
