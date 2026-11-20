"""Verify the capability/reliability report patch — no live calls, no
real database, no keys. Run from the project root AFTER overwriting
aibenchmark/report.py with the patched file:
    python verify_capability_report.py
Then delete or move to scripts/.

It feeds generate_report() synthetic rows that mirror Run 23's real
GLM + Groq rows (exact scores, error types and latencies) and checks:
  * blended Score and Current pick are unchanged (GLM coding 0.33,
    debugging 0.00, testing 0.33, TP 0.50; Groq picks all four),
  * capability means exclude request failures only (GLM coding 1.00
    over 1 valid, debugging "no valid evaluations", testing 0.67,
    TP 1.00; Groq truncated TP rows still count as valid),
  * reliability and valid counts match (GLM 33% / 0% / 50% / 50%),
  * the request-failure classifier accepts/rejects the right rows.
"""
from types import SimpleNamespace

import aibenchmark.report as R

ERR_1305 = 'error: HTTPError 429: {"error":{"code":"1305","message":"The service may be temporarily overloaded"}}'
ERR_1302 = 'error: HTTPError 429: {"error":{"code":"1302","message":"Rate limit reached for requests"}}'


def row(provider, model, category, problem, score, status, error, latency):
    return SimpleNamespace(
        provider=provider, model=model, category=category, problem_id=problem,
        score=score, status=status, error_type=error, latency_ms=latency,
    )


GLM, GROQ = "glm-4.7-flash", "openai/gpt-oss-120b"
ROWS = [
    # Run 23 GLM rows (exact scores/errors/latencies).
    row("zhipu", GLM, "coding", "coding_001", 1.0, "passed", None, 179156),
    row("zhipu", GLM, "coding", "coding_002", 0.0, "failed", ERR_1305, 47840),
    row("zhipu", GLM, "coding", "coding_003", 0.0, "failed", ERR_1305, 47701),
    row("zhipu", GLM, "debugging", "debug_001", 0.0, "failed", ERR_1305, 47897),
    row("zhipu", GLM, "debugging", "debug_002", 0.0, "failed", ERR_1302, 46843),
    row("zhipu", GLM, "debugging", "debug_003", 0.0, "failed", ERR_1305, 47873),
    row("zhipu", GLM, "testing", "testing_001", 0.6666666666666666, "passed", None, 51989),
    row("zhipu", GLM, "testing", "testing_002", 0.0, "failed", ERR_1305, 47520),
    row("zhipu", GLM, "thinking-planning", "plan_001", 1.0, "passed", None, 17768),
    row("zhipu", GLM, "thinking-planning", "plan_002", 0.0, "failed", ERR_1305, 47254),
    # Run 23 Groq rows (exact).
    row("groq", GROQ, "coding", "coding_001", 1.0, "passed", None, 2966),
    row("groq", GROQ, "coding", "coding_002", 1.0, "passed", None, 3107),
    row("groq", GROQ, "coding", "coding_003", 1.0, "passed", None, 934),
    row("groq", GROQ, "debugging", "debug_001", 1.0, "passed", None, 962),
    row("groq", GROQ, "debugging", "debug_002", 1.0, "passed", None, 1423),
    row("groq", GROQ, "debugging", "debug_003", 1.0, "passed", None, 1196),
    row("groq", GROQ, "testing", "testing_001", 1.0, "passed", None, 1787),
    row("groq", GROQ, "testing", "testing_002", 1.0, "passed", None, 3247),
    row("groq", GROQ, "thinking-planning", "plan_001", 1.0, "passed", "truncated_at_cap", 8978),
    row("groq", GROQ, "thinking-planning", "plan_002", 1.0, "passed", "truncated_at_cap", 9592),
]

R.get_results_for_run = lambda db_path, run_id: ROWS
R.get_runs = lambda db_path: [SimpleNamespace(id=23, timestamp="2026-10-30T14:03:13Z", notes="Run23")]
out = R.generate_report(23)

EXPECTED = [
    # Blended Score + Current pick unchanged (real Run 23 numbers).
    "| glm-4.7-flash | zhipu | 0.33 | 91565 | failed |",
    "| glm-4.7-flash | zhipu | 0.00 | 47537 | failed |",
    "| glm-4.7-flash | zhipu | 0.33 | 49754 | failed |",
    "| glm-4.7-flash | zhipu | 0.50 | 32511 | failed |",
    "**Current pick: openai/gpt-oss-120b (groq)**",
    # Capability / reliability / valid counts.
    "| glm-4.7-flash | zhipu | 1.00 | 33% | 1/3 |",
    "| glm-4.7-flash | zhipu | — | 0% | 0/3 |",
    "| glm-4.7-flash | zhipu | 0.67 | 50% | 1/2 |",
    "| glm-4.7-flash | zhipu | 1.00 | 50% | 1/2 |",
    # Groq: truncated TP rows still count as valid evaluations.
    "| openai/gpt-oss-120b | groq | 1.00 | 100% | 2/2 |",
]
missing = [line for line in EXPECTED if line not in out]
assert not missing, f"missing expected lines: {missing}"
assert out.count("**Current pick: openai/gpt-oss-120b (groq)**") == 4, "picks changed"
assert "Capability = mean score over valid evaluations only" in out, "legend missing"
assert "Current pick = highest blended Score" in out, "pick-objective legend missing"
assert "Latency = mean across attempted tasks" in out, "latency-definition legend missing"

# Classifier unit checks.
cases = [
    (None, False), ("", False),
    (ERR_1305, True), (ERR_1302, True),
    ("error: HTTPError 503: Service Unavailable", True),
    ("connection_error", True),
    ("judge_error: HTTPError 429: quota", True),
    ("judge_error", True),
    ("truncated_at_cap", False),
    ("execution_error; truncated_at_cap", False),
    ("execution_error", False),
    ("reference_impl_failed", False),
    ("no_tests_ran", False),
    ("sandbox_timeout", False),
]
for error, want in cases:
    got = R._is_request_failure(error)
    assert got == want, f"_is_request_failure({error!r}) = {got}, want {want}"

print("ALL CAPABILITY/RELIABILITY CHECKS PASSED (synthetic GLM + Groq fixture only — 20 rows mirroring Run 23; this script does not load the real database)")
print("=" * 60)
print(out)
