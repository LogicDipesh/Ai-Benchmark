"""Scorer integrity tests (2026-11-20 forgery fix).

Scores must come only from pytest's own JUnit XML. These tests prove:
  * a solution that prints fake PASSED lines and crashes scores 0;
  * fake lines cannot inflate a real run;
  * genuine correct / wrong solutions still score as before;
  * the mutant gate still works after the change;
  * the extract_code and judge-score parsers behave as documented.
"""
import os

import pytest
import yaml

from aibenchmark.categories.thinking_planning import _parse_judge_score
from aibenchmark.sandbox import (
    _parse_junitxml,
    extract_code,
    run_mutant_tests_sandboxed_with_evidence,
    run_tests_sandboxed_with_evidence,
)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODING_DIR = os.path.join(REPO, "problems", "coding")
CODING_001_TEST = os.path.join(CODING_DIR, "test_coding_001.py")
TESTING_001_YAML = os.path.join(
    REPO, "problems", "testing", "testing_001_valid_parentheses.yaml"
)

# The 2026-11-20 exploit, verbatim: prints three fake PASSED lines,
# then raises at import. Under the old stdout parser this scored
# (1.0, 'passed') with passed=3.
FAKE_ONLY = """\
print("test_solution.py::test_fake_a PASSED")
print("test_solution.py::test_fake_b PASSED")
print("test_solution.py::test_fake_c PASSED")
raise RuntimeError("boom")
"""

CORRECT_PALINDROME = """\
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def is_palindrome(head):
    vals = []
    cur = head
    while cur:
        vals.append(cur.val)
        cur = cur.next
    return vals == vals[::-1]
"""

# Passes the 5 tests that expect True, fails the 2 that expect False.
ALWAYS_TRUE = """\
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def is_palindrome(head):
    return True
"""

FAKE_PLUS_WRONG = (
    'print("test_solution.py::test_fake_a PASSED")\n'
    'print("test_solution.py::test_fake_b PASSED")\n' + ALWAYS_TRUE
)

GOOD_SUITE = """\
from solution import is_valid


def test_empty():
    assert is_valid("") is True


def test_simple():
    assert is_valid("()") is True


def test_nested():
    assert is_valid("{[]}") is True


def test_mismatch():
    assert is_valid("(]") is False


def test_unclosed():
    assert is_valid("((") is False
"""

# Import error at collection: the gate must fail, not "kill" mutants.
BROKEN_SUITE = """\
from solution import is_valid, no_such_function


def test_empty():
    assert is_valid("") is True
"""


def _score(code):
    return run_tests_sandboxed_with_evidence(
        CODING_DIR, code, CODING_001_TEST
    )


def _testing_001():
    with open(TESTING_001_YAML) as f:
        return yaml.safe_load(f)


def test_fake_passed_lines_score_zero():
    score, status, error_type, evidence = _score(FAKE_ONLY)
    assert score == 0.0
    assert status != "passed"
    assert evidence["passed"] == 0
    assert all("fake" not in t["name"] for t in evidence["tests"])


def test_fake_lines_cannot_inflate_real_run():
    score, status, error_type, evidence = _score(FAKE_PLUS_WRONG)
    # Identical to the same solution without the fake lines.
    assert score == pytest.approx(5 / 7)
    assert evidence["passed"] == 5
    assert all("fake" not in t["name"] for t in evidence["tests"])


def test_genuine_correct_solution_still_scores_full():
    score, status, error_type, evidence = _score(CORRECT_PALINDROME)
    assert score == 1.0
    assert status == "passed"
    assert evidence["passed"] == 7


def test_genuine_wrong_solution_scores_partial():
    score, status, error_type, evidence = _score(ALWAYS_TRUE)
    assert score == pytest.approx(5 / 7)
    assert status == "partial"
    assert evidence["passed"] == 5
    assert evidence["failed"] == 2


def test_mutant_gate_passes_and_kills():
    problem = _testing_001()
    score, error_type, evidence = run_mutant_tests_sandboxed_with_evidence(
        "", GOOD_SUITE, problem["reference_implementation"], problem["mutants"]
    )
    assert error_type is None
    assert evidence["gate_outcome"] == "passed"
    assert evidence["mutants_killed"] == 2
    assert score == pytest.approx(2 / 3)


def test_mutant_gate_fails_on_broken_suite():
    problem = _testing_001()
    score, error_type, evidence = run_mutant_tests_sandboxed_with_evidence(
        "", BROKEN_SUITE, problem["reference_implementation"],
        problem["mutants"],
    )
    assert score == 0.0
    assert error_type == "reference_impl_failed"
    assert evidence["gate_outcome"] == "failed"
    assert all(v == "not_run" for v in evidence["mutants"].values())


def _write_xml(tmp_path, body):
    path = tmp_path / "junit.xml"
    path.write_text(
        '<?xml version="1.0" encoding="utf-8"?>'
        '<testsuites><testsuite name="pytest">' + body + "</testsuite></testsuites>"
    )
    return str(path)


def test_parse_junitxml_counts_and_node_ids(tmp_path):
    path = _write_xml(
        tmp_path,
        '<testcase classname="test_solution" name="test_a" time="0.01" />'
        '<testcase classname="test_solution" name="test_b" time="0.01">'
        '<failure message="assert" /></testcase>'
        '<testcase classname="test_solution" name="test_c" time="0.01">'
        '<error message="boom" /></testcase>'
        '<testcase classname="test_solution" name="test_d" time="0.01">'
        '<skipped message="skip" /></testcase>'
        '<testcase classname="test_solution.TestCls" name="test_e" time="0.01" />'
        '<testcase classname="test_solution" name="test_f" time="0.01">'
        '<skipped type="pytest.xfail" message="expected" /></testcase>',
    )
    passed, failed, errors, skipped, tests = _parse_junitxml(path)
    # xfail is listed, not counted.
    assert (passed, failed, errors, skipped) == (2, 1, 1, 1)
    assert tests[0] == {"name": "test_solution.py::test_a", "status": "passed"}
    assert tests[1] == {"name": "test_solution.py::test_b", "status": "failed"}
    assert tests[2] == {"name": "test_solution.py::test_c", "status": "error"}
    assert tests[3] == {"name": "test_solution.py::test_d", "status": "skipped"}
    assert tests[4] == {
        "name": "test_solution.py::TestCls::test_e",
        "status": "passed",
    }
    assert tests[5] == {"name": "test_solution.py::test_f", "status": "xfail"}


def test_parse_junitxml_missing_file_returns_zeros(tmp_path):
    assert _parse_junitxml(str(tmp_path / "nope.xml")) == (0, 0, 0, 0, [])


def test_parse_junitxml_broken_file_returns_zeros(tmp_path):
    path = tmp_path / "broken.xml"
    path.write_text("<testsuites><testsuite><testcase")
    assert _parse_junitxml(str(path)) == (0, 0, 0, 0, [])


def test_extract_code_last_fenced_block_wins():
    resp = '```python\nprint("a")\n```\ntext\n```python\nprint("b")\n```'
    assert extract_code(resp) == 'print("b")'


def test_extract_code_tool_call_json():
    resp = '```json\n{"name": "x", "arguments": {"code": "print(1)"}}\n```'
    assert extract_code(resp) == "print(1)"


def test_extract_code_fallback_returns_prose():
    assert extract_code("just prose, no code") == "just prose, no code"


def test_judge_score_dict():
    assert _parse_judge_score('{"score": 0.75}') == 0.75


def test_judge_score_bare_number():
    assert _parse_judge_score("0.5") == 0.5


def test_judge_score_clamped():
    assert _parse_judge_score('{"score": 1.5}') == 1.0


def test_judge_score_prose_wrapped():
    assert _parse_judge_score('Here is my score: {"score": 0.25} done') == 0.25


def test_judge_score_garbage_raises():
    with pytest.raises(ValueError):
        _parse_judge_score("no numbers here at all")
