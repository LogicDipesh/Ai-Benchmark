import yaml
import os
from aibenchmark.sandbox import extract_code, run_tests_sandboxed_with_evidence
from aibenchmark.failure_artifacts import write_failure_artifact
from aibenchmark.providers import PROVIDERS


def load_problem(problem_path: str) -> dict:
    with open(problem_path) as f:
        return yaml.safe_load(f)


def list_debugging_problems() -> list[dict]:
    debugging_dir = "problems/debugging"
    problems = []
    for fname in sorted(os.listdir(debugging_dir)):
        if fname.endswith(".yaml"):
            path = os.path.join(debugging_dir, fname)
            problem = load_problem(path)
            problems.append(problem)
    return problems


def evaluate_debugging(problem: dict, provider_name: str, model: str) -> dict:
    provider_info = PROVIDERS[provider_name]
    provider_module = provider_info["module"]
    
    prompt = problem["prompt"] + "\n\nBroken code:\n" + problem["broken_code"] + "\n\nReturn ONLY one Python code block and nothing else. No explanation, no preamble, no tests, no text outside the block."
    
    # 8192-cap experiment (was 4096): adjudicates OpenRouter debug_003
    # truncation (run 23's only truncated code row). Revert to 4096 to
    # restore the run-22/23 cap baseline.
    result = provider_module.run_prompt(model, prompt, max_tokens=8192)
    if not result.success:
        return {
            "problem_id": problem["id"],
            "model": model,
            "provider": provider_name,
            "category": "debugging",
            "score": 0.0,
            "latency_ms": result.latency_ms,
            "status": "failed",
            "error_type": result.error_type,
            "evidence": None,
        }
    
    code = extract_code(result.response)
    test_file = problem["test_file"]
    score, status, error_type, evidence = run_tests_sandboxed_with_evidence(
        "problems/debugging", code, test_file
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
            problem_id=problem["id"], category="debugging",
            provider=provider_name, model=model, score=score,
            status=status, error_type=error_type,
            latency_ms=result.latency_ms, prompt=prompt,
            raw_response=result.response, executed_code=code,
            test_file=test_file,
        )
    return {
        "problem_id": problem["id"],
        "model": model,
        "provider": provider_name,
        "category": "debugging",
        "score": score,
        "latency_ms": result.latency_ms,
        "status": status,
        "error_type": error_type,
        "evidence": evidence,
    }