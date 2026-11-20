"""OpenRouter candidate smoke test (read-only; touches nothing in the
benchmark).

Purpose: qualify a replacement for the openrouter slot WITHOUT
changing the registry. The registry keeps
`cohere/north-mini-code:free` until a candidate passes here.

What it does, in order, for each candidate model id:
  0. Lists https://openrouter.ai/api/v1/models (no key, no quota)
     and checks the id exists there and is priced free. An id that
     is absent or non-free is SKIPPED, so no generation call (and
     no daily-budget request) is ever burned on a dead id.
  1. Makes ONE chat-completions call that mirrors the bench's
     provider module exactly: same endpoint, same OpenAI-compatible
     messages shape, max_tokens=8192, NO temperature field (bench
     reverted to provider defaults at run 17). The prompt is the
     bench's own coding_001 prompt plus the run-22 code-only suffix.
  2. Reports: HTTP status, returned model id, finish_reason,
     latency, token usage (including reasoning tokens when the
     provider reports them), rate-limit headers, and whether the
     response contains a COMPLETE fenced code block (the closing
     fence is required, exactly as sandbox.extract_code requires).
  3. Runs a functional probe on the extracted code in a temp dir
     under a 10-second subprocess timeout (the bench's sandbox
     limit): the code must define ListNode and a module-level
     is_palindrome, and must return True for [1,2,2,1] and the
     empty/single-node cases, False for [1,2,3].

Verdict PASS requires: HTTP 200, finish_reason "stop" (the
8192-token-cap check: "length" means the bench would truncate
it), a complete code block, the required interface, and all
functional cases green. Passing this probe QUALIFIES the model
for a full bench run; it does not predict its bench score.

Quota: one generation call per candidate that passes step 0
(2 by default). Nothing here touches history.db, the registry,
or any benchmark file; the only file written is the JSON report
in the current directory.

Usage (fresh PowerShell, from E:\\AI-Benchmark):
    python smoke_openrouter_candidates.py
    python smoke_openrouter_candidates.py nvidia/nemotron-3-ultra-550b-a55b:free
    python smoke_openrouter_candidates.py --list

--list prints every free model id in the live listing with its
context length and pricing (no key, no quota), and writes the
same rows to openrouter_free_models_<UTC stamp>.json. Pick
candidates from that list, not from articles: a listed id still
needs the live smoke call to prove it is callable (a listed-free
model can be gated to agentic harnesses, as Inkling Small was).

The key is read from the OPENROUTER_API_KEY environment variable
only. It is never printed, pasted, or written anywhere.
"""

import ast
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

MODELS_URL = "https://openrouter.ai/api/v1/models"
CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"

DEFAULT_CANDIDATES = [
    "recursive/flint:free",
    "thinkingmachines/inkling-small:free",
]

# The bench's own coding_001 prompt + run-22 code-only suffix.
PROMPT = (
    "Implement a function `is_palindrome(head)` that checks if a singly\n"
    "linked list is a palindrome. The linked list node is defined as:\n"
    "\n"
    "class ListNode:\n"
    "    def __init__(self, val=0, next=None):\n"
    "        self.val = val\n"
    "        self.next = next\n"
    "\n"
    "Return True if the linked list is a palindrome, False otherwise.\n"
    "\n"
    "You must implement the solution in a file called solution.py.\n"
    "Return only a single Python code block, no prose.\n"
    "\n"
    "\n"
    "Return ONLY one Python code block and nothing else. No explanation, "
    "no preamble, no tests, no text outside the block."
)

# Same fenced-block rule as sandbox.extract_code: the LAST fenced
# block, and only if it has a closing fence.
FENCE_RE = re.compile(r"```(?:\w+)?\n(.*?)```", re.DOTALL)

CHECK_RUNNER = '''\
import sys
from solution import ListNode, is_palindrome

def build(values):
    head = None
    for value in reversed(values):
        head = ListNode(value, head)
    return head

cases = [
    ([1, 2, 2, 1], True),
    ([1, 2, 3], False),
    ([], True),
    ([7], True),
]
ok = True
for values, expected in cases:
    try:
        got = is_palindrome(build(values))
    except Exception as exc:
        print(f"FAIL {values}: raised {type(exc).__name__}")
        ok = False
        continue
    if got is not expected:
        print(f"FAIL {values}: got {got!r}, expected {expected!r}")
        ok = False
    else:
        print(f"PASS {values}")
print("FUNCTIONAL_OK" if ok else "FUNCTIONAL_FAIL")
'''


def collapse(text, limit=500):
    return " ".join(str(text).split())[:limit]


def _is_free_pricing(pricing):
    pricing = pricing or {}
    free_values = ("0", 0, 0.0, None)
    return pricing.get("prompt") in free_values \
        and pricing.get("completion") in free_values


def fetch_listing(requests):
    """GET the public model listing. Returns the entry list, or None
    on any failure. No key, no quota."""
    try:
        resp = requests.get(MODELS_URL, timeout=60)
    except Exception as exc:
        print(f"ERROR: listing request failed: {type(exc).__name__}: {exc}")
        return None
    if resp.status_code != 200:
        print(f"ERROR: listing returned HTTP {resp.status_code}: "
              f"{collapse(resp.text)}")
        return None
    return resp.json().get("data", [])


def list_free():
    """--list: print every free model id in the live listing."""
    try:
        import requests
    except ImportError:
        print("ERROR: the 'requests' package is required.")
        sys.exit(2)
    entries = fetch_listing(requests)
    if entries is None:
        sys.exit(2)
    rows = []
    for entry in entries:
        if _is_free_pricing(entry.get("pricing")):
            rows.append({
                "id": entry.get("id"),
                "context_length": entry.get("context_length"),
                "prompt_price": (entry.get("pricing") or {}).get("prompt"),
                "completion_price": (entry.get("pricing") or {}).get("completion"),
            })
    rows.sort(key=lambda row: row["id"] or "")
    print(f"{len(rows)} free models in the live listing:")
    print(f"{'model id':50} {'context':>10}  prompt  completion")
    for row in rows:
        print(f"{row['id']:50} {str(row['context_length']):>10}  "
              f"{row['prompt_price']}  {row['completion_price']}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out_path = f"openrouter_free_models_{stamp}.json"
    with open(out_path, "w") as fh:
        json.dump({"models": rows}, fh, indent=2)
    print(f"\nList written to {out_path}")
    print("Pick candidates from this list, then smoke-test them:")
    print("  python smoke_openrouter_candidates.py <model-id> [<model-id> ...]")
    print("A listed id still needs the live smoke call: listing-free "
          "does not prove callable.")


def check_listing(candidates):
    """Step 0: verify ids exist and are free, without spending quota."""
    print("Step 0: checking OpenRouter model listing (no key, no quota)...")
    try:
        import requests
    except ImportError:
        print("ERROR: the 'requests' package is required.")
        sys.exit(2)
    entries = fetch_listing(requests)
    if entries is None:
        return {}, requests
    by_id = {}
    for entry in entries:
        by_id[entry.get("id")] = entry
    approved = {}
    for model_id in candidates:
        entry = by_id.get(model_id)
        if entry is None:
            print(f"  SKIP {model_id}: id not in the listing.")
            continue
        pricing = entry.get("pricing") or {}
        prompt_price = pricing.get("prompt")
        completion_price = pricing.get("completion")
        context = entry.get("context_length")
        print(f"  FOUND {model_id}: context_length={context}, "
              f"pricing prompt={prompt_price} completion={completion_price}")
        if not _is_free_pricing(pricing):
            print(f"  SKIP {model_id}: listing shows non-zero pricing.")
            continue
        approved[model_id] = entry
    return approved, requests


def extract_code(response_text):
    matches = FENCE_RE.findall(response_text or "")
    return matches[-1] if matches else None


def functional_probe(code):
    """Run the extracted code's interface + behaviour in a temp dir
    under the bench's 10-second sandbox limit. Returns (ok, output)."""
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "solution.py"), "w") as fh:
            fh.write(code)
        with open(os.path.join(tmp, "check.py"), "w") as fh:
            fh.write(CHECK_RUNNER)
        try:
            proc = subprocess.run(
                [sys.executable, "check.py"], cwd=tmp, capture_output=True,
                text=True, timeout=10)
        except subprocess.TimeoutExpired:
            return False, "probe timed out after 10 seconds"
        output = (proc.stdout + proc.stderr).strip()
        return "FUNCTIONAL_OK" in proc.stdout, output


def smoke_one(model_id, api_key, requests):
    print(f"\n=== {model_id} ===")
    result = {"model_requested": model_id}
    payload = {"model": model_id,
               "messages": [{"role": "user", "content": PROMPT}],
               "max_tokens": 8192}
    headers = {"Authorization": f"Bearer {api_key}",
               "Content-Type": "application/json"}
    started = time.monotonic()
    try:
        resp = requests.post(CHAT_URL, headers=headers, json=payload,
                             timeout=300)
    except Exception as exc:
        print(f"  HTTP request failed: {type(exc).__name__}: {exc}")
        result.update({"http_status": None, "verdict": "FAIL",
                       "reason": f"request failed: {type(exc).__name__}"})
        return result
    latency_ms = int((time.monotonic() - started) * 1000)
    result["latency_ms"] = latency_ms
    result["http_status"] = resp.status_code
    for header in ("x-ratelimit-limit", "x-ratelimit-remaining",
                   "x-ratelimit-reset"):
        if header in resp.headers:
            result[header] = resp.headers[header]
            print(f"  {header}: {resp.headers[header]}")
    if resp.status_code != 200:
        print(f"  HTTP {resp.status_code}: {collapse(resp.text)}")
        result.update({"verdict": "FAIL",
                       "reason": f"HTTP {resp.status_code}"})
        return result
    try:
        body = resp.json()
    except ValueError:
        print("  Response was not JSON.")
        result.update({"verdict": "FAIL", "reason": "non-JSON response"})
        return result
    choice = (body.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    content = message.get("content")
    if isinstance(content, list):
        content = "".join(
            part.get("text", "") for part in content
            if isinstance(part, dict))
    finish = choice.get("finish_reason")
    usage = body.get("usage") or {}
    details = usage.get("completion_tokens_details") or {}
    result.update({
        "model_returned": body.get("model"),
        "finish_reason": finish,
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "reasoning_tokens": details.get("reasoning_tokens"),
        "raw_chars": len(content or ""),
    })
    print(f"  HTTP 200 in {latency_ms} ms; model returned: {body.get('model')}")
    print(f"  finish_reason: {finish}")
    print(f"  usage: prompt={usage.get('prompt_tokens')} "
          f"completion={usage.get('completion_tokens')} "
          f"reasoning={details.get('reasoning_tokens')}")
    print(f"  raw content: {len(content or '')} chars")
    if finish != "stop":
        print("  CAP CHECK FAILED: finish_reason is not 'stop'; the bench "
              "would truncate this output at 8192 tokens.")
        result.update({"verdict": "FAIL",
                       "reason": f"finish_reason {finish!r}, not 'stop'"})
        return result
    code = extract_code(content)
    if code is None:
        print("  EXTRACTION FAILED: no complete fenced code block "
              "(missing closing fence).")
        result.update({"verdict": "FAIL",
                       "reason": "no complete fenced code block"})
        return result
    print(f"  extracted code: {len(code)} chars")
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        print(f"  SYNTAX FAILED: {exc}")
        result.update({"verdict": "FAIL", "reason": f"SyntaxError: {exc}"})
        return result
    names = set()
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.FunctionDef):
            names.add(node.name)
    if "ListNode" not in names or "is_palindrome" not in names:
        print(f"  INTERFACE FAILED: top-level definitions found: "
              f"{sorted(names)}")
        result.update({"verdict": "FAIL",
                       "reason": "ListNode/is_palindrome interface missing"})
        return result
    ok, output = functional_probe(code)
    print("  functional probe:")
    for line in output.splitlines():
        print(f"    {line}")
    if not ok:
        result.update({"verdict": "FAIL",
                       "reason": "functional probe failed"})
        return result
    print("  VERDICT: PASS")
    result.update({"verdict": "PASS", "reason": None})
    return result


def main():
    if "--list" in sys.argv:
        list_free()
        return
    candidates = sys.argv[1:] or DEFAULT_CANDIDATES
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY is not set in this window.")
        print("It was made persistent on 2026-10-28 via a User-scope "
              "environment variable; open PowerShell fresh and retry.")
        print("Never paste the key in chat or into a file.")
        sys.exit(2)
    approved, requests = check_listing(candidates)
    results = []
    for model_id in candidates:
        if model_id not in approved:
            results.append({"model_requested": model_id,
                            "verdict": "SKIP",
                            "reason": "not found in listing or not free"})
            continue
        results.append(smoke_one(model_id, api_key, requests))
        time.sleep(5)
    print("\n=== Comparison ===")
    print(f"{'model':42} {'finish':10} {'ms':>7} "
          f"{'compl':>6} {'reason':>7}  verdict")
    for row in results:
        print(f"{row['model_requested']:42} "
              f"{str(row.get('finish_reason')):10} "
              f"{str(row.get('latency_ms', '')):>7} "
              f"{str(row.get('completion_tokens', '')):>6} "
              f"{str(row.get('reasoning_tokens', '')):>7}  "
              f"{row['verdict']}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out_path = f"smoke_openrouter_candidates_{stamp}.json"
    with open(out_path, "w") as fh:
        json.dump({"candidates": candidates, "results": results},
                  fh, indent=2)
    print(f"\nReport written to {out_path}")
    print("Registry untouched: cohere/north-mini-code:free stays the "
          "openrouter slot until you approve a swap.")
    passed = [r for r in results if r["verdict"] == "PASS"]
    if len(passed) == 1:
        print(f"Next step: swap in {passed[0]['model_requested']} only "
              f"after you approve it, with a run note naming the switch.")
    elif len(passed) > 1:
        print("More than one candidate passed: choose ONE replacement; "
              "never combine their results.")


if __name__ == "__main__":
    main()
