"""audit_report.py — independently verify a generated bench report against
the real benchmark database. READ-ONLY: reads history.db, writes nothing,
makes no network calls, uses no keys.

Usage (from the project root):
    python audit_report.py            # latest run
    python audit_report.py 23         # a specific run
    python audit_report.py 23 history.db

What it checks, per provider per category, recomputed from the raw rows
with its own aggregation code (it does NOT reuse report.py's internals —
it only calls generate_report() to get the TEXT to compare against):
  * blended Score, Capability, Reliability, Valid counts, mean Latency
  * Current pick under the documented policy (highest blended Score,
    ties by lowest mean latency; no pick when the best score is 0)
  * the invariant S = C x R in FULL precision (tolerance 1e-9) — never
    by multiplying displayed 2-decimal values (that falsely fails:
    GLM testing 0.67 x 50% = 0.335 -> 0.34, while the true
    0.6666... x 0.5 = 0.3333... -> 0.33)
  * coverage: the report's model/category set matches the database's
  * duplicates: the same (problem, provider) recorded twice in a run
  * failed rows carrying nonzero scores (breaks the invariant's premise)

Classification rule used here (mirrors the documented rule in
report.py; the rule itself is a reviewed design decision, not
something this script can independently prove — it validates
aggregation, rendering, picks, coverage and the invariant GIVEN the
rule):
  A row is a VALID evaluation when its score was measured from model
  output: error_type is empty, or contains one of truncated_at_cap,
  execution_error, reference_impl_failed, no_tests_ran, sandbox_timeout.
  Everything else (HTTP errors, connection errors, timeouts, judge
  errors, missing keys, retry-exhausted, unknown failure names) is a
  request failure and is excluded from capability. This allowlist form
  matters: providers record unknown failures as "error: <ClassName>"
  (e.g. "error: ReadTimeout"), so a blocklist can never be complete.

NOT checked: the Status column (last-row-wins by construction in
report.py, arbitrary, not semantically meaningful), and contamination
rows (excluded from categories by design).

Exit code: 0 = all checks pass, 1 = any check fails, 2 = usage/DB error.
"""

import sys
from collections import Counter, defaultdict

CATEGORIES = ["coding", "debugging", "testing", "thinking-planning"]
TITLE_TO_CATEGORY = {
    "Coding": "coding",
    "Debugging": "debugging",
    "Testing": "testing",
    "Thinking-Planning": "thinking-planning",
}

# Allowlist of evaluation outcomes (see header). Anything else is a
# request failure. Mirrors report.py's documented rule; kept as a
# separate copy here so the audit does not import report internals.
_VALID_MARKERS = (
    "truncated_at_cap",
    "execution_error",
    "reference_impl_failed",
    "no_tests_ran",
    "sandbox_timeout",
)


def is_valid_evaluation(error_type) -> bool:
    if not error_type or not isinstance(error_type, str):
        return True
    return any(m in error_type for m in _VALID_MARKERS)


def fmt_score(x: float) -> str:
    return f"{x:.2f}"


def fmt_reliability(valid: int, total: int) -> str:
    return f"{int(round(100 * valid / total))}%" if total > 0 else "0%"


def recompute(rows):
    """Independent aggregation: {(provider, model): stats}, first-seen order."""
    groups = {}
    order = []
    for r in rows:
        key = (r.provider, r.model)
        if key not in groups:
            groups[key] = {"scores": [], "valid_scores": [], "latencies": []}
            order.append(key)
        groups[key]["scores"].append(r.score)
        groups[key]["latencies"].append(r.latency_ms)
        if is_valid_evaluation(r.error_type):
            groups[key]["valid_scores"].append(r.score)
    stats = {}
    for key in order:
        g = groups[key]
        total = len(g["scores"])
        valid = len(g["valid_scores"])
        blended = sum(g["scores"]) / total if total else 0.0
        capability = sum(g["valid_scores"]) / valid if valid else None
        stats[key] = {
            "total": total,
            "valid": valid,
            "blended": blended,
            "capability": capability,
            "reliability": valid / total if total else 0.0,
            "latency": int(sum(g["latencies"]) / total) if total else 0,
        }
    return stats


def pick_line(stats):
    """Current pick under the documented policy, same tie-break as report."""
    if not stats:
        return None
    ordered = sorted(stats.items(), key=lambda kv: (-kv[1]["blended"], kv[1]["latency"]))
    (provider, model), top = ordered[0]
    if top["blended"] > 0.0:
        return f"**Current pick: {model} ({provider})**"
    return "**No successful runs — no pick**"


def parse_report(text):
    """Parse generate_report() text into {category: {main, cap, pick}}."""
    sections = {}
    current = None
    current_table = None  # "main" | "cap" | None
    for line in text.splitlines():
        if line.startswith("## "):
            title = line[3:].strip()
            current = TITLE_TO_CATEGORY.get(title)
            current_table = None
            if current is not None:
                sections[current] = {"main": {}, "cap": {}, "pick": None}
            continue
        if current is None:
            continue
        sec = sections[current]
        if line.startswith("| Model | Provider | Score |"):
            current_table = "main"
            continue
        if line.startswith("| Model | Provider | Capability |"):
            current_table = "cap"
            continue
        if line.startswith("**Current pick:") or line.startswith("**No successful runs"):
            sec["pick"] = line.strip()
            current_table = None
            continue
        if line.startswith("|") and current_table and not line.startswith("|---"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if current_table == "main" and len(cells) == 5:
                model, provider, score, latency, _status = cells
                sec["main"][(provider, model)] = {"score": score, "latency": latency}
            elif current_table == "cap" and len(cells) == 5:
                model, provider, cap, rel, valid = cells
                sec["cap"][(provider, model)] = {
                    "capability": cap,
                    "reliability": rel,
                    "valid": valid,
                }
            continue
        if line.strip() == "" or line.startswith("---"):
            # Blank line or divider ends a table body (headers re-arm it).
            current_table = None
    return sections


def main(argv):
    from aibenchmark.history import get_latest_run_id, get_results_for_run, get_runs
    from aibenchmark.report import generate_report

    db_path = "history.db"
    run_id = None
    args = list(argv)
    if args:
        if args[0] != "latest":
            try:
                run_id = int(args[0])
            except ValueError:
                print(f"audit: run id must be an integer or 'latest', got {args[0]!r}")
                return 2
        args = args[1:]
    if args:
        db_path = args[0]

    runs = get_runs(db_path)
    if run_id is None:
        try:
            run_id = get_latest_run_id()
        except Exception:
            run_id = runs[-1].id if runs else None
    run = next((r for r in runs if r.id == run_id), None)
    if run is None:
        print(f"audit: run {run_id} not found in {db_path}")
        return 2
    rows = get_results_for_run(db_path, run_id)
    if not rows:
        print(f"audit: FAIL — run {run_id} has no result rows in {db_path}")
        return 1

    print(f"audit: run {run_id} from {db_path} ({len(rows)} rows)")
    print(
        "audit: classification rule — valid = scored from model output "
        "(empty error, or truncated_at_cap / execution_error / "
        "reference_impl_failed / no_tests_ran / sandbox_timeout); "
        "everything else is a request failure excluded from capability"
    )
    failures = []

    # Data sanity checks (independent of the report text).
    dupes = [k for k, n in Counter((r.category, r.problem_id, r.provider) for r in rows).items() if n > 1]
    for category, problem, provider in sorted(dupes):
        failures.append(f"{category} | {provider} | duplicate row for problem {problem}")
    for r in rows:
        if r.provider == "contamination_check":
            continue
        if not is_valid_evaluation(r.error_type) and r.score != 0:
            failures.append(
                f"{r.category} | {r.provider}/{r.model} | request-failure row for "
                f"{r.problem_id} carries nonzero score {r.score}"
            )

    text = generate_report(run_id, db_path)
    if f"# AI Benchmark Report (Run #{run_id})" not in text:
        failures.append(f"header | report header does not name run {run_id}")
    sections = parse_report(text)

    for category in CATEGORIES:
        cat_rows = [r for r in rows if r.category == category and r.provider != "contamination_check"]
        stats = recompute(cat_rows)
        sec = sections.get(category)
        if not cat_rows:
            if sec is not None:
                failures.append(f"{category} | unexpected report section with no database rows")
            continue
        if sec is None:
            failures.append(f"{category} | missing report section ({len(cat_rows)} database rows)")
            continue
        if set(sec["main"]) != set(stats):
            failures.append(
                f"{category} | main-table coverage mismatch: report {sorted(sec['main'])} "
                f"vs database {sorted(stats)}"
            )
        if set(sec["cap"]) != set(stats):
            failures.append(
                f"{category} | capability-table coverage mismatch: report {sorted(sec['cap'])} "
                f"vs database {sorted(stats)}"
            )
        for key, st in stats.items():
            provider, model = key
            m = sec["main"].get(key)
            c = sec["cap"].get(key)
            if m is not None:
                if m["score"] != fmt_score(st["blended"]):
                    failures.append(
                        f"{category} | {provider}/{model} | blended Score: "
                        f"report {m['score']}, recomputed {fmt_score(st['blended'])}"
                    )
                if m["latency"] != str(st["latency"]):
                    failures.append(
                        f"{category} | {provider}/{model} | Latency: "
                        f"report {m['latency']}, recomputed {st['latency']}"
                    )
            if c is not None:
                want_cap = fmt_score(st["capability"]) if st["capability"] is not None else "—"
                if c["capability"] != want_cap:
                    failures.append(
                        f"{category} | {provider}/{model} | Capability: "
                        f"report {c['capability']}, recomputed {want_cap}"
                    )
                if c["reliability"] != fmt_reliability(st["valid"], st["total"]):
                    failures.append(
                        f"{category} | {provider}/{model} | Reliability: "
                        f"report {c['reliability']}, recomputed "
                        f"{fmt_reliability(st['valid'], st['total'])}"
                    )
                if c["valid"] != f"{st['valid']}/{st['total']}":
                    failures.append(
                        f"{category} | {provider}/{model} | Valid: "
                        f"report {c['valid']}, recomputed {st['valid']}/{st['total']}"
                    )
            # Invariant S = C x R in full precision.
            if st["valid"] > 0:
                if abs(st["blended"] - st["capability"] * st["reliability"]) > 1e-9:
                    failures.append(
                        f"{category} | {provider}/{model} | invariant S != C x R: "
                        f"S={st['blended']}, C={st['capability']}, R={st['reliability']}"
                    )
            else:
                if st["blended"] != 0.0:
                    failures.append(
                        f"{category} | {provider}/{model} | no valid evaluations but "
                        f"blended Score is {st['blended']} (expected 0.0)"
                    )
        want_pick = pick_line(stats)
        if sec["pick"] != want_pick:
            failures.append(
                f"{category} | Current pick: report {sec['pick']!r}, "
                f"recomputed {want_pick!r}"
            )

    if failures:
        print(f"audit: FAIL — {len(failures)} check(s) failed for run {run_id}:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"audit: PASS — all checks passed for run {run_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
