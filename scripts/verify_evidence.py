"""Verify step-2 evidence capture (run from the project root, offline).

Asserts the evidence values the instrumented evaluators and sandbox
return, including the NULL semantics: counts are None (never zero)
when nothing was measured (provider failure, killed run), and gate
failures report kills as None (never measured) with mutants "not_run".

No API calls, no keys, no database writes: provider answers are
canned, artifact writes are suppressed, pytest runs locally only.
"""
import sys
import tempfile
from pathlib import Path
from types import ModuleType, SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))

from aibenchmark.categories import coding as coding_mod
from aibenchmark.categories import debugging as debugging_mod
from aibenchmark.categories import testing as testing_mod
from aibenchmark import sandbox as sandbox_mod
from aibenchmark.providers import PROVIDERS

TESTS = '''from solution import add


def test_pos():
    assert add(1, 2) == 3


def test_zero():
    assert add(0, 0) == 0


def test_neg():
    assert add(-1, 1) == 0
'''

TESTS_WITH_SKIP = '''from solution import add
import pytest


def test_pos():
    assert add(1, 2) == 3


def test_zero():
    assert add(0, 0) == 0


@pytest.mark.skip(reason="fixture skip")
def test_skipped():
    assert add(9, 9) == 0
'''

CORRECT = "def add(a, b):\n    return a + b\n"
PARTIAL = (
    "def add(a, b):\n"
    "    if a == 0 and b == 0:\n"
    "        return 1\n"
    "    return a + b\n"
)
SYNTAX_BROKEN = "def add(a, b):\n    return a +\n"
REFERENCE = "def is_even(n):\n    return n % 2 == 0\n"
MUTANTS = {
    "mutant_001": {"code": "def is_even(n):\n    return True\n"},
    "mutant_002": {"code": "def is_even(n):\n    return n % 2 == 1\n"},
}
GOOD_SUITE = '''from solution import is_even


def test_even():
    assert is_even(2) is True


def test_odd():
    assert is_even(3) is False


def test_zero():
    assert is_even(0) is True
'''
GATE_FAIL_SUITE = GOOD_SUITE + '''

def test_wrong():
    assert is_even(2) is False
'''
PARTIAL_SUITE = '''from solution import is_even


def test_even():
    assert is_even(2) is True
'''


def _fenced(code):
    return "```python\n" + code + "```\n"


class _Stub:
    def __init__(self):
        self.current = None

    def run_prompt(self, model, prompt, max_tokens=None, timeout=None):
        assert max_tokens == 8192
        return self.current


def _result(response=None, success=True, error_type=None, truncated=False):
    return SimpleNamespace(
        success=success, latency_ms=7, error_type=error_type,
        response=response, truncated=truncated,
    )


def _check(name, actual, expected):
    assert actual == expected, f"{name}: expected {expected!r}, got {actual!r}"
    print(f"ok: {name}")


def main():
    tmp = Path(tempfile.mkdtemp())
    (tmp / "problems" / "coding").mkdir(parents=True)
    (tmp / "problems" / "debugging").mkdir(parents=True)
    coding_tests = tmp / "problems" / "coding" / "test_add.py"
    coding_tests.write_text(TESTS)
    skip_tests = tmp / "problems" / "coding" / "test_skip.py"
    skip_tests.write_text(TESTS_WITH_SKIP)

    stub = _Stub()
    stub_module = ModuleType("equivalence_stub")
    stub_module.run_prompt = stub.run_prompt
    PROVIDERS["equivalence"] = {"module": stub_module}
    noop = lambda *a, **k: None
    saved = {}
    for mod in (coding_mod, debugging_mod, testing_mod):
        saved[mod] = mod.write_failure_artifact
        mod.write_failure_artifact = noop
    try:
        coding_problem = {"id": "eq", "prompt": "p", "test_file": str(coding_tests)}
        skip_problem = {"id": "eq", "prompt": "p", "test_file": str(skip_tests)}
        testing_problem = {
            "id": "eq", "prompt": "p",
            "reference_implementation": REFERENCE, "mutants": MUTANTS,
        }

        stub.current = _result(_fenced(CORRECT))
        row = coding_mod.evaluate_coding(coding_problem, "equivalence", "m")
        _check("coding correct evidence", row["evidence"],
               {"passed": 3, "failed": 0, "skipped": 0, "errors": 0, "collected": 3})
        _check("coding correct score", (row["score"], row["status"]), (1.0, "passed"))

        stub.current = _result(_fenced(PARTIAL))
        row = coding_mod.evaluate_coding(coding_problem, "equivalence", "m")
        _check("coding partial evidence", row["evidence"],
               {"passed": 2, "failed": 1, "skipped": 0, "errors": 0, "collected": 3})
        _check("coding partial score", (row["score"], row["status"]),
               (0.6666666666666666, "partial"))

        stub.current = _result(_fenced(CORRECT))
        row = coding_mod.evaluate_coding(skip_problem, "equivalence", "m")
        _check("skipped excluded from denominator, included in collected",
               (row["score"], row["evidence"]),
               (1.0, {"passed": 2, "failed": 0, "skipped": 1, "errors": 0, "collected": 3}))

        stub.current = _result(_fenced(SYNTAX_BROKEN))
        row = coding_mod.evaluate_coding(coding_problem, "equivalence", "m")
        _check("collection failure evidence is measured zeros, not None",
               (row["score"], row["error_type"], row["evidence"]),
               (0.0, "execution_error",
                {"passed": 0, "failed": 0, "skipped": 0, "errors": 0, "collected": 0}))

        stub.current = _result(success=False, error_type="error: HTTPError 429: x")
        row = coding_mod.evaluate_coding(coding_problem, "equivalence", "m")
        _check("provider failure evidence is None, never zero",
               (row["score"], row["evidence"]), (0.0, None))

        stub.current = _result(_fenced(GOOD_SUITE))
        row = testing_mod.evaluate_testing(testing_problem, "equivalence", "m")
        _check("testing good gate + kills", row["evidence"],
               {"gate_outcome": "passed",
                "gate": {"passed": 3, "failed": 0, "skipped": 0, "errors": 0, "collected": 3},
                "mutants_killed": 2, "mutants_total": 2,
                "mutants": {"mutant_001": "killed", "mutant_002": "killed"}})

        stub.current = _result(_fenced(GATE_FAIL_SUITE))
        row = testing_mod.evaluate_testing(testing_problem, "equivalence", "m")
        _check("gate failure: kills None, mutants not_run (never zero)",
               row["evidence"],
               {"gate_outcome": "failed",
                "gate": {"passed": 3, "failed": 1, "skipped": 0, "errors": 0, "collected": 4},
                "mutants_killed": None, "mutants_total": 2,
                "mutants": {"mutant_001": "not_run", "mutant_002": "not_run"}})
        _check("gate failure score", (row["score"], row["error_type"]),
               (0.0, "reference_impl_failed"))

        stub.current = _result(_fenced(PARTIAL_SUITE))
        row = testing_mod.evaluate_testing(testing_problem, "equivalence", "m")
        _check("partial kill evidence", row["evidence"],
               {"gate_outcome": "passed",
                "gate": {"passed": 1, "failed": 0, "skipped": 0, "errors": 0, "collected": 1},
                "mutants_killed": 1, "mutants_total": 2,
                "mutants": {"mutant_001": "survived", "mutant_002": "killed"}})

        stub.current = _result(_fenced(""))
        row = testing_mod.evaluate_testing(testing_problem, "equivalence", "m")
        _check("no-tests evidence", row["evidence"],
               {"gate_outcome": "not_run",
                "gate": {"passed": 0, "failed": 0, "skipped": 0, "errors": 0, "collected": 0},
                "mutants_killed": None, "mutants_total": 2,
                "mutants": {"mutant_001": "not_run", "mutant_002": "not_run"}})

        score, status, error, ev = sandbox_mod.run_tests_sandboxed_with_evidence(
            str(tmp), CORRECT, str(coding_tests))
        _check("sandbox direct with_evidence", (score, status, error, ev),
               (1.0, "passed", None,
                {"passed": 3, "failed": 0, "skipped": 0, "errors": 0, "collected": 3}))
        score, status, error = sandbox_mod.run_tests_sandboxed(
            str(tmp), CORRECT, str(coding_tests))
        _check("old sandbox interface unchanged", (score, status, error),
               (1.0, "passed", None))
        score, status, error, ev = sandbox_mod.run_tests_sandboxed_with_evidence(
            str(tmp), CORRECT, str(tmp / "missing.py"))
        _check("missing test file evidence is None", (score, status, error, ev),
               (0.0, "error", "test_file_missing",
                {"passed": None, "failed": None, "skipped": None,
                 "errors": None, "collected": None}))
        print("PASS: all evidence checks passed")
    finally:
        for mod, original in saved.items():
            mod.write_failure_artifact = original
        PROVIDERS.pop("equivalence", None)


if __name__ == "__main__":
    main()
