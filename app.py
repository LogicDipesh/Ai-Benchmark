"""AI-Benchmark GUI — Flask + Bootstrap admin dashboard. Version 1.7.

HOW THIS FILE CONNECTS TO THE PROJECT (read this before the demo):
  * The interface is Bootstrap 5 (MIT licence, loaded from CDN) with an
    admin-dashboard layout. The template only handles display — it
    knows nothing about benchmarking.
  * This file is the only new Python code. It imports the project's
    EXISTING functions from aibenchmark.history and aibenchmark.report
    and passes their rows into the templates. No scoring, provider,
    sandbox or evaluator code was changed, copied or re-implemented
    here — the GUI only READS history.db, it never writes scores.
  * Version 1.3 adds a methodology page and shared JSON definitions.
    The GUI reuses the report's _is_valid_evaluation and
    _display_error_type helpers; it does not duplicate the report's
    classification or change stored values. Request-failure counts
    are the complement of the report's valid-evaluation allowlist.
  * Version 1.6 adds a per-evaluation test-detail page (run-detail
    "Tests" column): for runs with per-test capture, it lists which
    tests passed and failed as captured during that evaluation
    itself. Rows without captured identities explain why instead of
    inventing names; the page never reconstructs identities.
  * Version 1.7 makes scores clickable (Score Breakdown): a problem
    score opens its detail page with a "How this score was
    calculated" block, and a category score opens a breakdown page
    with every problem score and the averaging formula. No new
    columns, no scoring change: every number comes from the stored
    row and its evidence dict, and unavailable states say so.
  * The one live action, the smoke test, calls the existing Groq
    provider module directly (aibenchmark.providers.groq) with a tiny
    prompt. It is a connectivity check, NOT a bench score, and it is
    labelled as such on screen. A full bench run is deliberately NOT
    a button here: it takes tens of minutes and depends on free-tier
    services, which is exactly what you do not want live in a demo.

HOW TO RUN (from the project root, E:\\AI-Benchmark):
  1. pip install -r requirements.txt
  2. Copy app.py, methodology.json, and the templates/ folder into
     E:\\AI-Benchmark (app.py must sit next to history.db and the
     aibenchmark/ folder).
  3. python app.py
  4. Open http://127.0.0.1:5000 in a browser.

If history.db is missing, the dashboard says so plainly instead of
showing invented numbers.
"""
import os
import json
import re
from pathlib import Path
from collections import defaultdict

from flask import Flask, abort, render_template, request

from aibenchmark.history import get_results_for_run, get_runs
from aibenchmark.providers import groq as groq_provider
from aibenchmark.report import _display_error_type, _is_valid_evaluation

GUI_VERSION = "1.7"

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def fmt_ist(timestamp):
    """Render a stored UTC timestamp as a readable IST time for
    presentation, e.g. '28 Oct 2026, 02:21 PM IST'. Falls back to the
    raw string if parsing fails — never hide a timestamp."""
    try:
        dt = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        return dt.astimezone(IST).strftime("%d %b %Y, %I:%M %p IST")
    except Exception:
        return str(timestamp)


def sorted_summary(summary, category):
    """Dashboard rows for one category, best first: highest mean
    score, ties broken by lowest mean latency (the report's
    'current pick' breaks ties arbitrarily — this does not)."""
    rows = [row for (cat, _), row in summary.items() if cat == category]
    rows.sort(key=lambda r: (-r["score"], r["latency_ms"]))
    return rows


def current_picks(summary):
    """Best provider per category, same ordering as sorted_summary."""
    picks = {}
    for category in CATEGORIES:
        rows = sorted_summary(summary, category)
        if rows:
            picks[category] = rows[0]
    return picks

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, "methodology.json"), encoding="utf-8") as _f:
    METHODOLOGY = json.load(_f)
DB_PATH = os.path.join(BASE_DIR, "history.db")
# Read-only evidence directory. Override only when artifacts live elsewhere.
FAILURE_ARTIFACTS_DIR = Path(os.environ.get(
    "AIBENCHMARK_FAILURE_ARTIFACTS_DIR",
    os.path.join(BASE_DIR, "failure_artifacts"),
))
ARTIFACT_NAME_RE = re.compile(
    r"^(?P<problem>[A-Za-z0-9_-]+)__(?P<provider>[A-Za-z0-9-]+)__(?P<stamp>\d{8}-\d{6})\.md$"
)
MAX_ARTIFACT_BYTES = 1_000_000

CATEGORIES = ["coding", "debugging", "testing", "thinking-planning"]
PROVIDER_COLORS = {
    "ollama": "#6c757d",
    "openrouter": "#0d6efd",
    "nvidia": "#198754",
    "groq": "#fd7e14",
    "zhipu": "#6f42c1",
}

def _evidence_suffix(counts):
    """Parenthetical detail for non-clean counts, e.g. ' (1 failed)'.
    Clean rows render without a suffix."""
    parts = []
    if counts.get("failed"):
        parts.append(f"{counts['failed']} failed")
    if counts.get("skipped"):
        parts.append(f"{counts['skipped']} skipped")
    if counts.get("errors"):
        parts.append(f"{counts['errors']} errors")
    return (" (" + ", ".join(parts) + ")") if parts else ""


def evidence_display(evidence):
    """Text + state for the run-detail 'Test counts' cell.

    evidence is the step-3 Result.evidence dict or None. None renders
    'not recorded' (never 0): it covers legacy pre-capture rows,
    provider failures, and plan rows alike, and the legend says so.
    A falsy value (missing attribute on old stubs, empty dict) is
    treated the same way — display must never invent counts.
    Gate-failed testing renders kills as 'not measured', never zero:
    kills is structurally None there. Gate 'not_run' (no tests
    collected) renders as 'gate: no tests', not '0/0'."""
    if not evidence:
        return {"text": "not recorded", "state": "not_recorded"}
    if isinstance(evidence, dict) and "gate_outcome" in evidence:
        outcome = evidence.get("gate_outcome")
        if outcome == "not_run":
            return {"text": "gate: no tests \u00b7 kills not measured",
                    "state": "recorded"}
        gate = evidence.get("gate") or {}
        passed = gate.get("passed")
        collected = gate.get("collected")
        if passed is None or collected is None:
            return {"text": "not recorded", "state": "not_recorded"}
        gate_text = f"gate {passed}/{collected} passed{_evidence_suffix(gate)}"
        if outcome == "passed":
            return {"text": f"{gate_text} \u00b7 killed "
                            f"{evidence.get('mutants_killed')}/{evidence.get('mutants_total')}",
                    "state": "recorded"}
        return {"text": f"{gate_text} \u00b7 kills not measured",
                "state": "recorded"}
    passed = evidence.get("passed") if isinstance(evidence, dict) else None
    collected = evidence.get("collected") if isinstance(evidence, dict) else None
    if passed is None or collected is None:
        return {"text": "not recorded", "state": "not_recorded"}
    return {"text": f"{passed} of {collected} passed{_evidence_suffix(evidence)}",
            "state": "recorded"}


def test_display_name(node_id):
    """Display form of a stored pytest node id: everything after the
    first "::" (file prefix stripped, class + test + parameters
    kept). Works for both separator forms ("../test_generated.py::..."
    on Linux, "..\\test_generated.py::..." on Windows) because the
    split is on "::", never on "/". Falls back to the whole string
    when there is no "::" (should not happen: the parser requires
    one)."""
    if not isinstance(node_id, str):
        return ""
    return node_id.split("::", 1)[-1] if "::" in node_id else node_id


def _not_recorded_reason(row):
    """Why a row has no per-test identities (display text, never a
    guess at names)."""
    if getattr(row, "category", None) == "thinking-planning":
        return "Plan rows carry judge scores, not pytest tests."
    if not _is_valid_evaluation(getattr(row, "error_type", None)):
        return "The attempt failed before evaluation, so no tests ran."
    return "This run predates per-test capture."


def test_detail_state(row):
    """Detail-page state for one result row. Returns (state, tests,
    reason): "recorded" with the list, "no_tests" when pytest ran
    with zero result lines, or "not_recorded" when no identities
    exist. A missing "tests" key (pre-per-test history code) is
    not_recorded, never an empty list: absence of the key means the
    capture never ran, while [] means it ran and found nothing."""
    evidence = getattr(row, "evidence", None)
    if not isinstance(evidence, dict):
        return "not_recorded", None, _not_recorded_reason(row)
    if "tests" not in evidence:
        return "not_recorded", None, _not_recorded_reason(row)
    tests = evidence.get("tests")
    if tests is None:
        return "not_recorded", None, _not_recorded_reason(row)
    if tests == []:
        return "no_tests", [], None
    return "recorded", tests, None


def _is_truncated(error_type):
    return bool(error_type) and "truncated_at_cap" in str(error_type)


def _zero_reason(row, evidence):
    """Plain-language reason for a 0.0 score, or None when the row
    does not score zero. Classification reads only stored values:
    the report allowlist (request failures), the testing gate,
    timeouts, and measured counts. It never invents a cause."""
    if getattr(row, "score", None) != 0.0:
        return None
    error_type = getattr(row, "error_type", None)
    category = getattr(row, "category", None)
    if error_type and "judge_error" in str(error_type):
        return ("Judge error — no plan score exists. Counts as 0 in "
                "blended and is excluded from capability.")
    if not _is_valid_evaluation(error_type):
        return ("Request failure — the model never answered, so no "
                "evaluation exists. Counts as 0 in the blended score "
                "and is excluded from capability.")
    if category == "thinking-planning":
        return "The judge awarded 0 marks for this plan."
    if category == "testing" and isinstance(evidence, dict) \
            and "gate_outcome" in evidence:
        outcome = evidence.get("gate_outcome")
        if outcome == "failed":
            return ("Reference-gate failure — the generated suite "
                    "failed against the known-correct reference, so "
                    "mutant scoring never ran. The problem scores 0 "
                    "by design, however many gate checks passed.")
        if outcome == "not_run":
            return ("Gate did not run — no tests were collected, so "
                    "no score could be measured.")
        if outcome == "passed":
            return "Gate passed, but no mutants were killed."
    if error_type and "sandbox_timeout" in str(error_type):
        return ("Execution timed out — the code exceeded the "
                "10-second sandbox limit. A valid evaluation "
                "scoring 0.")
    if error_type and ("execution_error" in str(error_type)
                       or "no_tests_ran" in str(error_type)):
        return ("The code could not run (collection or execution "
                "error) — no tests passed, so the score is 0.")
    if isinstance(evidence, dict) and "gate_outcome" not in evidence:
        p_ = evidence.get("passed")
        f_ = evidence.get("failed")
        e_ = evidence.get("errors")
        if p_ is not None and f_ is not None and e_ is not None \
                and p_ + f_ + e_ == 0:
            return "No counted tests ran, so the score is 0."
    return "All counted tests failed or errored."


def score_calculation(row):
    """Calculation block for the detail page: title, derivation
    lines, and zero_reason. Presentation only: every number comes
    from the stored row and its evidence dict; nothing is
    recomputed into a score, and unavailable states say so instead
    of inventing a derivation."""
    evidence = getattr(row, "evidence", None)
    error_type = getattr(row, "error_type", None)
    category = getattr(row, "category", None)
    score = getattr(row, "score", None)
    trunc_note = ("Output was truncated at the token limit; scored "
                  "on the code received.") if _is_truncated(error_type) else None
    zero = _zero_reason(row, evidence)
    if category == "thinking-planning":
        if not _is_valid_evaluation(error_type):
            return {"title": "Judge-based calculation — unavailable",
                    "lines": ["No plan score exists: the judge "
                              "request failed."],
                    "zero_reason": zero}
        lines = [f"Judge score = {score:.3f}."
                 if score is not None else "Judge score not recorded.",
                 "LLM-judged against a rubric; criterion-level marks "
                 "are not stored, so no finer breakdown exists."]
        if trunc_note:
            lines.append(trunc_note)
        return {"title": "Judge-based calculation", "lines": lines,
                "zero_reason": zero}
    if isinstance(evidence, dict) and "gate_outcome" in evidence:
        gate = evidence.get("gate") or {}
        gp, gc = gate.get("passed"), gate.get("collected")
        outcome = evidence.get("gate_outcome")
        kills, total = evidence.get("mutants_killed"), evidence.get("mutants_total")
        if outcome == "passed" and gp is not None and gc is not None \
                and kills is not None and total:
            lines = [f"Reference gate passed ({gp}/{gc} checks).",
                     f"Mutants killed: {kills}/{total}.",
                     f"Score = {kills} ÷ {total} = {score:.3f}."]
        elif outcome == "failed" and gp is not None and gc is not None:
            lines = [f"Reference gate failed ({gp}/{gc} passed"
                     f"{_evidence_suffix(gate)}).",
                     "Mutant scoring never ran, so there is no kill "
                     "fraction.",
                     "Score = 0 by design."]
        elif outcome == "not_run":
            lines = ["Reference gate did not run (no tests "
                     "collected).",
                     "Mutant scoring never ran, so there is no kill "
                     "fraction.",
                     "Score = 0."]
        else:
            return {"title": "Testing calculation — unavailable",
                    "lines": ["Gate evidence is incomplete, so no "
                              "derivation is shown."],
                    "zero_reason": zero}
        if trunc_note:
            lines.append(trunc_note)
        return {"title": "Two-stage testing calculation", "lines": lines,
                "zero_reason": zero}
    # Direct (coding / debugging).
    passed = evidence.get("passed") if isinstance(evidence, dict) else None
    failed = evidence.get("failed") if isinstance(evidence, dict) else None
    errors = evidence.get("errors") if isinstance(evidence, dict) else None
    skipped = evidence.get("skipped") if isinstance(evidence, dict) else None
    collected = evidence.get("collected") if isinstance(evidence, dict) else None
    if passed is not None and failed is not None and errors is not None:
        counted = passed + failed + errors
        if counted == 0:
            no_tests_lines = ["No counted tests ran (see the error "
                              "type above).",
                              "Score = 0."]
            if trunc_note:
                no_tests_lines.append(trunc_note)
            return {"title": "Test-based calculation — no tests ran",
                    "lines": no_tests_lines,
                    "zero_reason": zero}
        lines = [f"Score = {passed} ÷ {counted} = {score:.3f}."
                 if score is not None
                 else f"Passed {passed} of {counted} counted tests."]
        if skipped:
            lines.append(f"Skipped: {skipped} (not counted in the "
                         f"denominator).")
        if collected is not None and collected != counted:
            lines.append(f"Collected {collected} tests in total; "
                         f"{counted} counted toward the score.")
        tests = evidence.get("tests")
        if isinstance(tests, list):
            xf = sum(1 for t in tests
                     if isinstance(t, dict)
                     and t.get("status") in ("xfail", "xpass"))
            if xf:
                lines.append(f"Expected-failure markers: {xf} listed, "
                             f"not counted in the score.")
        if trunc_note:
            lines.append(trunc_note)
        return {"title": "Test-based calculation", "lines": lines,
                "zero_reason": zero}
    if not _is_valid_evaluation(error_type):
        return {"title": "Test-based calculation — unavailable",
                "lines": ["No evaluation exists: the model never "
                          "answered, so no tests were measured."],
                "zero_reason": zero}
    if error_type and "sandbox_timeout" in str(error_type):
        return {"title": "Test-based calculation — execution timed out",
                "lines": ["The code exceeded the 10-second sandbox "
                          "limit, so no test counts were measured.",
                          "Score = 0."],
                "zero_reason": zero}
    return {"title": "Test-based calculation — unavailable",
            "lines": ["Counts were not recorded for this evaluation, "
                      "so no derivation is shown."],
            "zero_reason": zero}


def score_basis(row):
    """One-line basis for the breakdown table."""
    evidence = getattr(row, "evidence", None)
    category = getattr(row, "category", None)
    error_type = getattr(row, "error_type", None)
    if category == "thinking-planning":
        return ("Judge score" if _is_valid_evaluation(error_type)
                else "No score (judge error)")
    if isinstance(evidence, dict) and "gate_outcome" in evidence:
        outcome = evidence.get("gate_outcome")
        gate = evidence.get("gate") or {}
        if outcome == "passed":
            return (f"Gate passed, killed {evidence.get('mutants_killed')}"
                    f"/{evidence.get('mutants_total')}")
        if outcome == "failed":
            return (f"Gate failed ({gate.get('passed')}"
                    f"/{gate.get('collected')} passed)")
        if outcome == "not_run":
            return "Gate: no tests"
        return "Gate evidence incomplete"
    if isinstance(evidence, dict):
        p, f, e = (evidence.get("passed"), evidence.get("failed"),
                   evidence.get("errors"))
        if p is not None and f is not None and e is not None:
            return f"{p}/{p + f + e} passed"
    if error_type and "sandbox_timeout" in str(error_type):
        return "Execution timed out"
    if not _is_valid_evaluation(error_type):
        return "No evaluation (request failure)"
    return "Not recorded"


app = Flask(__name__)
app.jinja_env.filters["ist"] = fmt_ist
app.jinja_env.globals["gui_version"] = GUI_VERSION
app.jinja_env.globals["evidence_display"] = evidence_display


def is_request_failure(error_type):
    """Use the report's allowlist as the sole validity authority."""
    return not _is_valid_evaluation(error_type)


def summarize(results):
    """Per (category, provider): mean blended score, mean latency,
    attempt count, and report-classified request-failure count."""
    grouped = defaultdict(list)
    for r in results:
        if r.provider == "contamination_check":
            continue
        grouped[(r.category, r.provider)].append(r)
    summary = {}
    for (category, provider), rows in grouped.items():
        model = rows[0].model
        summary[(category, provider)] = {
            "provider": provider,
            "model": model,
            "score": sum(r.score for r in rows) / len(rows),
            "latency_ms": int(sum(r.latency_ms for r in rows) / len(rows)),
            "count": len(rows),
            "request_failures": sum(1 for r in rows if is_request_failure(r.error_type)),
            # Rows carrying step-3 evidence (getattr: old stubs and
            # pre-step-3 Result objects have no evidence attribute).
            "evidence_recorded": sum(
                1 for r in rows if getattr(r, "evidence", None)),
        }
    return summary


def capability_summary(results):
    """Per (category, provider): capability mean over valid
    evaluations, reliability %, valid/total. Same rule as report.py
    (imported _is_valid_evaluation, not duplicated). Capability is
    None when there are zero valid evaluations — the template
    renders that as an em dash, exactly like the report."""
    grouped = defaultdict(list)
    for r in results:
        if r.provider == "contamination_check":
            continue
        grouped[(r.category, r.provider)].append(r)
    cap = {}
    for (category, provider), rows in grouped.items():
        valid = [r for r in rows if _is_valid_evaluation(r.error_type)]
        cap[(category, provider)] = {
            "provider": provider,
            "model": rows[0].model,
            "capability": (sum(r.score for r in valid) / len(valid))
            if valid else None,
            "reliability": int(round(100 * len(valid) / len(rows)))
            if rows else 0,
            "valid": len(valid),
            "total": len(rows),
        }
    return cap


def cap_by_category(summary, cap):
    """Capability rows per category, in the main table's order
    (highest blended score first, ties by lowest latency) so the
    two tables line up provider for provider."""
    out = {}
    for category in CATEGORIES:
        out[category] = [cap[(category, row["provider"])]
                         for row in sorted_summary(summary, category)
                         if (category, row["provider"]) in cap]
    return out


def parse_artifact_name(filename):
    """Return identifying fields from the established artifact filename.

    Expected: <problem_id>__<provider>__YYYYMMDD-HHMMSS.md
    Artifact files do not contain a run id; the timestamp is only a
    heuristic for associating an artifact with a run-detail row.
    """
    match = ARTIFACT_NAME_RE.match(Path(filename).name)
    if not match:
        return None
    try:
        stamp = datetime.strptime(match.group("stamp"), "%Y%m%d-%H%M%S")
    except ValueError:
        return None
    return {"filename": Path(filename).name,
            "problem_id": match.group("problem"),
            "provider": match.group("provider"),
            "timestamp": stamp}


def list_failure_artifacts():
    """List only flat, convention-matching Markdown artifacts; never write."""
    items = []
    if not FAILURE_ARTIFACTS_DIR.is_dir():
        return items
    for path in FAILURE_ARTIFACTS_DIR.iterdir():
        if not path.is_file() or path.stat().st_size > MAX_ARTIFACT_BYTES:
            continue
        parsed = parse_artifact_name(path.name)
        if parsed:
            parsed["size_bytes"] = path.stat().st_size
            items.append(parsed)
    return sorted(items, key=lambda item: item["timestamp"], reverse=True)


def _run_timestamp_for_matching(timestamp):
    """Convert a stored UTC run timestamp to the UTC-naive basis used by
    artifact filename stamps (the artifact writer stamps in UTC)."""
    try:
        dt = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except (TypeError, ValueError):
        return None


def match_evidence_artifacts(rows, run):
    """Map (problem, provider) to nearest filename timestamp within 24h.

    This is deliberately labeled heuristic: the artifact format has no
    run id, so a match is not a database foreign-key relationship.
    """
    artifacts = list_failure_artifacts()
    target = _run_timestamp_for_matching(getattr(run, "timestamp", None))
    matches = {}
    if target is None:
        return matches
    for row in rows:
        problem = str(getattr(row, "problem_id", ""))
        provider = str(getattr(row, "provider", ""))
        candidates = [a for a in artifacts
                      if a["problem_id"] == problem and a["provider"] == provider]
        if not candidates:
            continue
        nearest = min(candidates, key=lambda a: abs((a["timestamp"] - target).total_seconds()))
        delta = abs((nearest["timestamp"] - target).total_seconds())
        if delta <= 24 * 60 * 60:
            matches[(problem, provider)] = {
                "filename": nearest["filename"],
                "delta_seconds": int(delta),
            }
    return matches


def failure_class_breakdown(results):
    """Count stored-error classes by category.

    The report's validity helper remains the sole request-failure rule.
    The truncation flag is a suffix on the stored value
    ("<base>; truncated_at_cap"), so a combined row counts in BOTH its
    base class and truncation: counting it only as "other" would hide a
    real execution/reference failure, and counting it only as truncation
    would hide the base failure. Standalone values are unaffected.
    Other valid model-output errors (sandbox_timeout, no_tests_ran, ...)
    are retained in their own bucket so no failure disappears.
    """
    empty_counts = {
        "reference_gate": 0, "execution_error": 0, "truncation": 0,
        "request_failure": 0, "other_valid_output": 0,
    }
    grouped = defaultdict(lambda: dict(empty_counts))
    for category in CATEGORIES:
        grouped[category]
    for row in results:
        if row.provider == "contamination_check" or not row.error_type:
            continue
        counts = grouped[row.category]
        if not _is_valid_evaluation(row.error_type):
            counts["request_failure"] += 1
            continue
        parts = [part.strip() for part in str(row.error_type).lower().split(";")]
        truncated = "truncated_at_cap" in parts
        base = next((part for part in parts if part != "truncated_at_cap"), "")
        if base == "reference_impl_failed":
            counts["reference_gate"] += 1
        elif base == "execution_error":
            counts["execution_error"] += 1
        elif base == "":
            pass
        else:
            counts["other_valid_output"] += 1
        if truncated:
            counts["truncation"] += 1
    return dict(grouped)


def read_failure_artifact(filename):
    """Read one allowlisted artifact by basename; reject traversal."""
    if Path(filename).name != filename or not ARTIFACT_NAME_RE.match(filename):
        abort(404)
    path = FAILURE_ARTIFACTS_DIR / filename
    if not path.is_file() or path.stat().st_size > MAX_ARTIFACT_BYTES:
        abort(404)
    return path.read_text(encoding="utf-8", errors="replace")


def category_tables(results):
    """Rows grouped by category, in the fixed category order."""
    grouped = defaultdict(list)
    for r in results:
        if r.provider == "contamination_check":
            continue
        grouped[r.category].append(r)
    for rows in grouped.values():
        rows.sort(key=lambda r: (r.problem_id, r.provider))
    return [(cat, grouped[cat]) for cat in CATEGORIES if cat in grouped]


@app.route("/")
def dashboard():
    runs = get_runs(DB_PATH)
    if not runs:
        return render_template("dashboard.html", runs=[], run=None,
                               summary={}, request_failures_total=0, total_rows=0)
    run = runs[0]  # newest first from get_runs()
    results = get_results_for_run(DB_PATH, run.id)
    summary = summarize(results)
    cap = capability_summary(results)
    request_failures_total = sum(1 for r in results if is_request_failure(r.error_type))
    return render_template("dashboard.html", runs=runs, run=run,
                           summary=summary, request_failures_total=request_failures_total,
                           total_rows=len(results),
                           categories=CATEGORIES,
                           sorted_summary=sorted_summary,
                           picks=current_picks(summary),
                           cap_by_category=cap_by_category(summary, cap),
                           failure_breakdown=failure_class_breakdown(results),
                           methodology=METHODOLOGY)


@app.route("/methodology")
def methodology():
    return render_template("methodology.html", methodology=METHODOLOGY)


@app.route("/runs")
def runs_page():
    runs = get_runs(DB_PATH)
    counts = {}
    for run in runs:
        results = get_results_for_run(DB_PATH, run.id)
        counts[run.id] = {
            "rows": len(results),
            "request_failures": sum(1 for r in results if is_request_failure(r.error_type)),
        }
    return render_template("runs.html", runs=runs, counts=counts)


@app.route("/run/<int:run_id>")
def run_detail(run_id):
    runs = get_runs(DB_PATH)
    run = next((r for r in runs if r.id == run_id), None)
    if run is None:
        abort(404)
    results = get_results_for_run(DB_PATH, run_id)
    summary = summarize(results)
    cap = capability_summary(results)
    request_failures_total = sum(1 for r in results if is_request_failure(r.error_type))
    return render_template("run_detail.html", run=run,
                           tables=category_tables(results),
                           summary=summary, request_failures_total=request_failures_total,
                           total_rows=len(results),
                           cap_by_category=cap_by_category(summary, cap),
                           display_error=_display_error_type,
                           evidence_matches=match_evidence_artifacts(results, run),
                           failure_breakdown=failure_class_breakdown(results),
                           methodology=METHODOLOGY)


@app.route("/run/<int:run_id>/detail/<category>/<problem_id>/<provider>")
def test_detail(run_id, category, problem_id, provider):
    """Per-evaluation test detail: which tests passed and failed, as
    captured during that evaluation itself. Never reconstructs
    identities for rows that never recorded them."""
    if category not in CATEGORIES:
        abort(404)
    runs = get_runs(DB_PATH)
    run = next((r for r in runs if r.id == run_id), None)
    if run is None:
        abort(404)
    results = get_results_for_run(DB_PATH, run_id)
    row = next((r for r in results
                if r.category == category and r.problem_id == problem_id
                and r.provider == provider), None)
    if row is None:
        abort(404)
    state, tests, reason = test_detail_state(row)
    display_tests = None
    has_expected_markers = False
    if tests is not None:
        display_tests = []
        for t in tests:
            name = t.get("name", "") if isinstance(t, dict) else ""
            status = t.get("status", "") if isinstance(t, dict) else ""
            if status in ("xfail", "xpass"):
                has_expected_markers = True
            display_tests.append({"display": test_display_name(name),
                                  "full": name, "status": status})
    counts_text = None
    if state == "recorded":
        counts_text = evidence_display(getattr(row, "evidence", None))["text"]
    matches = match_evidence_artifacts([row], run)
    artifact = matches.get((problem_id, provider))
    group = [r for r in results
             if r.category == category and r.provider == provider
             and r.provider != "contamination_check"]
    group_mean = sum(r.score for r in group) / len(group)
    parts = " + ".join(f"{r.score:.3f}" for r in
                       sorted(group, key=lambda r: r.problem_id))
    contribution = (f"This problem contributes {row.score:.3f} to "
                    f"the {category} mean for {provider}: "
                    f"({parts}) ÷ {len(group)} = {group_mean:.3f}.")
    return render_template("test_detail.html", run=run, row=row,
                           state=state, tests=display_tests, reason=reason,
                           is_testing=(category == "testing"),
                           counts_text=counts_text,
                           has_expected_markers=has_expected_markers,
                           calculation=score_calculation(row),
                           contribution=contribution,
                           display_error=_display_error_type,
                           artifact=artifact)


@app.route("/run/<int:run_id>/breakdown/<category>/<provider>")
def category_breakdown(run_id, category, provider):
    """Category drill-down: every problem score for one provider in
    one category, plus the averaging formula. The mean shown here
    is computed the same way as the dashboard's (all attempts,
    request failures counting as 0); capability is shown alongside
    so a request-failure zero is never mistaken for a measured 0."""
    if category not in CATEGORIES:
        abort(404)
    runs = get_runs(DB_PATH)
    run = next((r for r in runs if r.id == run_id), None)
    if run is None:
        abort(404)
    results = get_results_for_run(DB_PATH, run_id)
    rows = [r for r in results
            if r.category == category and r.provider == provider
            and r.provider != "contamination_check"]
    if not rows:
        abort(404)
    rows.sort(key=lambda r: r.problem_id)
    mean = sum(r.score for r in rows) / len(rows)
    valid = [r for r in rows if _is_valid_evaluation(r.error_type)]
    capability = (sum(r.score for r in valid) / len(valid)) if valid else None
    scores_joined = " + ".join(f"{r.score:.3f}" for r in rows)
    return render_template("breakdown.html", run=run, category=category,
                           provider=provider, model=rows[0].model, rows=rows,
                           mean=mean, capability=capability,
                           valid_count=len(valid), total=len(rows),
                           scores_joined=scores_joined,
                           display_error=_display_error_type,
                           basis=score_basis)


@app.route("/evidence")
def evidence_browser():
    artifacts = list_failure_artifacts()
    return render_template("evidence.html", artifacts=artifacts,
                           artifacts_dir=str(FAILURE_ARTIFACTS_DIR))


@app.route("/evidence/<path:filename>")
def evidence_detail(filename):
    content = read_failure_artifact(filename)
    metadata = parse_artifact_name(filename)
    return render_template("evidence_detail.html", artifact=metadata,
                           content=content)


@app.route("/trends")
def trends():
    category = request.args.get("category", "coding")
    if category not in CATEGORIES:
        category = "coding"
    runs = get_runs(DB_PATH)  # newest first
    run_ids = sorted(r.id for r in runs)
    providers = sorted({r.provider for r in runs
                        for r in get_results_for_run(DB_PATH, r.id)
                        if r.category == category
                        and r.provider != "contamination_check"})
    series = {}
    for provider in providers:
        points = []
        for run_id in run_ids:
            rows = [r for r in get_results_for_run(DB_PATH, run_id)
                    if r.category == category and r.provider == provider]
            points.append(round(sum(r.score for r in rows) / len(rows), 3)
                          if rows else None)
        series[provider] = points
    return render_template("trends.html", category=category,
                           categories=CATEGORIES, run_ids=run_ids,
                           series=series, colors=PROVIDER_COLORS)


@app.route("/smoke", methods=["POST"])
def smoke():
    """Live connectivity check only — NOT a bench score. Calls the
    existing Groq provider with a one-word prompt and reports what
    came back, including failures, honestly."""
    try:
        # Output-time package, smoke split: 60-second per-call
        # deadline, 500-token cap, fast Groq model. Still a
        # connectivity check, not a bench score.
        result = groq_provider.run_prompt(
            "openai/gpt-oss-120b", "Reply with the single word OK.",
            max_tokens=500, timeout=60,
        )
        return render_template("smoke.html", result=result)
    except Exception as exc:  # show the failure, do not hide it
        return render_template("smoke.html", result=None, error=str(exc))


if __name__ == "__main__":
    # Debug mode off: a demo should not expose a debugger.
    app.run(host="127.0.0.1", port=5000, debug=False)
