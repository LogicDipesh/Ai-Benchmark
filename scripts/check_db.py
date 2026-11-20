import sqlite3
conn = sqlite3.connect('history.db')
conn.row_factory = sqlite3.Row

# Check latest run
runs = conn.execute('SELECT * FROM runs ORDER BY id DESC LIMIT 1').fetchall()
for r in runs:
    print('Run {}: {} - {}'.format(r['id'], r['timestamp'], r['notes']))

run_id = runs[0]['id']
results = conn.execute('SELECT provider, model, category, problem_id, score, latency_ms, status, error_type FROM results WHERE run_id = ? ORDER BY category, score DESC', (run_id,)).fetchall()
for r in results:
    print('  {:15} {:12} {:30} score={:.2f} latency={}ms status={:8} error={}'.format(
        r['category'], r['provider'], r['model'], r['score'], r['latency_ms'], r['status'], r['error_type'] or 'None'))