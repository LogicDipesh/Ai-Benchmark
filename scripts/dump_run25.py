"""Dump per-problem rows for bench Run #25, in readable order.
Save in the project root (E:\\AI-Benchmark), run, paste the output,
then delete or move to scripts/. No keys, no writes, read-only.
Expected: this is the GLM cap-1 experiment run (zhipu semaphore cap
1, all other providers unchanged) — label the run's notes
accordingly when running bench, e.g. bench run --notes "GLM cap-1
experiment".
"""
import sqlite3

conn = sqlite3.connect("history.db")
rows = conn.execute(
    """
    SELECT problem_id, category, provider, model, score, status,
           error_type, latency_ms
    FROM results
    WHERE run_id = 25
    ORDER BY category, problem_id, provider
    """
).fetchall()
conn.close()

print(f"Run 25: {len(rows)} rows")
print("problem_id | category | provider | model | score | status | error_type | latency_ms")
for r in rows:
    print(" | ".join(str(x) for x in r))
