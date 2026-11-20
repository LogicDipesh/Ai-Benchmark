"""Check that Run #28 actually stored per-test identities (read-only).

Run from the project root after the bench run:
    python check_run28_pertest.py        # checks run 28
    python check_run28_pertest.py 29     # checks another run id

Reports, per category, how many rows carry test identities, and
flags real capture bugs (not ordinary model failures):
  * measured counts but NO test identities — the parser ran but
    the identities were dropped;
  * counts None but identities present, or vice versa in a way
    that breaks the tests-None-iff-counts-None invariant;
  * a test list whose tallies (excluding xfail/xpass) do not
    reconcile with the stored counts;
  * a gate-failed / gate-not-run testing row whose mutants_killed
    is NOT NULL — kills were never measured;
  * a thinking-planning row carrying test identities — plans
    never run pytest.

Expected NULLs are NOT flagged: provider/request failures,
sandbox timeouts, missing test files (counts None, identities
None), and thinking-planning rows legitimately carry no
identities, and are listed as expected.
"""
import json
import sqlite3
import sys

VALID_MARKERS = (
    "truncated_at_cap",
    "execution_error",
    "reference_impl_failed",
    "no_tests_ran",
    "sandbox_timeout",
)


def is_valid(error_type):
    if not error_type:
        return True
    return any(m in error_type for m in VALID_MARKERS)


def display_name(node_id):
    if not isinstance(node_id, str):
        return ""
    return node_id.split("::", 1)[-1] if "::" in node_id else node_id


def main():
    run_id = int(sys.argv[1]) if len(sys.argv) > 1 else 28
    conn = sqlite3.connect("history.db")
    conn.row_factory = sqlite3.Row
    columns = [r[1] for r in conn.execute("PRAGMA table_info(results)")]
    if "test_details" not in columns:
        print("test_details column missing: per-test step 3 is not "
              "installed on this database. Migrate first, then rerun.")
        return 2
    rows = conn.execute(
        "SELECT * FROM results WHERE run_id = ? ORDER BY category, problem_id, provider",
        (run_id,),
    ).fetchall()
    conn.close()
    if not rows:
        print(f"Run {run_id}: no rows found.")
        return 2

    flags = []
    sample = None
    print(f"Run {run_id}: {len(rows)} rows")
    for category in ("coding", "debugging", "testing", "thinking-planning"):
        cat = [r for r in rows if r["category"] == category]
        if not cat:
            continue
        with_tests = [r for r in cat if r["test_details"] is not None]
        print(f"{category}: {len(with_tests)}/{len(cat)} rows carry test identities")
        for r in cat:
            raw = r["test_details"]
            problem, provider = r["problem_id"], r["provider"]
            if category == "thinking-planning":
                if raw is not None:
                    flags.append(
                        f"Plan row carries test identities (must be NULL): "
                        f"{problem} / {provider}")
                else:
                    print(f"  expected NULL: {problem} / {provider} (plan row)")
                continue
            if category == "testing":
                gate = r["evidence_gate_outcome"]
                counts = (r["evidence_gate_passed"], r["evidence_gate_failed"],
                          r["evidence_gate_errors"], r["evidence_gate_skipped"])
                counts_measured = gate is not None and counts[0] is not None
            else:
                gate = None
                counts = (r["evidence_passed"], r["evidence_failed"],
                          r["evidence_errors"], r["evidence_skipped"])
                counts_measured = counts[0] is not None
            if raw is None:
                if counts_measured and category != "testing":
                    flags.append(
                        f"Measured counts but NO test identities: "
                        f"{problem} / {provider}")
                elif counts_measured and category == "testing" and gate in ("passed", "failed"):
                    flags.append(
                        f"Gate {gate} but NO test identities: "
                        f"{problem} / {provider}")
                elif counts_measured and category == "testing" and gate == "not_run":
                    print(f"  expected NULL: {problem} / {provider} (gate not run)")
                else:
                    print(f"  expected NULL: {problem} / {provider} "
                          f"({r['error_type']})")
                if category == "testing" and gate in ("failed", "not_run") \
                        and r["evidence_mutants_killed"] is not None:
                    flags.append(
                        f"Gate {gate} but kills={r['evidence_mutants_killed']} "
                        f"(must be NULL): {problem} / {provider}")
                continue
            # Identities present: must be a JSON list of {name, status}.
            try:
                tests = json.loads(raw)
            except (ValueError, TypeError):
                flags.append(f"test_details is not valid JSON: {problem} / {provider}")
                continue
            if not isinstance(tests, list) or any(
                    not isinstance(t, dict) or "name" not in t or "status" not in t
                    for t in tests):
                flags.append(
                    f"test_details malformed (not a list of name/status): "
                    f"{problem} / {provider}")
                continue
            if not counts_measured:
                flags.append(
                    f"Identities present but counts unmeasured (invariant "
                    f"broken): {problem} / {provider}")
            else:
                tallies = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0}
                for t in tests:
                    status = t["status"]
                    if status in tallies:
                        tallies[status] += 1
                # xfail/xpass are listed but never counted.
                expected = dict(zip(
                    ("passed", "failed", "errors", "skipped"), counts))
                if tallies != expected:
                    flags.append(
                        f"Test list does not reconcile with counts: "
                        f"{problem} / {provider} (list {tallies}, "
                        f"counts {expected})")
            if category == "testing" and gate in ("failed", "not_run") \
                    and r["evidence_mutants_killed"] is not None:
                flags.append(
                    f"Gate {gate} but kills={r['evidence_mutants_killed']} "
                    f"(must be NULL): {problem} / {provider}")
            if sample is None and tests:
                sample = (problem, provider, len(tests),
                          [display_name(t["name"]) for t in tests[:3]])
    if sample:
        print(f"Sample recorded row: {sample[0]} / {sample[1]}: "
              f"{sample[2]} tests, first: {', '.join(sample[3])}")
    if flags:
        print("PER-TEST CHECK: FLAGS FOUND")
        for f in flags:
            print("  FLAG: " + f)
        return 1
    print("PER-TEST CHECK: PASS — no capture bugs found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
