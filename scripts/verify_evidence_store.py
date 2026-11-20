"""Verify step-3 database persistence (run from the project root).

Fixture-based and safe: builds temporary databases, never touches
the real history.db, makes no provider calls, needs no keys.

Checks:
  1. Pre-migration reads: a pre-step-3 database (old schema, no
     evidence columns) reads fine through the new history module,
     with evidence None for every row (not recorded, never zero).
  2. Migration: ensure_evidence_columns adds exactly the 14
     evidence columns, is idempotent, and leaves legacy rows'
     evidence NULL with scores untouched.
  3. Round-trip: direct, testing (gate passed and gate failed),
     and evidence=None inserts read back exactly through
     get_results_for_run, including the mutants map (JSON).
  4. Backward-compatible calls: insert_result without evidence
     (the contamination path) still works and yields NULL evidence.
  5. Fresh databases: init_db creates the evidence columns.
  6. Report tolerance: the real generate_report renders a fixture
     run on the migrated schema, and the real audit_report.py
     PASSES on it (evidence columns change nothing the report
     or audit compute).
"""
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from aibenchmark.history import (
    EVIDENCE_COLUMNS,
    create_run,
    ensure_evidence_columns,
    get_results_for_run,
    init_db,
    insert_result,
)

OLD_RESULTS = """
CREATE TABLE results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    category TEXT NOT NULL,
    problem_id TEXT NOT NULL,
    score REAL NOT NULL,
    latency_ms INTEGER NOT NULL,
    status TEXT NOT NULL,
    error_type TEXT,
    FOREIGN KEY (run_id) REFERENCES runs(id)
);
"""
OLD_RUNS = """
CREATE TABLE runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    notes TEXT
);
"""

DIRECT = {"passed": 3, "failed": 0, "skipped": 0, "errors": 0, "collected": 3}
GATE_OK = {"passed": 3, "failed": 0, "skipped": 0, "errors": 0, "collected": 3}
GATE_FAIL = {"passed": 3, "failed": 1, "skipped": 0, "errors": 0, "collected": 4}
TESTING_OK = {
    "gate_outcome": "passed", "gate": GATE_OK,
    "mutants_killed": 2, "mutants_total": 2,
    "mutants": {"mutant_001": "killed", "mutant_002": "killed"},
}
TESTING_FAIL = {
    "gate_outcome": "failed", "gate": GATE_FAIL,
    "mutants_killed": None, "mutants_total": 2,
    "mutants": {"mutant_001": "not_run", "mutant_002": "not_run"},
}


def _check(name, actual, expected):
    assert actual == expected, f"{name}: expected {expected!r}, got {actual!r}"
    print(f"ok: {name}")


def _fixture_run(db_path, run_id, providers):
    """One small but complete run: all 4 categories, 2 providers,
    2 problems each, so generate_report + audit have real sections."""
    for provider in providers:
        for category, problems in (
            ("coding", ["coding_001", "coding_002"]),
            ("debugging", ["debug_001", "debug_002"]),
            ("testing", ["testing_001", "testing_002"]),
            ("thinking-planning", ["plan_001", "plan_002"]),
        ):
            for i, problem in enumerate(problems):
                if category == "testing":
                    ev = TESTING_OK if i == 0 else TESTING_FAIL
                    score = 1.0 if i == 0 else 0.0
                    err = None if i == 0 else "reference_impl_failed"
                elif category == "thinking-planning":
                    ev, score, err = None, 1.0 if i == 0 else 0.5, None
                else:
                    ev, score, err = DIRECT, 1.0 if i == 0 else 0.5, None
                insert_result(
                    str(db_path), run_id, provider, "model-" + provider,
                    category, problem, score, 1000 + i,
                    "passed" if score > 0 else "failed", err, ev,
                )


def main():
    tmp = Path(tempfile.mkdtemp())

    # 1-2. Legacy database: old schema, raw inserts, pre-migration read.
    legacy = tmp / "legacy.db"
    conn = sqlite3.connect(str(legacy))
    conn.executescript(OLD_RUNS + OLD_RESULTS)
    conn.execute("INSERT INTO runs (timestamp, notes) VALUES ('t', 'legacy')")
    for category, score in (("coding", 1.0), ("testing", 0.5),
                            ("thinking-planning", 1.0)):
        conn.execute(
            "INSERT INTO results (run_id, provider, model, category,"
            " problem_id, score, latency_ms, status, error_type)"
            " VALUES (1, 'groq', 'm', ?, ?, ?, 100, 'passed', NULL)",
            (category, category + "_001", score),
        )
    conn.commit()
    conn.close()
    rows = get_results_for_run(str(legacy), 1)
    _check("pre-migration read: evidence None, scores intact",
           [(r.score, r.evidence) for r in rows],
           [(1.0, None), (0.5, None), (1.0, None)])

    conn = sqlite3.connect(str(legacy))
    added = ensure_evidence_columns(conn)
    conn.commit()
    _check("migration adds all 14 columns", len(added), len(EVIDENCE_COLUMNS))
    added_again = ensure_evidence_columns(conn)
    conn.close()
    _check("migration idempotent", added_again, [])
    rows = get_results_for_run(str(legacy), 1)
    _check("legacy rows stay NULL after migration",
           [(r.score, r.evidence) for r in rows],
           [(1.0, None), (0.5, None), (1.0, None)])

    # 3-4. Round-trip on a fresh database.
    db = tmp / "fresh.db"
    run_id = create_run(str(db), "verify")
    insert_result(str(db), run_id, "groq", "m", "coding",
                  "coding_001", 1.0, 100, "passed", None, DIRECT)
    insert_result(str(db), run_id, "groq", "m", "testing",
                  "testing_001", 1.0, 100, "passed", None, TESTING_OK)
    insert_result(str(db), run_id, "groq", "m", "testing",
                  "testing_002", 0.0, 100, "failed",
                  "reference_impl_failed", TESTING_FAIL)
    insert_result(str(db), run_id, "groq", "m", "coding",
                  "coding_002", 0.0, 100, "failed", "error: HTTPError 429: x")
    insert_result(str(db), run_id, "groq", "m", "thinking-planning",
                  "plan_001", 1.0, 100, "passed", None)
    # Contamination-style call: no evidence argument at all.
    insert_result(str(db), run_id, "contamination_check",
                  "contamination_warning", "contamination", "warning",
                  0.0, 0, "warning", "diverged")
    rows = get_results_for_run(str(db), run_id)
    by_key = {(r.category, r.problem_id): r for r in rows}
    _check("direct round-trip",
           by_key[("coding", "coding_001")].evidence, DIRECT)
    _check("testing gate-passed round-trip",
           by_key[("testing", "testing_001")].evidence, TESTING_OK)
    _check("testing gate-failed round-trip (kills None, not zero)",
           by_key[("testing", "testing_002")].evidence, TESTING_FAIL)
    _check("provider-failure evidence None",
           by_key[("coding", "coding_002")].evidence, None)
    _check("plan evidence None",
           by_key[("thinking-planning", "plan_001")].evidence, None)
    _check("contamination call without evidence arg",
           by_key[("contamination", "warning")].evidence, None)

    # 5. Fresh init_db creates the columns.
    fresh = tmp / "init.db"
    init_db(str(fresh))
    cols = {row[1] for row in sqlite3.connect(str(fresh)).execute(
        "PRAGMA table_info(results)")}
    _check("fresh init_db has all evidence columns",
           all(name in cols for name, _ in EVIDENCE_COLUMNS), True)

    # 6. Report + audit tolerance on a migrated-schema fixture run.
    audit_db = tmp / "audit.db"
    audit_run = create_run(str(audit_db), "verify-audit")
    _fixture_run(audit_db, audit_run, ["groq", "nvidia"])
    from aibenchmark.report import generate_report
    text = generate_report(audit_run, str(audit_db))
    assert "groq" in text and "nvidia" in text, "report missing providers"
    print("ok: generate_report renders on migrated schema")
    root = Path(__file__).resolve().parent
    audit_script = root / "audit_report.py"
    if not audit_script.exists():
        audit_script = root / "scripts" / "audit_report.py"
    if not audit_script.exists():
        raise SystemExit(
            "verify: audit_report.py not found in the project root or "
            "scripts/ — copy it to the project root and re-run this script. "
            "All evidence checks above already passed; only the audit "
            "tolerance check is blocked by the missing file."
        )
    proc = subprocess.run(
        [sys.executable, str(audit_script), str(audit_run), str(audit_db)],
        cwd=root,
        capture_output=True, text=True, timeout=120,
    )
    print(proc.stdout.strip().splitlines()[0] if proc.stdout else "")
    assert proc.returncode == 0, (
        f"audit failed on migrated schema:\n{proc.stdout}\n{proc.stderr}")
    print("ok: audit_report.py PASSES on migrated schema")
    print("PASS: all evidence-store checks passed")


if __name__ == "__main__":
    main()
