"""Verify the 8192 code-cap experiment patch — no live calls, no keys,
no database. Run from the project root AFTER overwriting
aibenchmark/categories/{coding,debugging,testing}.py:
    python verify_cap8192.py
Then delete or move to scripts/.

Checks, by reading the installed files (AST, so comments cannot fool
it):
  * every max_tokens= value in coding.py, debugging.py, testing.py
    is 8192 (and nothing else),
  * every max_tokens= value in thinking_planning.py is still 4096,
  * the stricter code-only prompt suffix is still present in each
    code evaluator (the cap change must not disturb the prompt).
"""
import ast
import pathlib

ROOT = pathlib.Path("aibenchmark") / "categories"


def max_token_values(path):
    tree = ast.parse(path.read_text())
    values = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg == "max_tokens":
            assert isinstance(node.value, ast.Constant) and isinstance(node.value.value, int), (
                f"{path}: max_tokens is not a plain integer"
            )
            values.add(node.value.value)
    return values


for name in ("coding", "debugging", "testing"):
    path = ROOT / f"{name}.py"
    values = max_token_values(path)
    assert values == {8192}, f"{path}: max_tokens values = {values}, want {{8192}}"
    text = path.read_text()
    assert "Return ONLY one Python code block" in text, f"{path}: code-only prompt suffix missing"
    print(f"{name}.py: max_tokens = 8192, code-only prompt present")

tp_values = max_token_values(ROOT / "thinking_planning.py")
assert tp_values == {4096}, f"thinking_planning.py: max_tokens values = {tp_values}, want {{4096}}"
print("thinking_planning.py: max_tokens = 4096 (unchanged)")

print("ALL 8192-CAP CHECKS PASSED")
