"""Check Run 31 TP capture artifacts (project root, after bench run).

Read-only: globs tp_artifacts/*__run31__*.json, validates structure,
and prints a per-file summary. Expected: 10 files (2 TP problems x
5 providers), every file with run_id 31. A provider-failed row has
judge None (expected, no judge ran); every other file must carry the
judge raw text and parsed score. Flags: wrong count, wrong run_id,
missing keys, judge dict without raw text on a judged row.
Exit 0 = all checks pass, 1 = a real problem found.
"""
import glob
import json
import os
import sys

files = sorted(glob.glob(os.path.join("tp_artifacts", "*__run31__*.json")))
print(f"TP artifacts for run 31: {len(files)} files")
problems = 0
for path in files:
    try:
        with open(path, encoding="utf-8") as fh:
            art = json.load(fh)
    except Exception as e:
        print(f"FAIL {path}: unreadable JSON ({type(e).__name__})")
        sys.exit(1)
    if art.get("run_id") != 31:
        print(f"FAIL {path}: run_id is {art.get('run_id')}, expected 31")
        sys.exit(1)
    for key in ("problem_id", "provider", "model", "prompt", "response",
                "finish_reason", "usage", "truncated", "error_type", "judge"):
        if key not in art:
            print(f"FAIL {path}: missing key {key}")
            sys.exit(1)
    judge = art["judge"]
    if judge is None:
        note = "judge None (provider failed, expected)" if art["error_type"] else "judge None UNEXPECTED"
        if not art["error_type"]:
            print(f"FAIL {path}: {note}")
            sys.exit(1)
    else:
        if not isinstance(judge.get("raw"), str):
            print(f"FAIL {path}: judged row without raw judge text")
            sys.exit(1)
        note = f"judge score {judge.get('score')}"
    problems += 1
    print(f"  {art['problem_id']} | {art['provider']} | finish={art['finish_reason']} "
          f"| truncated={art['truncated']} | {note}")
if len(files) != 10:
    print(f"FAIL: expected 10 TP artifacts, found {len(files)}")
    sys.exit(1)
print("TP capture check: PASS")
