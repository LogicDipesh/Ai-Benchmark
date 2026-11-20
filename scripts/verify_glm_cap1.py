"""Verify the GLM cap-1 experiment patch — no live calls, no keys,
no database. Run from the project root AFTER overwriting
aibenchmark/engine.py:
    python verify_glm_cap1.py
Then delete or move to scripts/.

Checks, by reading the installed engine.py (AST, so comments cannot
fool it):
  * MAX_CONCURRENT_PER_PROVIDER["zhipu"] is 1,
  * the other caps are unchanged: ollama 1, openrouter 2, nvidia 2,
    groq 2.
"""
import ast
import pathlib

tree = ast.parse((pathlib.Path("aibenchmark") / "engine.py").read_text())
caps = None
for node in ast.walk(tree):
    if isinstance(node, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id == "MAX_CONCURRENT_PER_PROVIDER" for t in node.targets
    ):
        assert isinstance(node.value, ast.Dict), "cap dict is not a literal dict"
        caps = {
            k.value: v.value
            for k, v in zip(node.value.keys, node.value.values)
            if isinstance(k, ast.Constant) and isinstance(v, ast.Constant)
        }
assert caps is not None, "MAX_CONCURRENT_PER_PROVIDER not found"
print(f"caps: {caps}")
assert caps["zhipu"] == 1, f'zhipu cap = {caps["zhipu"]}, want 1'
for name, want in (("ollama", 1), ("openrouter", 2), ("nvidia", 2), ("groq", 2)):
    assert caps[name] == want, f"{name} cap = {caps[name]}, want {want}"
print("ALL GLM CAP-1 CHECKS PASSED")
