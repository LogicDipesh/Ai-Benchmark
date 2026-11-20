"""Add the test_details column to history.db (per-test step 3).

Run from the project root BEFORE the next bench run:
    python migrate_test_details.py [db_path]

Behavior:
- Refuses a missing database or a database without a results table.
- If test_details is already present, reports and changes nothing
  (no backup is written on a no-op run).
- Otherwise writes a timestamped backup FIRST
  (history.db.testdetails-backup-YYYYMMDD-HHMMSS), then adds the
  column. Existing rows get NULL: legacy rows stay "not recorded",
  never zero.
- Reports total rows and rows already carrying test details
  (expected 0 on the first migration: no instrumented run exists
  yet; run 28 will be the first).

Note: init_db auto-adds missing columns on the next bench run, so
forgetting this script loses nothing except the backup. Run it
anyway: the backup is the point.
"""
import os
import shutil
import sqlite3
import sys
from datetime import datetime, timezone


def main() -> int:
    db_path = sys.argv[1] if len(sys.argv) > 1 else "history.db"
    if not os.path.exists(db_path):
        print(f"migrate: no such database: {db_path}")
        return 1
    conn = sqlite3.connect(db_path)
    tables = {r[0] for r in
              conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "results" not in tables:
        print(f"migrate: no results table in {db_path}")
        conn.close()
        return 1
    cols = {r[1] for r in conn.execute("PRAGMA table_info(results)")}
    total = conn.execute("SELECT COUNT(*) FROM results").fetchone()[0]
    if "test_details" in cols:
        with_details = conn.execute(
            "SELECT COUNT(*) FROM results WHERE test_details IS NOT NULL"
        ).fetchone()[0]
        print(f"migrate: test_details already present in {db_path}; "
              f"nothing to do ({total} rows, {with_details} carry details).")
        conn.close()
        return 0
    conn.close()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup = f"{db_path}.testdetails-backup-{stamp}"
    shutil.copy(db_path, backup)
    print(f"migrate: backup written to {backup}")
    conn = sqlite3.connect(db_path)
    conn.execute("ALTER TABLE results ADD COLUMN test_details TEXT")
    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM results").fetchone()[0]
    with_details = conn.execute(
        "SELECT COUNT(*) FROM results WHERE test_details IS NOT NULL"
    ).fetchone()[0]
    conn.close()
    print(f"migrate: test_details added to {db_path} "
          f"({total} rows, {with_details} carry details).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
