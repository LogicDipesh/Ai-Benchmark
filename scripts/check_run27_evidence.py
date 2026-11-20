"""Check that Run #27 actually stored evidence (read-only).

Run from the project root after the bench run:
    python check_run27_evidence.py        # checks run 27
    python check_run27_evidence.py 28     # checks another run id

Reports, per category, how many rows carry evidence, and flags two
real bugs (not ordinary failures):
  * a VALID evaluation (measured score) with NO evidence — capture
    did not run for that row;
  * a gate-failed testing row whose mutants_killed is NOT NULL —
    kills were never measured, so any number there is fabrication.

Expected NULLs are NOT flagged: provider/request failures (HTTP,
connection, judge errors) and thinking-planning rows legitimately
carry no evidence, and are listed as expected.
"""
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


def main():
    run_id = int(sys.argv[1]) if len(sys.argv) > 1 else 27
    conn = sqlite3.connect("history.db")
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM results WHERE run_id = ? ORDER BY category, problem_id, provider",
        (run_id,),
    ).fetchall()
    conn.close()
    if not rows:
        print(f"Run {run_id}: no rows found.")
        return 2

    flags = []
    print(f"Run {run_id}: {len(rows)} rows")
    for category in ("coding", "debugging", "testing", "thinking-planning"):
        cat = [r for r in rows if r["category"] == category]
        if not cat:
            continue
        with_ev = [r for r in cat
                   if r["evidence_passed"] is not None
                   or r["evidence_gate_outcome"] is not None]
        print(f"{category}: {len(with_ev)}/{len(cat)} rows carry evidence")
        for r in cat:
            has_ev = (r["evidence_passed"] is not None
                      or r["evidence_gate_outcome"] is not None)
            if not has_ev:
                if category == "thinking-planning" or not is_valid(r["error_type"]):
                    print(f"  expected NULL: {r['problem_id']} / {r['provider']} "
                          f"({r['error_type']})")
                else:
                    flags.append(
                        f"VALID evaluation without evidence: {r['problem_id']} / "
                        f"{r['provider']} (score {r['score']}, {r['error_type']})")
            if category == "testing" and has_ev:
                gate = r["evidence_gate_outcome"]
                kills = r["evidence_mutants_killed"]
                print(f"  testing {r['problem_id']} / {r['provider']}: "
                      f"gate {gate}, kills {kills}/{r['evidence_mutants_total']}")
                if gate in ("failed", "not_run") and kills is not None:
                    flags.append(
                        f"Gate {gate} but kills={kills} (must be NULL): "
                        f"{r['problem_id']} / {r['provider']}")
    if flags:
        print("EVIDENCE CHECK: FLAGS FOUND")
        for f in flags:
            print("  FLAG: " + f)
        return 1
    print("EVIDENCE CHECK: PASS — no capture bugs found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
