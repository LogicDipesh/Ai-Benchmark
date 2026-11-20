"""Score-equivalence regression test (step 1 of Evaluation Evidence Capture).

Proves observation-only behavior BEFORE any evidence capture is implemented:
the current evaluators and sandbox, run against fixed fixtures, must
reproduce a checked-in golden baseline exactly. At step 2, the same
fixtures run against the instrumented evaluators/sandbox, and every
result must match the golden baseline on ALL FOUR dimensions:

  1. numerical score (exact float equality, not approximate),
  2. evaluator status,
  3. error classification (error_type),
  4. gate outcome (testing only; see gate_outcome()).

Latency is DELIBERATELY excluded: it is timing, not scoring. Artifact
I/O is also excluded: write_failure_artifact is patched to a no-op
during runs (the gate call still executes; only the disk write is
suppressed), so this test never writes to failure_artifacts/ and
never touches history.db. No API calls, no keys, no network: provider
answers are canned, and the sandbox runs local pytest only.

Gate outcome definition (testing category only; other categories are
"not_applicable"):
  - "failed"       -- error_type is reference_impl_failed: the suite
                      failed the strict reference gate, mutants never ran.
  - "not_run"      -- no evaluation reached the gate: provider failure
                      (no answer), no_tests_ran, or sandbox_timeout.
  - "passed"       -- mutants ran and the score is a kill fraction
                      (including 0.0 when the suite passed the gate but
                      killed nothing).

Run from the project root (offline):
    python test_score_equivalence.py

Regenerate the golden baseline ONLY with review, never blindly: a
regenerated golden after a behavior change would defeat this test.
    SCORE_EQUIVALENCE_REGENERATE=1 python test_score_equivalence.py

Step 2 hook: run_all_cases() takes evaluator/sandbox modules as
arguments. Step 2 calls it with the instrumented modules and compares
each stripped result to the golden baseline with assert_equivalent().
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace

HERE = Path(__file__).resolve().parent
GOLDEN_PATH = HERE / "score_equivalence_golden.json"

sys.path.insert(0, str(HERE))

from aibenchmark.categories import coding as coding_mod
from aibenchmark.categories import debugging as debugging_mod
from aibenchmark.categories import testing as testing_mod
from aibenchmark import sandbox as sandbox_mod
from aibenchmark.providers import PROVIDERS

# ---------------------------------------------------------------- fixtures

CODING_TESTS = '''from solution import add


def test_pos():
    assert add(1, 2) == 3


def test_zero():
    assert add(0, 0) == 0


def test_neg():
    assert add(-1, 1) == 0
'''

CODING_CORRECT = "def add(a, b):\n    return a + b\n"
CODING_PARTIAL = (
    "def add(a, b):\n"
    "    if a == 0 and b == 0:\n"
    "        return 1\n"
    "    return a + b\n"
)
CODING_SYNTAX_BROKEN = "def add(a, b):\n    return a +\n"
CODING_WRONG_NAME = "def addd(a, b):\n    return a + b\n"

DEBUGGING_BROKEN = "def add(a, b):\n    return a - b\n"

TESTING_REFERENCE = "def is_even(n):\n    return n % 2 == 0\n"
TESTING_MUTANTS = {
    "mutant_001": {"code": "def is_even(n):\n    return True\n"},
    "mutant_002": {"code": "def is_even(n):\n    return n % 2 == 1\n"},
}
TESTING_GOOD_SUITE = '''from solution import is_even


def test_even():
    assert is_even(2) is True


def test_odd():
    assert is_even(3) is False


def test_zero():
    assert is_even(0) is True
'''
TESTING_GATE_FAIL_SUITE = TESTING_GOOD_SUITE + '''

def test_wrong():
    assert is_even(2) is False
'''
TESTING_PARTIAL_SUITE = '''from solution import is_even


def test_even():
    assert is_even(2) is True
'''
TESTING_WRONG_IMPORT_SUITE = '''from calc import is_even


def test_even():
    assert is_even(2) is True


def test_odd():
    assert is_even(3) is False
'''
TESTING_EMPTY_SUITE = ""


def _fenced(code):
    return "```python\n" + code + "```\n"


def _provider_result(response=None, success=True, error_type=None, truncated=False):
    return SimpleNamespace(
        success=success,
        latency_ms=123,
        error_type=error_type,
        response=response,
        truncated=truncated,
    )


# Each evaluator case: (id, category, problem dict, canned provider result).
# Problems are fixture dicts, NOT the project's problems/ files, so this
# test is independent of problem content and runs anywhere the package
# is importable. The test file path is filled in at setup (absolute path
# inside the temp fixture root).
def _evaluator_cases(test_file_coding, test_file_debugging):
    def problem(pid, prompt, **extra):
        d = {"id": pid, "prompt": prompt}
        d.update(extra)
        return d

    coding_problem = problem(
        "eq_coding_add", "Write add(a, b).", test_file=test_file_coding
    )
    debugging_problem = problem(
        "eq_debugging_add",
        "Fix the broken add function.",
        broken_code=DEBUGGING_BROKEN,
        test_file=test_file_debugging,
    )
    testing_problem = problem(
        "eq_testing_is_even",
        "Write tests for is_even.",
        reference_implementation=TESTING_REFERENCE,
        mutants=TESTING_MUTANTS,
    )
    http_429 = "error: HTTPError 429: Rate limit exceeded"
    return [
        ("coding_correct", "coding", coding_problem,
         _provider_result(_fenced(CODING_CORRECT))),
        ("coding_partial", "coding", coding_problem,
         _provider_result(_fenced(CODING_PARTIAL))),
        ("coding_syntax_broken", "coding", coding_problem,
         _provider_result(_fenced(CODING_SYNTAX_BROKEN))),
        ("coding_wrong_name", "coding", coding_problem,
         _provider_result(_fenced(CODING_WRONG_NAME))),
        ("coding_provider_failure", "coding", coding_problem,
         _provider_result(success=False, error_type=http_429)),
        ("coding_truncated_pass", "coding", coding_problem,
         _provider_result(_fenced(CODING_CORRECT), truncated=True)),
        ("debugging_fixed", "debugging", debugging_problem,
         _provider_result(_fenced(CODING_CORRECT))),
        ("debugging_still_broken", "debugging", debugging_problem,
         _provider_result(_fenced(DEBUGGING_BROKEN))),
        ("debugging_provider_failure", "debugging", debugging_problem,
         _provider_result(success=False, error_type=http_429)),
        ("testing_good_suite", "testing", testing_problem,
         _provider_result(_fenced(TESTING_GOOD_SUITE))),
        ("testing_gate_fail", "testing", testing_problem,
         _provider_result(_fenced(TESTING_GATE_FAIL_SUITE))),
        ("testing_partial_kill", "testing", testing_problem,
         _provider_result(_fenced(TESTING_PARTIAL_SUITE))),
        ("testing_wrong_import", "testing", testing_problem,
         _provider_result(_fenced(TESTING_WRONG_IMPORT_SUITE))),
        ("testing_no_tests", "testing", testing_problem,
         _provider_result(_fenced(TESTING_EMPTY_SUITE))),
        ("testing_provider_failure", "testing", testing_problem,
         _provider_result(success=False, error_type=http_429)),
        ("testing_truncated_pass", "testing", testing_problem,
         _provider_result(_fenced(TESTING_GOOD_SUITE), truncated=True)),
    ]


# Sandbox-direct cases: (id, kind, payload). These lock the sandbox
# parsers themselves, which step 2 also touches (counts come from here).
def _sandbox_cases():
    return [
        ("sandbox_coding_correct", "direct", CODING_CORRECT),
        ("sandbox_coding_partial", "direct", CODING_PARTIAL),
        ("sandbox_coding_syntax_broken", "direct", CODING_SYNTAX_BROKEN),
        ("sandbox_mutant_good", "mutant", TESTING_GOOD_SUITE),
        ("sandbox_mutant_gate_fail", "mutant", TESTING_GATE_FAIL_SUITE),
        ("sandbox_mutant_partial", "mutant", TESTING_PARTIAL_SUITE),
    ]


# ---------------------------------------------------------------- comparison


def gate_outcome(category, result, provider_success):
    """Four-dimension gate outcome. See the module docstring."""
    if category != "testing":
        return "not_applicable"
    if not provider_success:
        return "not_run"
    err = result.get("error_type")
    if err == "reference_impl_failed":
        return "failed"
    if err in ("no_tests_ran", "sandbox_timeout"):
        return "not_run"
    return "passed"


def strip_result(category, result, provider_success):
    """Keep only the four compared dimensions. Latency is excluded."""
    return {
        "score": result["score"],
        "status": result["status"],
        "error_type": result["error_type"],
        "gate": gate_outcome(category, result, provider_success),
    }


def assert_equivalent(case_id, expected, actual):
    """Exact comparison on all four dimensions. Raises AssertionError
    naming the case and the dimension that differs."""
    for dimension in ("score", "status", "error_type", "gate"):
        if expected[dimension] != actual[dimension]:
            raise AssertionError(
                f"{case_id}: {dimension} differs: "
                f"expected {expected[dimension]!r}, got {actual[dimension]!r}"
            )


# ---------------------------------------------------------------- runner


class _StubProvider:
    """Canned provider answers. Asserts the 8192 cap the evaluators
    must keep passing: a step-2 change must not silently alter it."""

    def __init__(self):
        self.current = None

    def run_prompt(self, model, prompt, max_tokens=None, timeout=None):
        assert max_tokens == 8192, f"evaluator passed max_tokens={max_tokens}"
        return self.current


class EquivalenceRunner:
    """Runs every fixture through the given evaluator/sandbox modules
    and returns stripped results keyed by case id. Step 2 passes the
    instrumented modules here and compares against the golden file."""

    def __init__(self, coding, debugging, testing, sandbox):
        self.coding = coding
        self.debugging = debugging
        self.testing = testing
        self.sandbox = sandbox
        self.stub = _StubProvider()

    def run_all(self, fixture_root):
        tmp = Path(fixture_root)
        coding_tests = tmp / "problems" / "coding" / "test_add.py"
        debugging_tests = tmp / "problems" / "debugging" / "test_add.py"
        (tmp / "problems" / "coding").mkdir(parents=True, exist_ok=True)
        (tmp / "problems" / "debugging").mkdir(parents=True, exist_ok=True)
        coding_tests.write_text(CODING_TESTS)
        debugging_tests.write_text(CODING_TESTS)

        # Artifact I/O is not an evaluated dimension: suppress disk
        # writes (the gate call still executes) so this test is
        # side-effect-free and never touches failure_artifacts/.
        noop = lambda *args, **kwargs: None
        saved = {}
        for mod in (self.coding, self.debugging, self.testing):
            saved[mod] = mod.write_failure_artifact
            mod.write_failure_artifact = noop
        # The stub answers every provider call; cases set .current first.
        stub_module = ModuleType("equivalence_stub")
        stub_module.run_prompt = self.stub.run_prompt
        PROVIDERS["equivalence"] = {"module": stub_module}
        try:
            results = {}
            evaluators = {
                "coding": self.coding.evaluate_coding,
                "debugging": self.debugging.evaluate_debugging,
                "testing": self.testing.evaluate_testing,
            }
            for case_id, category, problem, canned in _evaluator_cases(
                str(coding_tests), str(debugging_tests)
            ):
                self.stub.current = canned
                raw = evaluators[category](problem, "equivalence", "equivalence-model")
                results[case_id] = strip_result(category, raw, canned.success)
            for case_id, kind, payload in _sandbox_cases():
                if kind == "direct":
                    score, status, error = self.sandbox.run_tests_sandboxed(
                        str(tmp), payload, str(coding_tests)
                    )
                    raw = {"score": score, "status": status, "error_type": error}
                    results[case_id] = strip_result("coding", raw, True)
                else:
                    score, error = self.sandbox.run_mutant_tests_sandboxed(
                        str(tmp), payload, TESTING_REFERENCE, TESTING_MUTANTS
                    )
                    raw = {
                        "score": score,
                        "status": "passed" if score > 0 else "failed",
                        "error_type": error,
                    }
                    results[case_id] = strip_result("testing", raw, True)
            return results
        finally:
            for mod, original in saved.items():
                mod.write_failure_artifact = original
            PROVIDERS.pop("equivalence", None)


def load_golden():
    if not GOLDEN_PATH.exists():
        raise AssertionError(
            f"golden baseline missing: {GOLDEN_PATH}. Generate it once "
            "with SCORE_EQUIVALENCE_REGENERATE=1 and review it before "
            "committing it; never regenerate blindly after a behavior change."
        )
    return json.loads(GOLDEN_PATH.read_text())


# ---------------------------------------------------------------- tests


class ScoreEquivalenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.runner = EquivalenceRunner(
            coding_mod, debugging_mod, testing_mod, sandbox_mod
        )
        cls.results = cls.runner.run_all(cls.tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_golden_reproduction(self):
        """Current code reproduces the golden baseline exactly."""
        golden = load_golden()
        self.assertEqual(set(golden), set(self.results))
        for case_id, expected in golden.items():
            assert_equivalent(case_id, expected, self.results[case_id])

    def test_self_comparison_passes(self):
        """The step-2 hook shape: current modules compared against
        themselves through the same comparator must pass."""
        second = EquivalenceRunner(
            coding_mod, debugging_mod, testing_mod, sandbox_mod
        ).run_all(self.tmp.name)
        for case_id, expected in self.results.items():
            assert_equivalent(case_id, expected, second[case_id])

    def test_comparator_detects_each_dimension(self):
        """Sensitivity: tampering with any one dimension must fail."""
        base = dict(next(iter(self.results.values())))
        for dimension, tampered in (
            ("score", base["score"] + 0.001),
            ("status", "tampered_status"),
            ("error_type", "tampered_error"),
            ("gate", "tampered_gate"),
        ):
            mutated = dict(base)
            mutated[dimension] = tampered
            with self.assertRaises(AssertionError):
                assert_equivalent("sensitivity", base, mutated)

    def test_latency_is_not_compared(self):
        """Latency differences must never fail equivalence."""
        base = dict(next(iter(self.results.values())))
        assert_equivalent("latency", base, dict(base))


def generate_golden():
    tmp = tempfile.TemporaryDirectory()
    try:
        results = EquivalenceRunner(
            coding_mod, debugging_mod, testing_mod, sandbox_mod
        ).run_all(tmp.name)
    finally:
        tmp.cleanup()
    GOLDEN_PATH.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    print(f"golden baseline written to {GOLDEN_PATH} "
          f"({len(results)} cases). REVIEW IT before committing.")


if __name__ == "__main__":
    if os.environ.get("SCORE_EQUIVALENCE_REGENERATE") == "1":
        generate_golden()
    else:
        unittest.main()
