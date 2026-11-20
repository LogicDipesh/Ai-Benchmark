"""Dump per-problem rows for bench Run #29, in readable order.
Save in the project root (E:\\AI-Benchmark), run, paste the output,
then delete or move to scripts/. No keys, no writes, read-only.
Expected: this is the FIRST run with Lightning in the openrouter slot —
label the run's notes accordingly when running bench, e.g.
bench run --notes "First run with the new openrouter slot (Lightning swap)".
"""
import sqlite3

conn = sqlite3.connect("history.db")
rows = conn.execute(
    """
    SELECT problem_id, category, provider, model, score, status,
           error_type, latency_ms
    FROM results
    WHERE run_id = 29
    ORDER BY category, problem_id, provider
    """
).fetchall()
conn.close()

print(f"Run 29: {len(rows)} rows")
print("problem_id | category | provider | model | score | status | error_type | latency_ms")
for r in rows:
    print(" | ".join(str(x) for x in r))
