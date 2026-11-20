import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

DB_PATH = "history.db"


@dataclass
class Run:
    id: int
    timestamp: str
    notes: str


@dataclass
class Result:
    id: int
    run_id: int
    provider: str
    model: str
    category: str
    problem_id: str
    score: float
    latency_ms: int
    status: str
    error_type: Optional[str]
    # Step 3: evidence counts captured during evaluation (step 2), or
    # None when nothing was measured (legacy rows, provider failures,
    # thinking-planning rows). None means "not recorded", never zero.
    evidence: Optional[dict] = None


# Step 3 evidence columns, in fixed order. Direct-test counts first,
# then testing gate + mutant counts, then the per-test list. All
# nullable: legacy rows and unmeasured rows (provider failures,
# plans) stay NULL, never zero.
EVIDENCE_COLUMNS = [
    ("evidence_passed", "INTEGER"),
    ("evidence_failed", "INTEGER"),
    ("evidence_skipped", "INTEGER"),
    ("evidence_errors", "INTEGER"),
    ("evidence_collected", "INTEGER"),
    ("evidence_gate_outcome", "TEXT"),
    ("evidence_gate_passed", "INTEGER"),
    ("evidence_gate_failed", "INTEGER"),
    ("evidence_gate_skipped", "INTEGER"),
    ("evidence_gate_errors", "INTEGER"),
    ("evidence_gate_collected", "INTEGER"),
    ("evidence_mutants_killed", "INTEGER"),
    ("evidence_mutants_total", "INTEGER"),
    ("evidence_mutants_json", "TEXT"),
    # Per-test evidence (phase 2): the ordered (node id, outcome)
    # list as JSON. NULL = never recorded; "[]" = pytest executed
    # with zero result lines. Never zero-as-absence: [] is data.
    ("test_details", "TEXT"),
]


def ensure_evidence_columns(conn) -> list[str]:
    """Add any missing evidence columns to results (idempotent).
    Existing rows get NULL for new columns: legacy rows stay
    "not recorded", never zero. Returns the names added (empty if
    the schema already has them)."""
    existing = {row[1] for row in conn.execute("PRAGMA table_info(results)")}
    added = []
    for name, coltype in EVIDENCE_COLUMNS:
        if name not in existing:
            conn.execute(f"ALTER TABLE results ADD COLUMN {name} {coltype}")
            added.append(name)
    return added


def init_db(db_path: str = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            notes TEXT
        );
        CREATE TABLE IF NOT EXISTS results (
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
            evidence_passed INTEGER,
            evidence_failed INTEGER,
            evidence_skipped INTEGER,
            evidence_errors INTEGER,
            evidence_collected INTEGER,
            evidence_gate_outcome TEXT,
            evidence_gate_passed INTEGER,
            evidence_gate_failed INTEGER,
            evidence_gate_skipped INTEGER,
            evidence_gate_errors INTEGER,
            evidence_gate_collected INTEGER,
            evidence_mutants_killed INTEGER,
            evidence_mutants_total INTEGER,
            evidence_mutants_json TEXT,
            test_details TEXT,
            FOREIGN KEY (run_id) REFERENCES runs(id)
        );
        """
    )
    ensure_evidence_columns(conn)
    conn.commit()
    conn.close()


def create_run(db_path: str, notes: str = "") -> int:
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    ts = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        "INSERT INTO runs (timestamp, notes) VALUES (?, ?)",
        (ts, notes),
    )
    conn.commit()
    run_id = cur.lastrowid
    conn.close()
    return run_id


def _tests_json(evidence) -> str | None:
    """JSON for the evidence "tests" list, preserving the NULL vs []
    distinction: None (or a missing key, e.g. evidence built by
    pre-per-test code) stays NULL; [] stores "[]"."""
    tests = evidence.get("tests")
    return json.dumps(tests) if tests is not None else None


def insert_result(
    db_path: str,
    run_id: int,
    provider: str,
    model: str,
    category: str,
    problem_id: str,
    score: float,
    latency_ms: int,
    status: str,
    error_type: Optional[str] = None,
    evidence: Optional[dict] = None,
) -> int:
    """Insert one result row. evidence is the step-2/pertest dict
    (direct or testing shape) or None. None leaves every evidence
    column NULL: the row records that nothing was measured, never a
    zero. When evidence carries "tests", it is stored as JSON (None
    stays NULL, [] stays "[]"); a missing key also stays NULL."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    columns = [
        "run_id", "provider", "model", "category", "problem_id",
        "score", "latency_ms", "status", "error_type",
    ]
    values = [
        run_id, provider, model, category, problem_id,
        score, latency_ms, status, error_type,
    ]
    if evidence is not None:
        if "gate_outcome" in evidence:
            gate = evidence["gate"] or {}
            columns += [
                "evidence_gate_outcome",
                "evidence_gate_passed", "evidence_gate_failed",
                "evidence_gate_skipped", "evidence_gate_errors",
                "evidence_gate_collected",
                "evidence_mutants_killed", "evidence_mutants_total",
                "evidence_mutants_json",
                "test_details",
            ]
            values += [
                evidence["gate_outcome"],
                gate.get("passed"), gate.get("failed"),
                gate.get("skipped"), gate.get("errors"),
                gate.get("collected"),
                evidence.get("mutants_killed"),
                evidence.get("mutants_total"),
                json.dumps(evidence.get("mutants", {}), sort_keys=True),
                _tests_json(evidence),
            ]
        else:
            columns += [
                "evidence_passed", "evidence_failed", "evidence_skipped",
                "evidence_errors", "evidence_collected",
                "test_details",
            ]
            values += [
                evidence["passed"], evidence["failed"],
                evidence["skipped"], evidence["errors"],
                evidence["collected"],
                _tests_json(evidence),
            ]
    placeholders = ", ".join("?" for _ in values)
    cur = conn.execute(
        f"INSERT INTO results ({', '.join(columns)}) VALUES ({placeholders})",
        values,
    )
    conn.commit()
    result_id = cur.lastrowid
    conn.close()
    return result_id


def _row_tests(row) -> Optional[list]:
    """Per-test list from a row, or None when never recorded. Safe
    on databases predating the test_details column (column absent
    means not recorded, not an error). "[]" round-trips as []."""
    if "test_details" not in row.keys():
        return None
    raw = row["test_details"]
    return json.loads(raw) if raw else None


def _row_evidence(row) -> Optional[dict]:
    """Rebuild the step-2 evidence dict from a sqlite3.Row, or None
    when nothing was measured. Safe on pre-step-3 databases: if the
    evidence columns are absent, the row predates capture and the
    answer is None (not recorded), not an error."""
    keys = row.keys()
    if "evidence_passed" not in keys:
        return None
    gate_outcome = row["evidence_gate_outcome"]
    if gate_outcome is not None:
        mutants_json = row["evidence_mutants_json"]
        return {
            "gate_outcome": gate_outcome,
            "gate": {
                "passed": row["evidence_gate_passed"],
                "failed": row["evidence_gate_failed"],
                "skipped": row["evidence_gate_skipped"],
                "errors": row["evidence_gate_errors"],
                "collected": row["evidence_gate_collected"],
            },
            "mutants_killed": row["evidence_mutants_killed"],
            "mutants_total": row["evidence_mutants_total"],
            "mutants": json.loads(mutants_json) if mutants_json else {},
            "tests": _row_tests(row),
        }
    counts = (
        row["evidence_passed"], row["evidence_failed"],
        row["evidence_skipped"], row["evidence_errors"],
        row["evidence_collected"],
    )
    if all(v is None for v in counts):
        return None
    return {
        "passed": counts[0],
        "failed": counts[1],
        "skipped": counts[2],
        "errors": counts[3],
        "collected": counts[4],
        "tests": _row_tests(row),
    }


def get_runs(db_path: str = DB_PATH) -> list[Run]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM runs ORDER BY id DESC").fetchall()
    conn.close()
    return [Run(row["id"], row["timestamp"], row["notes"]) for row in rows]


def get_results_for_run(db_path: str, run_id: int) -> list[Result]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM results WHERE run_id = ?", (run_id,)
    ).fetchall()
    conn.close()
    return [
        Result(
            r["id"], r["run_id"], r["provider"], r["model"], r["category"],
            r["problem_id"], r["score"], r["latency_ms"], r["status"], r["error_type"],
            _row_evidence(r),
        )
        for r in rows
    ]


def get_latest_run_id(db_path: str = DB_PATH) -> Optional[int]:
    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT id FROM runs ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    return row[0] if row else None


def get_trend_data(
    db_path: str,
    category: str,
    model: str,
    provider: str,
) -> list[Result]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT r.* FROM results r
        JOIN runs run ON r.run_id = run.id
        WHERE r.category = ? AND r.model = ? AND r.provider = ?
        ORDER BY run.timestamp ASC
        """,
        (category, model, provider),
    ).fetchall()
    conn.close()
    return [
        Result(
            r["id"], r["run_id"], r["provider"], r["model"], r["category"],
            r["problem_id"], r["score"], r["latency_ms"], r["status"], r["error_type"],
            _row_evidence(r),
        )
        for r in rows
    ]
