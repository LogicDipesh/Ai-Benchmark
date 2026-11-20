from collections import defaultdict
from aibenchmark.history import get_results_for_run, get_runs

_VALID_EVALUATION_MARKERS = (
    "truncated_at_cap",
    "execution_error",
    "reference_impl_failed",
    "no_tests_ran",
    "sandbox_timeout",
)


def _is_valid_evaluation(error_type) -> bool:
    """True when a result row was scored from model output: no
    error, or an evaluation outcome (truncated output, execution
    failure, reference failure, no tests ran, sandbox timeout).
    Allowlist form is deliberate: providers record unknown
    failures as "error: <ClassName>" (e.g. "error: ReadTimeout"),
    so a blocklist of failure names can never be complete —
    unknown names must default to excluded, not to valid. Kept
    separate from _is_request_failure so the rule reads in the
    direction the capability mean uses it."""
    if not error_type or not isinstance(error_type, str):
        return True
    return any(m in error_type for m in _VALID_EVALUATION_MARKERS)


def _is_request_failure(error_type) -> bool:
    """Compat wrapper: a request failure is simply not a valid
    evaluation. Kept so earlier classifier checks keep passing."""
    return not _is_valid_evaluation(error_type)



_DISPLAY_LABELS = {
    "reference_impl_failed": "Reference validation failed",
    "execution_error": "Execution or collection error",
    "truncated_at_cap": "Output truncated at token limit",
    "sandbox_timeout": "Execution timed out",
    "no_tests_ran": "No tests ran",
}


def _display_error_type(error_type):
    """Readable label for a stored error_type (report display only).

    Stored values in history.db are untouched, and so are scores,
    picks, and the audit classifier — this only changes what the
    report prints. The truncation suffix ("; truncated_at_cap") is
    split off first so a combined value maps both parts; anything
    unmapped (HTTP errors, judge errors, timeouts, unknown names)
    passes through verbatim, so no diagnostic detail is ever hidden.
    Returns None for an empty/missing error (nothing failed)."""
    if not error_type or not isinstance(error_type, str):
        return None
    text = error_type.strip()
    if not text:
        return None
    suffix = "; truncated_at_cap"
    if text.endswith(suffix):
        base = text[: -len(suffix)].strip()
        label = _DISPLAY_LABELS["truncated_at_cap"]
        if not base:
            return label
        return f"{_DISPLAY_LABELS.get(base, base)}; {label}"
    if text == "truncated_at_cap":
        return _DISPLAY_LABELS["truncated_at_cap"]
    return _DISPLAY_LABELS.get(text, text)


def generate_report(run_id: int, db_path: str = "history.db") -> str:
    results = get_results_for_run(db_path, run_id)
    runs = get_runs(db_path)
    run = next((r for r in runs if r.id == run_id), None)
    lines = []
    lines.append(f"# AI Benchmark Report (Run #{run_id})")
    if run:
        lines.append(f"_Run at: {run.timestamp}_")
    if run and run.notes:
        lines.append(f"_Notes: {run.notes}_")
    lines.append("")
    lines.append("_Capability = mean score over valid evaluations only (valid = scored from model output; request failures — HTTP 429/5xx, connection errors, timeouts, judge errors — excluded); Reliability = valid evaluations / tasks attempted. The Score column still counts request failures as 0, and Current pick still uses it._")
    lines.append("_Current pick = highest blended Score (expected value per attempted task): the pick serves pipeline assignment, where a request failure is a failure to deliver, not just a missing datapoint. Latency = mean across attempted tasks in that category, each task's latency including retry waits; wall time is measured separately._")
    lines.append("_Failure detail shows readable labels for stored error types (reference_impl_failed reads as Reference validation failed); stored values in history.db, scores, picks, and the audit classifier are unchanged._")
    lines.append("")
    categories = ["coding", "debugging", "testing", "thinking-planning"]
    for category in categories:
        cat_results = [r for r in results if r.category == category and r.provider != "contamination_check"]
        if not cat_results:
            continue
        lines.append(f"## {category.title()}")
        lines.append("")
        scores = defaultdict(lambda: {"score": 0.0, "latency": 0, "count": 0, "status": "failed", "error_type": None})
        for r in cat_results:
            key = (r.provider, r.model)
            scores[key]["score"] += r.score
            scores[key]["latency"] += r.latency_ms
            scores[key]["count"] += 1
            scores[key]["status"] = r.status
            scores[key]["error_type"] = r.error_type
        # Capability/reliability split: a row counts as a *valid
        # evaluation* only when its score was measured from model
        # output — no error, or an evaluation outcome (truncated
        # output, execution error, reference failure, no tests
        # ran, sandbox timeout). Everything else is a request
        # failure excluded from the capability mean (HTTP errors,
        # connection errors, timeouts, judge errors, unknown
        # failure names): they still count as 0 in the blended
        # Score above, and they still lower Reliability. The
        # allowlist form matters because providers record unknown
        # failures as "error: <ClassName>" — a blocklist can never
        # be complete, so unknown names default to excluded.
        cap = defaultdict(lambda: {"valid_score": 0.0, "valid": 0, "total": 0})
        for r in cat_results:
            key = (r.provider, r.model)
            cap[key]["total"] += 1
            if _is_valid_evaluation(r.error_type):
                cap[key]["valid_score"] += r.score
                cap[key]["valid"] += 1
        rows = []
        for (provider, model), data in scores.items():
            avg_score = data["score"] / data["count"] if data["count"] > 0 else 0.0
            avg_latency = int(data["latency"] / data["count"]) if data["count"] > 0 else 0
            rows.append((avg_score, avg_latency, model, provider, data["status"], data["error_type"]))
        # Fairness fix (latency package): ties used to break by
        # provider insertion order, which is arbitrary. Break them by
        # lowest mean latency instead, so the "current pick" is the
        # fastest model among equals — the only defensible tie-break
        # for a pipeline assignment. Scores are untouched.
        rows.sort(key=lambda x: (-x[0], x[1]))
        lines.append("| Model | Provider | Score | Latency (ms) | Status |")
        lines.append("|-------|----------|-------|--------------|--------|")
        for score, latency, model, provider, status, error_type in rows:
            lines.append(f"| {model} | {provider} | {score:.2f} | {latency} | {status} |")
        lines.append("")
        if category == "thinking-planning":
            lines.append("_subjective — LLM-judged_")
            lines.append("")
        if rows:
            max_score = rows[0][0]
            if max_score > 0.0:
                pick = rows[0]
                lines.append(f"**Current pick: {pick[2]} ({pick[3]})**")
            else:
                lines.append("**No successful runs — no pick**")
            lines.append("")
        # Display mapping (report-side only): one readable line per
        # model whose last evaluation in this category carries a
        # stored error_type. Table rows, scores, picks, and the audit
        # classifier are untouched — the audit parser ignores these
        # lines because they are not table rows, and the stored value
        # is shown alongside whenever it differs from the label.
        detail_lines = []
        for _score, _lat, _model, _provider, _status, _err in rows:
            if _err:
                _label = _display_error_type(_err)
                if _label is None:
                    continue
                if _label != _err:
                    detail_lines.append(
                        f"- {_provider} ({_model}): {_label} (stored: {_err})"
                    )
                else:
                    detail_lines.append(f"- {_provider} ({_model}): {_label}")
        if detail_lines:
            lines.append("**Failure detail (last evaluation per model)**")
            lines.append("")
            lines.extend(detail_lines)
            lines.append("")
        if rows:
            lines.append("**Capability & reliability (valid evaluations only)**")
            lines.append("")
            lines.append("| Model | Provider | Capability | Reliability | Valid |")
            lines.append("|-------|----------|------------|-------------|-------|")
            for _score, _lat, _model, _provider, _status, _err in rows:
                _c = cap[(_provider, _model)]
                _cap = f"{_c['valid_score'] / _c['valid']:.2f}" if _c["valid"] > 0 else "—"
                _rel = int(round(100 * _c["valid"] / _c["total"])) if _c["total"] > 0 else 0
                lines.append(f"| {_model} | {_provider} | {_cap} | {_rel}% | {_c['valid']}/{_c['total']} |")
            lines.append("")
        lines.append("---")
        lines.append("")
    contamination_results = [r for r in results if r.provider == "contamination_check" and r.category == "contamination"]
    for cr in contamination_results:
        if cr.error_type:
            lines.append("### Contamination Warning")
            lines.append("")
            lines.append("```")
            lines.append(cr.error_type)
            lines.append("```")
            lines.append("")
    return "\n".join(lines)


def generate_trend_report(
    db_path: str,
    category: str,
    model: str,
    provider: str,
) -> str:
    from aibenchmark.history import get_trend_data
    results = get_trend_data(db_path, category, model, provider)
    lines = []
    lines.append(f"# Trend: {model} ({provider}) — {category.title()}")
    lines.append("")
    if not results:
        lines.append("No data found.")
        return "\n".join(lines)
    lines.append("| Run ID | Problem | Score | Latency (ms) | Status |")
    lines.append("|--------|---------|-------|--------------|--------|")
    for r in results:
        lines.append(f"| {r.run_id} | {r.problem_id} | {r.score:.2f} | {r.latency_ms} | {r.status} |")
    lines.append("")
    scores = [r.score for r in results]
    if scores:
        avg = sum(scores) / len(scores)
        lines.append(f"**Average score: {avg:.2f}**")
    return "\n".join(lines)