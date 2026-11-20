"""Verify the failure-artifacts patch — no live calls, no keys,
no database. Run from the project root AFTER copying the patched
files:
    python verify_artifacts.py
Then delete or move to scripts/.

Checks, by reading the installed files (AST, so comments cannot
fool it):
  * aibenchmark/failure_artifacts.py exists and defines
    write_failure_artifact,
  * each code evaluator imports it and calls it inside an
    `if score < 1.0:` gate (score, not status — testing's status is
    "passed" for any score above 0, so a status gate would miss
    partials),
  * each code evaluator still uses max_tokens=8192 (the artifacts
    patch must not regress the 8192 cap),
  * testing.py still captures the pre-import-fix code.
"""
import ast
import pathlib

ROOT = pathlib.Path("aibenchmark")
CAT = ROOT / "categories"


def has_score_gate_call(tree):
    """True when some `if score < 1.0:` body calls
    write_failure_artifact."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if not (
            isinstance(test, ast.Compare)
            and isinstance(test.left, ast.Name)
            and test.left.id == "score"
            and len(test.ops) == 1
            and isinstance(test.ops[0], ast.Lt)
            and len(test.comparators) == 1
            and isinstance(test.comparators[0], ast.Constant)
            and test.comparators[0].value == 1.0
        ):
            continue
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) \
                    and sub.func.id == "write_failure_artifact":
                return True
    return False


def max_token_values(tree):
    values = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg == "max_tokens":
            assert isinstance(node.value, ast.Constant), "max_tokens not a literal"
            values.add(node.value.value)
    return values


helper = ROOT / "failure_artifacts.py"
assert helper.exists(), "aibenchmark/failure_artifacts.py missing"
helper_tree = ast.parse(helper.read_text())
assert any(
    isinstance(n, ast.FunctionDef) and n.name == "write_failure_artifact"
    for n in helper_tree.body
), "write_failure_artifact not defined"
print("failure_artifacts.py: write_failure_artifact defined")

for name in ("coding", "debugging", "testing"):
    path = CAT / f"{name}.py"
    text = path.read_text()
    tree = ast.parse(text)
    assert any(
        isinstance(n, ast.ImportFrom)
        and n.module == "aibenchmark.failure_artifacts"
        and any(a.name == "write_failure_artifact" for a in n.names)
        for n in ast.walk(tree)
    ), f"{name}.py: missing failure_artifacts import"
    assert has_score_gate_call(tree), (
        f"{name}.py: no write_failure_artifact call inside "
        f"`if score < 1.0:`"
    )
    values = max_token_values(tree)
    assert values == {8192}, f"{name}.py: max_tokens values = {values}, want {{8192}}"
    print(f"{name}.py: artifact call gated on score < 1.0, cap still 8192")

testing_text = (CAT / "testing.py").read_text()
assert "raw_test_code" in testing_text, "testing.py: pre-fix code not captured"
print("testing.py: pre-import-fix code captured")
print("ALL FAILURE-ARTIFACT CHECKS PASSED")
