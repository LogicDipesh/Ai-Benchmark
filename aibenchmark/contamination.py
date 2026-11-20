from datetime import date, datetime, timezone
import os
import yaml
from aibenchmark.history import insert_result

# DB category names use a hyphen ("thinking-planning"); the folder on disk
# uses an underscore ("thinking_planning"). Without this mapping the
# thinking-planning lookup never finds a file and always falls back to now.
_CATEGORY_DIRS = {"thinking-planning": "thinking_planning"}


def check_contamination(run_id: int, results: list) -> None:
    recent_problems = {}
    old_problems = {}
    for r in results:
        problem_id = r["problem_id"]
        created = get_problem_created(problem_id, r["category"])
        age_days = (datetime.now(timezone.utc) - created).days
        if age_days <= 30:
            recent_problems.setdefault((r["provider"], r["model"], r["category"]), []).append(r)
        else:
            old_problems.setdefault((r["provider"], r["model"], r["category"]), []).append(r)
    
    for key, recent_results in recent_problems.items():
        provider, model, category = key
        recent_scores = [r["score"] for r in recent_results]
        recent_avg = sum(recent_scores) / len(recent_scores) if recent_scores else 0
        
        old_results = old_problems.get(key, [])
        old_scores = [r["score"] for r in old_results]
        if not old_scores:
            continue
        old_avg = sum(old_scores) / len(old_scores)
        diff = abs(recent_avg - old_avg)
        if diff > 0.15:
            warning = (
                f"Contamination warning: Model {model} ({provider}) on category '{category}': "
                f"recent score {recent_avg:.2f} diverges from older score {old_avg:.2f} (diff={diff:.2f})"
            )
            insert_result(
                "history.db",
                run_id,
                "contamination_check",
                "contamination_warning",
                "contamination",
                "warning",
                0.0,
                0,
                "warning",
                warning,
            )


def get_problem_created(problem_id: str, category: str):
    problem_file = None
    problem_dir = os.path.join(
        "problems", _CATEGORY_DIRS.get(category, category)
    )
    if os.path.exists(problem_dir):
        for fname in os.listdir(problem_dir):
            if fname.endswith(".yaml") and problem_id in fname:
                problem_file = os.path.join(problem_dir, fname)
                break
    if not problem_file:
        return datetime.now(timezone.utc)
    with open(problem_file) as f:
        data = yaml.safe_load(f)
    created = data.get("created", "2026-09-20")
    # YAML may give a string ("2026-09-20", as in the current files), a
    # datetime, or a plain date if the value is unquoted. The old code
    # called .tzinfo on whatever it got, which crashes on a date object.
    # Any unparseable value falls back to now() instead of crashing the run.
    try:
        if isinstance(created, datetime):
            result = created
        elif isinstance(created, date):
            result = datetime.combine(created, datetime.min.time())
        elif isinstance(created, str):
            result = datetime.fromisoformat(created)
        else:
            return datetime.now(timezone.utc)
    except ValueError:
        return datetime.now(timezone.utc)
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result