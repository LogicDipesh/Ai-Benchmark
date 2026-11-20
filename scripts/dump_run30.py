"""Dump per-problem rows for bench Run #30, in readable order.
Save in the project root (E:\\AI-Benchmark), run, paste the output,
then delete or move to scripts/. No keys, no writes, read-only.
Expected: this is the REPEATABILITY CHECK for Lightning (run 29 debut) —
label the run's notes accordingly when running bench, e.g.
bench run --notes "Run 30 repeatability check: Lightning stays in openrouter slot; identical configuration to run 29, no code changes".
"""
import sqlite3

conn = sqlite3.connect("history.db")
rows = conn.execute(
    """
    SELECT problem_id, category, provider, model, score, status,
           error_type, latency_ms
    FROM results
    WHERE run_id = 30
    ORDER BY category, problem_id, provider
    """
).fetchall()
conn.close()

print(f"Run 30: {len(rows)} rows")
print("problem_id | category | provider | model | score | status | error_type | latency_ms")
for r in rows:
    print(" | ".join(str(x) for x in r))
