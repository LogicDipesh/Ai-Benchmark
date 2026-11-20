"""Migrate an existing history.db to the step-3 evidence schema.

Run from the project root:
    python migrate_evidence.py            # migrates ./history.db
    python migrate_evidence.py other.db   # migrates another database

What it does, in order:
  1. Refuses if the database file or its results table does not exist
     (it never creates a database; a bench run creates one).
  2. Copies the database to a timestamped backup
     (history.db.evidence-backup-YYYYMMDD-HHMMSS) and prints the path.
  3. Adds any missing evidence columns (idempotent: running it twice
     adds nothing the second time). Existing rows get NULL for new
     columns: legacy rows stay "not recorded", never zero.
  4. Prints the columns added, the row count, and how many rows
     already carry evidence (0 for a pre-step-3 database).

No bench code runs, no provider calls, no scores change. If the
project's bench has already run since step 3 was installed, the
migration already happened automatically (init_db migrates on every
write) and this script will report "already present".
"""
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from aibenchmark.history import EVIDENCE_COLUMNS, ensure_evidence_columns


def main(argv):
    db_path = Path(argv[0]) if argv else Path("history.db")
    if not db_path.exists():
        print(f"migrate: no such database: {db_path} (run bench first)")
        return 2
    conn = sqlite3.connect(str(db_path))
    tables = {row[0] for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'")}
    if "results" not in tables:
        print(f"migrate: {db_path} has no results table (run bench first)")
        conn.close()
        return 2
    conn.close()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup = db_path.with_name(f"{db_path.name}.evidence-backup-{stamp}")
    shutil.copy2(db_path, backup)
    print(f"migrate: backup written to {backup}")

    conn = sqlite3.connect(str(db_path))
    added = ensure_evidence_columns(conn)
    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM results").fetchone()[0]
    with_evidence = conn.execute(
        "SELECT COUNT(*) FROM results WHERE evidence_passed IS NOT NULL "
        "OR evidence_gate_outcome IS NOT NULL"
    ).fetchone()[0]
    conn.close()

    if added:
        print(f"migrate: added {len(added)} evidence column(s): "
              f"{', '.join(added)}")
    else:
        print("migrate: evidence columns already present (nothing to add)")
    print(f"migrate: {total} result rows, "
          f"{with_evidence} already carry evidence")
    print("migrate: done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
