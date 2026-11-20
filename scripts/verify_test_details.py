"""Verify per-test step-3 persistence (test_details column).

Run from the project root (offline, no API calls):
    python verify_test_details.py

Uses ONLY temporary fixture databases (never the real history.db).
Checks:
 1. Fresh init_db creates the test_details column.
 2. A legacy pre-evidence database reads safely and migrates to all
    15 evidence columns with rows intact and NULL (not recorded).
 3. migrate_test_details.py backs up first, adds exactly the column,
    and is idempotent (second run changes nothing, writes no second
    backup).
 4. Round-trips through insert_result + get_results_for_run:
    list exact, [] stays [] (never collapsed to None), None stays
    None, a missing "tests" key stays None, gate lists round-trip
    with gate fields intact, evidence=None stays None.
 5. The CLI report renders on a migrated-schema fixture run.
 6. audit_report.py PASSES on a migrated-schema fixture run
    (aggregation unchanged by the extra column).
 7. Scores are identical before/after migration.

Exit code 0 only when every check passes.
"""
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from aibenchmark import history as H

FAILURES = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name +
          ("" if cond else f" — {detail}"))
    if not cond:
        FAILURES.append(name)


def _cols(db_path):
    conn = sqlite3.connect(db_path)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(results)")}
    conn.close()
    return cols


def _by_problem(db_path, run_id):
    return {r.problem_id: r for r in H.get_results_for_run(db_path, run_id)}


def main():
    tmp = Path(tempfile.mkdtemp(prefix="verify_test_details_"))

    # 1. Fresh init_db creates test_details.
    fresh = str(tmp / "fresh.db")
    H.init_db(fresh)
    check("fresh init creates test_details", "test_details" in _cols(fresh))

    # 2. Legacy pre-evidence database reads safely, then migrates.
    legacy = str(tmp / "legacy.db")
    conn = sqlite3.connect(legacy)
    conn.executescript("""
        CREATE TABLE runs (id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL, notes TEXT);
        CREATE TABLE results (id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL, provider TEXT NOT NULL,
            model TEXT NOT NULL, category TEXT NOT NULL,
            problem_id TEXT NOT NULL, score REAL NOT NULL,
            latency_ms INTEGER NOT NULL, status TEXT NOT NULL,
            error_type TEXT);
    """)
    conn.execute("INSERT INTO runs (timestamp, notes) VALUES ('t', 'legacy')")
    conn.execute("INSERT INTO results (run_id, provider, model, category,"
                 " problem_id, score, latency_ms, status, error_type)"
                 " VALUES (1, 'groq', 'm', 'coding', 'coding_001', 1.0, 100,"
                 " 'passed', NULL)")
    conn.commit()
    conn.close()
    rows = H.get_results_for_run(legacy, 1)
    check("legacy DB reads without evidence columns",
          len(rows) == 1 and rows[0].evidence is None)
    H.init_db(legacy)
    cols = _cols(legacy)
    check("legacy DB migrates to all 15 evidence columns",
          len([c for c in cols if c.startswith("evidence_")]) == 14
          and "test_details" in cols, f"cols={sorted(cols)}")
    rows = H.get_results_for_run(legacy, 1)
    check("legacy rows stay NULL after migration",
          rows[0].evidence is None and rows[0].score == 1.0)

    # 3. migrate_test_details.py: backup, column, idempotent.
    s3 = str(tmp / "s3.db")
    conn = sqlite3.connect(s3)
    conn.executescript("""
        CREATE TABLE runs (id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL, notes TEXT);
        CREATE TABLE results (id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL, provider TEXT NOT NULL,
            model TEXT NOT NULL, category TEXT NOT NULL,
            problem_id TEXT NOT NULL, score REAL NOT NULL,
            latency_ms INTEGER NOT NULL, status TEXT NOT NULL,
            error_type TEXT,
            evidence_passed INTEGER, evidence_failed INTEGER,
            evidence_skipped INTEGER, evidence_errors INTEGER,
            evidence_collected INTEGER, evidence_gate_outcome TEXT,
            evidence_gate_passed INTEGER, evidence_gate_failed INTEGER,
            evidence_gate_skipped INTEGER, evidence_gate_errors INTEGER,
            evidence_gate_collected INTEGER,
            evidence_mutants_killed INTEGER,
            evidence_mutants_total INTEGER,
            evidence_mutants_json TEXT);
    """)
    conn.execute("INSERT INTO runs (timestamp, notes) VALUES ('t', 's3')")
    conn.execute("INSERT INTO results (run_id, provider, model, category,"
                 " problem_id, score, latency_ms, status, error_type,"
                 " evidence_passed, evidence_failed, evidence_skipped,"
                 " evidence_errors, evidence_collected)"
                 " VALUES (1, 'groq', 'm', 'coding', 'coding_001', 0.5, 200,"
                 " 'partial', NULL, 1, 1, 0, 0, 2)")
    conn.commit()
    conn.close()
    before = {r.problem_id: r.score for r in H.get_results_for_run(s3, 1)}
    proc = subprocess.run([sys.executable, str(HERE / "migrate_test_details.py"), s3],
                          capture_output=True, text=True)
    backups = sorted(tmp.glob("s3.db.testdetails-backup-*"))
    check("migrate writes a backup first",
          proc.returncode == 0 and len(backups) == 1, proc.stdout + proc.stderr)
    check("migrate adds exactly test_details",
          "test_details" in _cols(s3) and
          len([c for c in _cols(s3) if c.startswith("evidence_")]) == 14)
    after = {r.problem_id: r.score for r in H.get_results_for_run(s3, 1)}
    check("scores identical before/after migration", before == after)
    proc2 = subprocess.run([sys.executable, str(HERE / "migrate_test_details.py"), s3],
                           capture_output=True, text=True)
    check("migrate is idempotent (no second backup)",
          proc2.returncode == 0 and len(list(tmp.glob("s3.db.testdetails-backup-*"))) == 1
          and "already present" in proc2.stdout)

    # 4. Round-trips.
    rt = str(tmp / "roundtrip.db")
    H.init_db(rt)
    run_id = H.create_run(rt, "verify")
    direct_list = [{"name": "t.py::test_a", "status": "passed"},
                   {"name": "t.py::test_b", "status": "failed"},
                   {"name": "t.py::test_c", "status": "passed"}]
    H.insert_result(rt, run_id, "groq", "m", "coding", "coding_001",
                    0.6667, 100, "partial", None,
                    {"passed": 2, "failed": 1, "skipped": 0, "errors": 0,
                     "collected": 3, "tests": direct_list})
    H.insert_result(rt, run_id, "groq", "m", "coding", "coding_002",
                    0.0, 100, "error", "execution_error",
                    {"passed": 0, "failed": 0, "skipped": 0, "errors": 0,
                     "collected": 0, "tests": []})
    H.insert_result(rt, run_id, "groq", "m", "debugging", "debug_001",
                    0.0, 100, "failed", "error: ReadTimeout",
                    {"passed": None, "failed": None, "skipped": None,
                     "errors": None, "collected": None, "tests": None})
    H.insert_result(rt, run_id, "groq", "m", "debugging", "debug_002",
                    1.0, 100, "passed", None,
                    {"passed": 1, "failed": 0, "skipped": 0, "errors": 0,
                     "collected": 1})  # old shape: no "tests" key
    gate_list = [{"name": "g.py::test_even", "status": "passed"},
                 {"name": "g.py::test_wrong", "status": "failed"}]
    H.insert_result(rt, run_id, "groq", "m", "testing", "testing_001",
                    0.0, 100, "failed", "reference_impl_failed",
                    {"gate_outcome": "failed",
                     "gate": {"passed": 1, "failed": 1, "skipped": 0,
                              "errors": 0, "collected": 2},
                     "mutants_killed": None, "mutants_total": 2,
                     "mutants": {"m1": "not_run", "m2": "not_run"},
                     "tests": gate_list})
    H.insert_result(rt, run_id, "groq", "m", "testing", "testing_002",
                    0.0, 100, "error", "no_tests_ran",
                    {"gate_outcome": "not_run",
                     "gate": {"passed": 0, "failed": 0, "skipped": 0,
                              "errors": 0, "collected": 0},
                     "mutants_killed": None, "mutants_total": 2,
                     "mutants": {"m1": "not_run", "m2": "not_run"},
                     "tests": []})
    H.insert_result(rt, run_id, "groq", "m", "thinking-planning", "plan_001",
                    1.0, 100, "passed", None, None)
    got = _by_problem(rt, run_id)
    check("direct list round-trips exactly",
          got["coding_001"].evidence["tests"] == direct_list)
    check("direct [] stays [] (not None)",
          got["coding_002"].evidence["tests"] == [])
    # All-None counts read back as evidence None wholesale (established
    # step-3 semantics: unmeasured rows have no evidence dict at all).
    # The tests=None information is encoded in that None, not lost.
    check("direct all-None counts read back as evidence None",
          got["debug_001"].evidence is None)
    check("missing tests key stays None",
          got["debug_002"].evidence["tests"] is None)
    check("gate list round-trips with gate fields intact",
          got["testing_001"].evidence["tests"] == gate_list
          and got["testing_001"].evidence["gate_outcome"] == "failed"
          and got["testing_001"].evidence["mutants_killed"] is None)
    check("gate [] stays []",
          got["testing_002"].evidence["tests"] == [])
    check("evidence=None stays None",
          got["plan_001"].evidence is None)

    # 5. CLI report renders on the migrated fixture run.
    from aibenchmark.report import generate_report
    text = generate_report(run_id, rt)
    check("report renders on migrated schema",
          "Current pick" in text and "Coding" in text and "Testing" in text)

    # 6. Audit passes on the migrated fixture run.
    audit = HERE / "audit_report.py"
    if not (HERE / "scripts" / "audit_report.py").exists() and not audit.exists():
        check("audit_report.py present in root or scripts/", False,
              "copy audit_report.py to the project root or scripts/")
    else:
        audit = audit if audit.exists() else HERE / "scripts" / "audit_report.py"
        proc = subprocess.run(
            [sys.executable, str(audit), str(run_id), rt],
            capture_output=True, text=True, cwd=str(HERE))
        check("audit_report.py PASSES on migrated schema",
              proc.returncode == 0 and "audit: PASS" in proc.stdout,
              proc.stdout[-500:] + proc.stderr[-500:])

    if FAILURES:
        print(f"\nverify_test_details: FAILED — {', '.join(FAILURES)}")
    else:
        print("\nverify_test_details: ALL CHECKS PASS")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
