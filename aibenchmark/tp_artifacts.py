"""Observational thinking-planning capture artifacts (2026-11-02, run 31).

One JSON file per TP evaluation, written by the engine AFTER the
result row is saved. The file carries the complete model response as
received (including truncation), the provider metadata exactly as
supplied (finish reason, token usage — absent stays absent, never
inferred), the TP prompt and rubric, and the judge's raw output next
to its parsed score.

BOUNDARY (architectural principle, approved 2026-11-02): this module
is observational only. It never feeds scoring, reliability
classification, model selection, or ranking, and it never modifies
historical records. The evaluator stays run-ID unaware by design;
the engine supplies the run ID, so no timestamp-based substitute
for run-ID association is used anywhere in this feature.

FAILURE BEHAVIOUR: write_tp_artifact NEVER raises. It returns the
path written, or None on any failure (unwritable directory, disk
error, malformed capture). The engine prints a stderr warning on
None; the benchmark result is already saved and is unaffected.
"""

import json
import os
from datetime import datetime, timezone

ARTIFACTS_DIR = "tp_artifacts"


def _artifact_path(problem_id: str, provider: str, run_id: int) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    base = f"{problem_id}__{provider}__run{run_id}__{stamp}"
    path = os.path.join(ARTIFACTS_DIR, base + ".json")
    n = 2
    while os.path.exists(path):
        path = os.path.join(ARTIFACTS_DIR, f"{base}-{n}.json")
        n += 1
    return path


def write_tp_artifact(run_id: int, result: dict, capture: dict):
    """Write one TP capture artifact. Never raises; returns the path
    or None. `result` supplies identity (problem, provider, model,
    category); `capture` supplies the observed evidence."""
    try:
        os.makedirs(ARTIFACTS_DIR, exist_ok=True)
        payload = {
            "run_id": run_id,
            "problem_id": result.get("problem_id"),
            "provider": result.get("provider"),
            "model": result.get("model"),
            "category": result.get("category", "thinking-planning"),
            "prompt": capture.get("prompt"),
            "response": capture.get("response"),
            "finish_reason": capture.get("finish_reason"),
            "usage": capture.get("usage"),
            "truncated": capture.get("truncated"),
            "latency_ms": capture.get("latency_ms"),
            "error_type": capture.get("error_type"),
            "rubric": capture.get("rubric"),
            "judge": capture.get("judge"),
            "captured_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        path = _artifact_path(
            result.get("problem_id", "unknown"),
            result.get("provider", "unknown"),
            run_id,
        )
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
        return path
    except Exception:
        return None
