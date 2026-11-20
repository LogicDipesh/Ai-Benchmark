"""Dump per-problem rows for bench Run #23, in readable order.
Save in the project root (E:\\AI-Benchmark), run, paste the output,
then delete or move to scripts/. No keys, no writes, read-only.
NOTE: the previous paste ran dump_run22.py by mistake, so it showed
run 22's rows again. This script filters run_id = 23.
"""
import sqlite3

conn = sqlite3.connect("history.db")
rows = conn.execute(
    """
    SELECT problem_id, category, provider, model, score, status,
           error_type, latency_ms
    FROM results
    WHERE run_id = 23
    ORDER BY category, problem_id, provider
    """
).fetchall()
conn.close()

print(f"Run 23: {len(rows)} rows")
print("problem_id | category | provider | model | score | status | error_type | latency_ms")
for r in rows:
    print(" | ".join(str(x) for x in r))
