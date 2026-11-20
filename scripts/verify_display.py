"""Verify the report display-mapping patch — no live calls, no real
database, no keys. Run from the project root AFTER overwriting
aibenchmark/report.py with the patched file:
  python verify_display.py
Then delete or move to scripts/.

Checks only the pure mapping function (no report rendering, no DB):
known stored types map to their readable labels, the truncation
suffix maps both parts, and unmapped values pass through verbatim
so no diagnostic detail is ever hidden.
"""

import sys

from aibenchmark.report import _display_error_type

CASES = [
    ("reference_impl_failed", "Reference validation failed"),
    ("execution_error", "Execution or collection error"),
    ("truncated_at_cap", "Output truncated at token limit"),
    ("execution_error; truncated_at_cap",
     "Execution or collection error; Output truncated at token limit"),
    ("sandbox_timeout", "Execution timed out"),
    ("no_tests_ran", "No tests ran"),
    ('error: HTTPError 429: {"code": 1305}',
     'error: HTTPError 429: {"code": 1305}'),
    ("error: ReadTimeout", "error: ReadTimeout"),
    ("judge_error: HTTPError 429: quota", "judge_error: HTTPError 429: quota"),
    ("error: retry_exhausted", "error: retry_exhausted"),
    (None, None),
    ("", None),
    ("   ", None),
]

failures = []
for stored, want in CASES:
    got = _display_error_type(stored)
    if got != want:
        failures.append((stored, want, got))
        print(f"FAIL: _display_error_type({stored!r}) = {got!r}, want {want!r}")
    else:
        print(f"PASS: {stored!r} -> {got!r}")

if failures:
    print(f"FAIL: {len(failures)} mapping case(s) failed")
    sys.exit(1)
print("PASS: all display-mapping cases pass")
