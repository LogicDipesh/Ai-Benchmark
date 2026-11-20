"""Diagnostic artifacts for failed code evaluations.

When a code evaluation scores below 1.0 (a failure OR a partial score —
note that testing's status is "passed" for any score above 0, so the
trigger is the score, not the status), the evaluator calls
write_failure_artifact() with everything it already has: the prompt
sent, the model's raw response, the code that was actually executed,
and the score/status/error. The artifact is a markdown file under
failure_artifacts/ in the project root, named
<problem_id>__<provider>__<UTC timestamp>.md.

What this deliberately does NOT do:
* It never changes a score, a row, or the database. The returned dict
  from the evaluator is untouched; the artifact is a side file only.
* It never raises. Artifact writing must never break a bench run, so
  every failure inside this module degrades to a printed warning.
* It does not store per-test detail (which test failed, pytest
  stdout). The sandbox functions return only score/status/error, so
  that detail is not available to the evaluators. The artifact does
  store the executed code and the test file, so the detail can be
  reproduced by re-running pytest on them (see the note at the end
  of each artifact).
* It does not record a run id. Evaluators never receive one (the
  engine creates it and does not pass it down), so artifacts are
  matched to runs by timestamp + problem + provider.
* Provider failures (no model output) get no artifact: there is
  nothing to store beyond the error already in the row.
* Thinking-planning is not covered: its failures are provider 429s
  (no output) or judged partials, and the investigation that
  motivated this feature concerns code categories only.
"""

import os
from datetime import datetime, timezone

ARTIFACT_DIR = "failure_artifacts"


def _read_best_effort(path):
    """File content, or None when the path is missing/unreadable."""
    if not path:
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def _unique_path(directory, filename):
    """Avoid overwriting when two failures land in the same second."""
    path = os.path.join(directory, filename)
    if not os.path.exists(path):
        return path
    stem, ext = os.path.splitext(filename)
    n = 2
    while True:
        path = os.path.join(directory, f"{stem}-{n}{ext}")
        if not os.path.exists(path):
            return path
        n += 1


def write_failure_artifact(
    *,
    problem_id,
    category,
    provider,
    model,
    score,
    status,
    error_type,
    latency_ms,
    prompt,
    raw_response,
    executed_code,
    test_file=None,
    pre_fix_code=None,
    reference_implementation=None,
    mutant_ids=None,
):
    """Write one artifact file. Returns its path, or None on failure."""
    try:
        os.makedirs(ARTIFACT_DIR, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        filename = f"{problem_id}__{provider}__{stamp}.md"
        path = _unique_path(ARTIFACT_DIR, filename)

        lines = []
        lines.append(f"# Failure artifact: {problem_id} ({category})")
        lines.append("")
        lines.append(f"- Provider: {provider}")
        lines.append(f"- Model: {model}")
        lines.append(f"- Score: {score}")
        lines.append(f"- Status: {status}")
        lines.append(f"- Error: {error_type}")
        lines.append(f"- Latency (ms): {latency_ms}")
        lines.append(f"- Written (UTC): {stamp}")
        lines.append("- Run id: not recorded (evaluators do not receive "
                     "one); match by timestamp + problem + provider.")
        if test_file:
            lines.append(f"- Test file on disk: {test_file}")
        lines.append("")
        lines.append("## Prompt sent")
        lines.append("")
        lines.append("```")
        lines.append(prompt or "")
        lines.append("```")
        lines.append("")
        lines.append("## Raw model response")
        lines.append("")
        lines.append("```")
        lines.append(raw_response or "")
        lines.append("```")
        lines.append("")
        if pre_fix_code is not None:
            lines.append("## Extracted code, before import fix")
            lines.append("")
            lines.append("```python")
            lines.append(pre_fix_code)
            lines.append("```")
            lines.append("")
        lines.append("## Executed code")
        lines.append("")
        lines.append("```python")
        lines.append(executed_code or "")
        lines.append("```")
        lines.append("")
        if reference_implementation is not None:
            lines.append("## Reference implementation (what the suite "
                         "was tested against)")
            lines.append("")
            lines.append("```python")
            lines.append(reference_implementation)
            lines.append("```")
            lines.append("")
        if mutant_ids:
            lines.append(f"## Mutants in this problem: "
                         f"{', '.join(mutant_ids)}")
            lines.append("")
        test_content = _read_best_effort(test_file)
        if test_content is not None:
            lines.append("## Test file content")
            lines.append("")
            lines.append("```python")
            lines.append(test_content)
            lines.append("```")
            lines.append("")
        if category == "testing":
            lines.append("## How to reproduce the detail")
            lines.append("")
            lines.append("The bench ran this suite sandboxed: the "
                         "executed test code was saved as "
                         "test_generated.py, the reference as "
                         "solution.py in a solution_dir, and pytest "
                         "ran with `-v --tb=short` (10 s timeout, "
                         "Python-level network blocked). First the "
                         "suite must pass cleanly against the "
                         "reference, else the row is "
                         "reference_impl_failed; then each mutant's "
                         "code replaces solution.py and the suite "
                         "must fail it to count a kill. To see which "
                         "mutants survived, re-run the suite above "
                         "against the reference and then against "
                         "each mutant from the problem YAML.")
        else:
            lines.append("## How to reproduce the detail")
            lines.append("")
            lines.append("The bench ran this code sandboxed: it was "
                         "saved as solution.py next to the test file "
                         "(copied as test_solution.py) in a fresh "
                         "temp dir, then `python -m pytest "
                         "test_solution.py -v --tb=short` with a 10 s "
                         "timeout and Python-level network blocked. "
                         "To see the per-test detail the row does "
                         "not carry, save the executed code above "
                         "as solution.py, copy the test file next "
                         "to it as test_solution.py, and run the "
                         "same pytest command. If the failure was "
                         "sandbox_timeout, run with a timeout: "
                         "without the sandbox, a hanging solution "
                         "hangs instead of timing out.")
        lines.append("")
        lines.append("Diagnostic only: this file changes no score, "
                     "no row, and no database entry.")
        lines.append("")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return path
    except Exception as e:  # never break a bench run for an artifact
        print(f"[failure_artifacts] WARNING: could not write artifact "
              f"for {problem_id}/{provider}: {e}")
        return None
