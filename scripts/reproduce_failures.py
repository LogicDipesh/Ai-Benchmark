"""Reproduce the run-25 failure pairs and print what the models
produce now, with their artifacts.

Pairs (the failures called out after run 25):
  * coding_001_palindrome_linked_list on nvidia (execution_error,
    3 runs straight: 23, 24, 25)
  * testing_002_dedupe_preserve_order on nvidia
    (reference_impl_failed, 7 runs straight: 19-25)
  * testing_002_dedupe_preserve_order on groq
    (reference_impl_failed, 2 runs straight: 24, 25)

Run from the project root (E:\\AI-Benchmark):
    python reproduce_failures.py
Then delete or move to scripts/.

What it costs and what it does NOT do:
  * It burns exactly 3 provider calls (nvidia x2, groq x1) and runs
    the sandbox locally 3 times. No judge calls.
  * It does NOT touch history.db: no run is created, no row is
    inserted, the report and trend are unaffected. It calls the
    evaluators directly, bypassing the engine (so no semaphores, no
    DB, no contamination check).
  * It re-generates outputs under the CURRENT installed config
    (8192 code caps, code-only prompt). It does NOT replay run 25's
    exact outputs — those were never stored. A pair that passes on
    reproduction is itself information (output variance at default
    temperature); a pair that fails the same way shows its current
    failing output in the artifact.

How it finds artifacts (needs the failure-artifacts patch
installed): before each call it snapshots the failure_artifacts/
filenames; after the call it prints the content of any NEW file for
that problem+provider. If the pair passes (score 1.0), no artifact
is written by design. If the pair fails but no new artifact appears,
the artifacts patch is not installed (or its write failed — the
helper prints a warning in that case).
"""

import os

from aibenchmark.categories.coding import evaluate_coding, list_coding_problems
from aibenchmark.categories.testing import evaluate_testing, list_testing_problems
from aibenchmark.providers import PROVIDERS

ARTIFACT_DIR = "failure_artifacts"

# (category, problem_id, provider)
PAIRS = [
    ("coding", "coding_001_palindrome_linked_list", "nvidia"),
    ("testing", "testing_002_dedupe_preserve_order", "nvidia"),
    ("testing", "testing_002_dedupe_preserve_order", "groq"),
]

LOADERS = {
    "coding": (list_coding_problems, evaluate_coding),
    "testing": (list_testing_problems, evaluate_testing),
}


def find_problem(category, problem_id):
    list_fn, _ = LOADERS[category]
    for problem in list_fn():
        if problem["id"] == problem_id:
            return problem
    raise SystemExit(f"problem not found: {problem_id} in {category}")


def artifact_files():
    if not os.path.isdir(ARTIFACT_DIR):
        return set()
    return set(os.listdir(ARTIFACT_DIR))


def main():
    print("Reproducing 3 failure pairs (3 provider calls, no DB writes).")
    print("Models are taken from the registry, not hardcoded.")
    for category, problem_id, provider in PAIRS:
        models = PROVIDERS[provider]["models"]
        assert len(models) == 1, (
            f"{provider} has {len(models)} registry models; this script "
            f"expects exactly one — update PAIRS instead of guessing."
        )
        model = models[0]
        problem = find_problem(category, problem_id)
        _, evaluate_fn = LOADERS[category]
        print("")
        print(f"=== {problem_id} on {provider} ({model}) ===")
        before = artifact_files()
        row = evaluate_fn(problem, provider, model)
        print(f"row: {row}")
        new = sorted(
            f for f in (artifact_files() - before)
            if f.startswith(f"{problem_id}__{provider}__")
        )
        if new:
            for fname in new:
                path = os.path.join(ARTIFACT_DIR, fname)
                print(f"--- artifact: {path} ---")
                with open(path, encoding="utf-8") as f:
                    print(f.read())
        elif row["score"] == 1.0:
            print("PASSED on reproduction: no artifact is written for a "
                  "1.0 by design. The run-25 failure did not reproduce "
                  "under the current config (output variance).")
        else:
            print("FAILED but no new artifact appeared: the "
                  "failure-artifacts patch is probably not installed "
                  "(its helper prints a warning when a write fails).")
    print("")
    print("Done. history.db untouched; no run created.")


if __name__ == "__main__":
    main()
