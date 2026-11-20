import ast
import re
import yaml
import os
from aibenchmark.sandbox import extract_code, run_mutant_tests_sandboxed_with_evidence
from aibenchmark.failure_artifacts import write_failure_artifact
from aibenchmark.providers import PROVIDERS

# Module names models commonly invent instead of "solution". Used ONLY as
# whole-word matches (see _fix_imports); never as substring replacements,
# which is what corrupted "parentheses" into "solutiontheses" before.
_KNOWN_WRONG_MODULES = {"paren_check", "paren", "parentheses"}

_FROM_IMPORT_RE = re.compile(
    r"^(\s*)from\s+([A-Za-z_][A-Za-z0-9_]*)\s+import\s+(.+)$"
)
_IMPORT_RE = re.compile(
    r"^(\s*)import\s+([A-Za-z_][A-Za-z0-9_]*)(?:\s+as\s+([A-Za-z_][A-Za-z0-9_]*))?\s*$"
)


def _ref_function_names(reference_implementation: str) -> list[str]:
    """Top-level function / class names defined by the reference code.

    Used to know what a generated test file should import from solution,
    instead of hardcoding one problem's function name (the old code always
    added `is_valid`, which is wrong for every other testing problem).
    """
    try:
        tree = ast.parse(reference_implementation)
    except SyntaxError:
        return []
    names = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append(node.name)
    return names


def _fix_imports(test_code: str, ref_names: list[str]) -> str:
    """Rewrite imports of the tested function(s) to come from `solution`.

    Rules, in order, per line (regex with word boundaries, not substrings):
    * `from <mod> import <name>` where <mod> is not solution and either
      <mod> is a known wrong module or <name> is a reference function
      -> `from solution import <name>`.
    * `import <mod>` / `import <mod> as <alias>` where <mod> is a known
      wrong module -> `import solution as <alias or mod>`, preserving
      later uses like `paren_check.is_valid`.
    * If no solution import remains and reference names are known, prepend
      `from solution import <ref_names>`.
    """
    fixed_lines = []
    for line in test_code.splitlines():
        m = _FROM_IMPORT_RE.match(line)
        if m:
            indent, module, imported = m.groups()
            imported_names = [
                part.strip().split(" as ")[0].strip()
                for part in imported.split(",")
            ]
            if module != "solution" and (
                module in _KNOWN_WRONG_MODULES
                or any(name in ref_names for name in imported_names)
            ):
                fixed_lines.append(f"{indent}from solution import {imported}")
                continue
            fixed_lines.append(line)
            continue
        m = _IMPORT_RE.match(line)
        if m:
            indent, module, alias = m.groups()
            if module in _KNOWN_WRONG_MODULES:
                fixed_lines.append(f"{indent}import solution as {alias or module}")
                continue
            fixed_lines.append(line)
            continue
        fixed_lines.append(line)
    fixed = "\n".join(fixed_lines)
    if ref_names and "from solution import" not in fixed and "import solution" not in fixed:
        fixed = f"from solution import {', '.join(ref_names)}\n" + fixed
    return fixed


def load_problem(problem_path: str) -> dict:
    with open(problem_path) as f:
        return yaml.safe_load(f)


def list_testing_problems() -> list[dict]:
    testing_dir = "problems/testing"
    problems = []
    for fname in sorted(os.listdir(testing_dir)):
        if fname.endswith(".yaml"):
            path = os.path.join(testing_dir, fname)
            problem = load_problem(path)
            problems.append(problem)
    return problems


def evaluate_testing(problem: dict, provider_name: str, model: str) -> dict:
    provider_info = PROVIDERS[provider_name]
    provider_module = provider_info["module"]
    
    prompt = problem["prompt"] + "\n\nReturn ONLY one Python code block containing the test code and nothing else. No explanation, no preamble, no text outside the block. Import the function from 'solution' module (e.g., 'from solution import is_valid')."
    
    # 8192-cap experiment (was 4096): adjudicates OpenRouter debug_003
    # truncation (run 23's only truncated code row). Revert to 4096 to
    # restore the run-22/23 cap baseline.
    result = provider_module.run_prompt(model, prompt, max_tokens=8192)
    if not result.success:
        return {
            "problem_id": problem["id"],
            "model": model,
            "provider": provider_name,
            "category": "testing",
            "score": 0.0,
            "latency_ms": result.latency_ms,
            "status": "failed",
            "error_type": result.error_type,
            "evidence": None,
        }
    
    raw_test_code = extract_code(result.response)
    ref_impl = problem["reference_implementation"]
    # Fix common import issues: models often import from a wrong module.
    # The function name(s) come from this problem's reference code, not
    # from a hardcoded name, so this works for dedupe as well as is_valid.
    test_code = _fix_imports(raw_test_code, _ref_function_names(ref_impl))

    mutants = problem["mutants"]
    
    score, error_type, evidence = run_mutant_tests_sandboxed_with_evidence(
        "problems/testing", test_code, ref_impl, mutants
    )
    
    # Output-time package: if the provider cut the answer at the token
    # cap (finish_reason/done_reason == "length"), say so in the row.
    # The score above is measured from the code as returned; the flag
    # keeps a truncation from being read as a model failure.
    if getattr(result, "truncated", False):
        error_type = "truncated_at_cap" if error_type is None \
            else f"{error_type}; truncated_at_cap"
    if score < 1.0:
        write_failure_artifact(
            problem_id=problem["id"], category="testing",
            provider=provider_name, model=model, score=score,
            status="passed" if score > 0 else "failed",
            error_type=error_type,
            latency_ms=result.latency_ms, prompt=prompt,
            raw_response=result.response, executed_code=test_code,
            pre_fix_code=raw_test_code,
            reference_implementation=ref_impl,
            mutant_ids=list(mutants.keys()),
        )
    return {
        "problem_id": problem["id"],
        "model": model,
        "provider": provider_name,
        "category": "testing",
        "score": score,
        "latency_ms": result.latency_ms,
        "status": "passed" if score > 0 else "failed",
        "error_type": error_type,
        "evidence": evidence,
    }