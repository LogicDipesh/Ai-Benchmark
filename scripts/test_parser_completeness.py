"""Parser-completeness tests for per-test evidence capture (steps 1-2).

Two safeguards, tested separately from scoring:

A. Parser completeness: every pytest result line is captured whole
   (full node id + outcome), nothing is silently dropped or
   duplicated, and the captured list reconciles with the counts.
   Covers: passed / failed / skipped / error, parametrized ids
   (including a whitespace parameter, the case the old ::\\S+
   matcher dropped), XFAIL / XPASS, subtest summary lines,
   collection-error output, no-tests output, and printed-output
   lines that merely contain the word PASSED.

B. Score independence: the new parser must not change any scoring
   decision. For every implementation case, the old wrapper and the
   with-evidence call agree exactly on (score, status, error_type),
   and the step-1 equivalence test (run separately, unmodified)
   must still reproduce the golden baseline.

Also enforced: the tests invariant — tests is None exactly when the
counts are None (nothing measured: missing file, timeout, harness
error), and tests == [] exactly when pytest executed but produced
zero result lines (collection error, no tests collected).

Run from the project root (offline, no API calls, no history.db):
    python test_parser_completeness.py
"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from aibenchmark import sandbox as sandbox_mod


def _tally(tests):
    """Counts implied by a tests list, XFAIL/XPASS excluded (as in
    the parser). Returns (passed, failed, errors, skipped)."""
    p = f = e = s = 0
    for t in tests:
        if t["status"] == "passed":
            p += 1
        elif t["status"] == "failed":
            f += 1
        elif t["status"] == "error":
            e += 1
        elif t["status"] == "skipped":
            s += 1
    return p, f, e, s


def _check_reconciles(case, output):
    passed, failed, errors, skipped, tests = sandbox_mod._parse_pytest_output(output)
    assert _tally(tests) == (passed, failed, errors, skipped), (
        f"{case}: list tallies {_tally(tests)} != counts "
        f"{(passed, failed, errors, skipped)}")
    return passed, failed, errors, skipped, tests


class ParserCases(unittest.TestCase):
    def test_mixed_outcomes(self):
        out = (
            "test_a.py::test_one PASSED [ 20%]\n"
            "test_a.py::TestCls::test_two FAILED [ 40%]\n"
            "test_a.py::test_three SKIPPED [ 60%]\n"
            "test_a.py::test_four ERROR [ 80%]\n"
            "test_a.py::test_five PASSED [100%]\n"
        )
        p, f, e, s, tests = _check_reconciles("mixed", out)
        self.assertEqual((p, f, e, s), (2, 1, 1, 1))
        self.assertEqual(
            [t["name"] for t in tests],
            ["test_a.py::test_one", "test_a.py::TestCls::test_two",
             "test_a.py::test_three", "test_a.py::test_four",
             "test_a.py::test_five"])
        self.assertEqual(
            [t["status"] for t in tests],
            ["passed", "failed", "skipped", "error", "passed"])

    def test_padded_percent_and_skip_reason(self):
        # Real pytest -v shapes (caught by impl tests, not by the
        # single-space synthetic lines): the status column is padded
        # with spaces before the percentage, and skips carry a reason.
        out = (
            "test_solution.py::test_ok PASSED                                         [ 33%]\n"
            "test_solution.py::test_bad FAILED                                        [ 66%]\n"
            "test_solution.py::test_skip SKIPPED (unconditional skip)                 [100%]\n"
        )
        p, f, e, s, tests = _check_reconciles("padded", out)
        self.assertEqual((p, f, e, s), (1, 1, 0, 1))
        self.assertEqual([t["status"] for t in tests],
                         ["passed", "failed", "skipped"])

    def test_parametrized_and_whitespace_param(self):
        # The exact case from the spec: the old ::\\S+ matcher dropped
        # this line entirely (the id contains a space).
        out = (
            "tests/test_example.py::TestExample::test_value[hello world] PASSED [ 50%]\n"
            "tests/test_example.py::TestExample::test_value[plain] FAILED [100%]\n"
        )
        p, f, e, s, tests = _check_reconciles("space-param", out)
        self.assertEqual((p, f, e, s), (1, 1, 0, 0))
        self.assertEqual(tests[0]["name"],
                         "tests/test_example.py::TestExample::test_value[hello world]")
        self.assertEqual(tests[0]["status"], "passed")
        self.assertEqual(tests[1]["name"],
                         "tests/test_example.py::TestExample::test_value[plain]")
        self.assertEqual(tests[1]["status"], "failed")

    def test_xfail_xpass_listed_not_counted(self):
        out = (
            "test_a.py::test_ok PASSED [ 33%]\n"
            "test_a.py::test_expected XFAIL [ 66%]\n"
            "test_a.py::test_unexpected XPASS [100%]\n"
        )
        p, f, e, s, tests = _check_reconciles("xfail", out)
        self.assertEqual((p, f, e, s), (1, 0, 0, 0))
        self.assertEqual(len(tests), 3)
        # Stored statuses are the lowercased pytest tokens.
        self.assertEqual([t["status"] for t in tests],
                         ["passed", "xfail", "xpass"])

    def test_subtest_summary_not_double_counted(self):
        # pytest-subtests style: a FAILED result line plus a SUBFAILED
        # summary line for the same test. The summary must not add a
        # second entry (it carries no trailing status token).
        out = (
            "test_a.py::TestCls::test_complex PASSED [ 50%]\n"
            "test_a.py::TestCls::test_other FAILED [100%]\n"
            "SUBFAILED(s='bad') test_a.py::TestCls::test_other\n"
        )
        p, f, e, s, tests = _check_reconciles("subtest", out)
        self.assertEqual((p, f, e, s), (1, 1, 0, 0))
        self.assertEqual(len(tests), 2)

    def test_collection_error_yields_empty_list(self):
        out = (
            "============================= test session starts ==============================\n"
            "collected 0 items / 1 error\n"
            "ERROR collecting test_a.py\n"
            "E   SyntaxError: invalid syntax\n"
        )
        p, f, e, s, tests = _check_reconciles("collection", out)
        self.assertEqual((p, f, e, s), (0, 0, 0, 0))
        self.assertEqual(tests, [])

    def test_no_tests_yields_empty_list(self):
        out = "collected 0 items\nno tests ran\n"
        p, f, e, s, tests = _check_reconciles("no-tests", out)
        self.assertEqual((p, f, e, s), (0, 0, 0, 0))
        self.assertEqual(tests, [])

    def test_printed_output_without_node_id_ignored(self):
        out = (
            "test output says PASSED but has no node id\n"
            "test_a.py::test_real PASSED [100%]\n"
        )
        p, f, e, s, tests = _check_reconciles("printed", out)
        self.assertEqual((p, f, e, s), (1, 0, 0, 0))
        self.assertEqual(len(tests), 1)


def _write(tmpdir, name, content):
    path = os.path.join(tmpdir, name)
    with open(path, "w") as fh:
        fh.write(content)
    return path


def _check_invariant(case, evidence):
    """tests is None ⟺ counts are None; tests == [] ⟺ counts all zero.
    Testing evidence carries its counts under evidence["gate"]; direct
    evidence carries them at the top level."""
    counts = evidence["gate"] if "gate_outcome" in evidence else evidence
    tests = evidence.get("tests")
    counts_none = counts["passed"] is None
    if counts_none:
        assert tests is None, f"{case}: counts None but tests={tests!r}"
    else:
        assert tests is not None, f"{case}: counts measured but tests None"
        all_zero = all(counts[k] == 0 for k in
                       ("passed", "failed", "skipped", "errors", "collected"))
        if all_zero:
            assert tests == [], f"{case}: counts zero but tests={tests!r}"
        else:
            assert len(tests) > 0, f"{case}: counts nonzero but tests empty"


class ImplCases(unittest.TestCase):
    def test_direct_mixed_suite(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = _write(tmpdir, "t.py",
                               "from solution import f\n"
                               "import pytest\n"
                               "def test_ok():\n    assert f() == 1\n"
                               "def test_bad():\n    assert f() == 2\n"
                               "@pytest.mark.skip\n"
                               "def test_skip():\n    assert False\n")
            code = "def f():\n    return 1\n"
            old = sandbox_mod.run_tests_sandboxed("", code, test_path)
            score, status, error, evidence = \
                sandbox_mod.run_tests_sandboxed_with_evidence("", code, test_path)
            self.assertEqual((score, status, error), old)
            self.assertEqual((score, status), (0.5, "partial"))
            self.assertEqual(
                [(t["name"], t["status"]) for t in evidence["tests"]],
                [("test_solution.py::test_ok", "passed"),
                 ("test_solution.py::test_bad", "failed"),
                 ("test_solution.py::test_skip", "skipped")])
            _check_invariant("direct-mixed", evidence)

    def test_direct_collection_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = _write(tmpdir, "t.py",
                               "from solution import f\n"
                               "def test_ok():\n    assert f() == 1\n")
            old = sandbox_mod.run_tests_sandboxed("", "def f(:\n", test_path)
            score, status, error, evidence = \
                sandbox_mod.run_tests_sandboxed_with_evidence("", "def f(:\n", test_path)
            self.assertEqual((score, status, error), old)
            self.assertEqual(error, "execution_error")
            self.assertEqual(evidence["tests"], [])
            _check_invariant("direct-collection", evidence)

    def test_direct_no_tests(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = _write(tmpdir, "t.py", "# no tests here\n")
            score, status, error, evidence = \
                sandbox_mod.run_tests_sandboxed_with_evidence(
                    "", "def f():\n    return 1\n", test_path)
            self.assertEqual(error, "no_tests_ran")
            self.assertEqual(evidence["tests"], [])
            _check_invariant("direct-no-tests", evidence)

    def test_direct_missing_file(self):
        score, status, error, evidence = \
            sandbox_mod.run_tests_sandboxed_with_evidence(
                "", "def f():\n    return 1\n", "/nonexistent/t.py")
        self.assertEqual(error, "test_file_missing")
        self.assertIsNone(evidence["tests"])
        _check_invariant("direct-missing", evidence)

    def test_direct_timeout_yields_tests_none(self):
        saved = sandbox_mod._run_pytest

        def _boom(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd="pytest", timeout=10)

        sandbox_mod._run_pytest = _boom
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                test_path = _write(tmpdir, "t.py",
                                   "def test_ok():\n    assert True\n")
                score, status, error, evidence = \
                    sandbox_mod.run_tests_sandboxed_with_evidence(
                        "", "x = 1\n", test_path)
        finally:
            sandbox_mod._run_pytest = saved
        self.assertEqual(error, "sandbox_timeout")
        self.assertIsNone(evidence["tests"])
        _check_invariant("direct-timeout", evidence)

    def test_gate_failed_list_names_the_failure(self):
        ref = ("def is_even(n):\n    return n % 2 == 0\n")
        suite = ("from solution import is_even\n"
                 "def test_even():\n    assert is_even(2)\n"
                 "def test_odd():\n    assert not is_even(3)\n"
                 "def test_wrong():\n    assert is_even(3)\n")
        mutants = {"m1": {"code": "def is_even(n):\n    return True\n"}}
        old = sandbox_mod.run_mutant_tests_sandboxed("", suite, ref, mutants)
        score, error, evidence = \
            sandbox_mod.run_mutant_tests_sandboxed_with_evidence(
                "", suite, ref, mutants)
        self.assertEqual((score, error), old)
        self.assertEqual(error, "reference_impl_failed")
        self.assertEqual(evidence["gate_outcome"], "failed")
        self.assertIsNone(evidence["mutants_killed"])
        # Gate runs invoke pytest with "../test_generated.py", so the
        # printed (and stored) node ids carry that prefix — with a
        # forward slash on Linux, a backslash on Windows
        # ("..\\test_generated.py"). The parser stores exactly what
        # pytest printed; the GUI display rule strips everything up
        # to the first "::", so the displayed name is identical on
        # both platforms. Build the expectation from the platform's
        # own separator instead of hardcoding one form.
        prefix = os.path.join("..", "test_generated.py")
        self.assertEqual(
            [(t["name"], t["status"]) for t in evidence["tests"]],
            [(prefix + "::test_even", "passed"),
             (prefix + "::test_odd", "passed"),
             (prefix + "::test_wrong", "failed")])
        _check_invariant("gate-failed", evidence)

    def test_gate_passed_list_and_kills(self):
        ref = ("def is_even(n):\n    return n % 2 == 0\n")
        suite = ("from solution import is_even\n"
                 "def test_even():\n    assert is_even(2)\n"
                 "def test_odd():\n    assert not is_even(3)\n")
        mutants = {"m1": {"code": "def is_even(n):\n    return True\n"}}
        old = sandbox_mod.run_mutant_tests_sandboxed("", suite, ref, mutants)
        score, error, evidence = \
            sandbox_mod.run_mutant_tests_sandboxed_with_evidence(
                "", suite, ref, mutants)
        self.assertEqual((score, error), old)
        self.assertEqual(evidence["gate_outcome"], "passed")
        self.assertEqual(evidence["mutants_killed"], 1)
        self.assertEqual(
            [t["status"] for t in evidence["tests"]],
            ["passed", "passed"])
        _check_invariant("gate-passed", evidence)


if __name__ == "__main__":
    unittest.main(verbosity=2)
