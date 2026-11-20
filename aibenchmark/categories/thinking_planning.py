import yaml
import os
import json
import time
import requests
import threading
from aibenchmark.providers import PROVIDERS


def load_problem(problem_path: str) -> dict:
    with open(problem_path) as f:
        return yaml.safe_load(f)


def list_thinking_planning_problems() -> list[dict]:
    thinking_dir = "problems/thinking_planning"
    problems = []
    for fname in sorted(os.listdir(thinking_dir)):
        if fname.endswith(".yaml"):
            path = os.path.join(thinking_dir, fname)
            problem = load_problem(path)
            problems.append(problem)
    return problems


# 2026-10-27 judge switch (direct Gemini, supersedes fix v2):
# Gemma via OpenRouter failed 4 times in a row (3x 429, then 504 with an
# underlying 429 from Google AI Studio), and adding a BYOK Google key
# to OpenRouter did not lift it. The judge now calls the Gemini API
# DIRECTLY via Google's OpenAI-compatible endpoint, bypassing
# OpenRouter entirely — no OpenRouter key, no OpenRouter abort layer.
# 2026-10-29 judge switch (supersedes gemini-2.5-flash): Flash's RPD
# on THIS project is 20/day (AI Studio screenshot, project "Dipesh":
# Flash RPM 5, TPM 250K, RPD 20, usage 21/20) — one run needs 10 judge
# calls minimum, so a run with any failures exceeds the budget by
# itself (run 19 TP: 22 judge requests) and two runs in one Pacific
# day are impossible. Gemini 2.5 Flash Lite does NOT fix this: its
# RPD on this project is also 20 (RPM 15, TPM 250K). The models on
# this project with a usable judge budget are Gemini 3.1 Flash Lite
# and Gemini 3.5 Flash Lite, both RPM 15, TPM 250K, RPD 500 — 25x
# Flash's budget, same key, same endpoint. This file uses 3.5 Flash
# Lite; if its model ID is ever rejected, 3.1 Flash Lite carries
# identical limits and is the fallback (change JUDGE_MODEL only).
# Judge separation (plan §5a) still holds: no 3.x Flash Lite model
# is benchmarked (benchmarked models are Qwen, Cohere, Nemotron,
# GPT-OSS, GLM). TP scores under this judge are NOT comparable to
# TP scores under the Gemini 2.5 Flash judge (incl. demo run 14) —
# TP must be re-baselined from the first run under the new judge.
# Key env: GEMINI_API_KEY — unchanged (never in a file, never in
# chat). Do NOT enable billing on that Google Cloud project:
# billing removes the free tier for that project.
JUDGE_MODEL = "gemini-3.5-flash-lite"
JUDGE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"


def _parse_judge_score(judge_text: str) -> float:
    # Run 15 lesson: this parser zeroed all 10 TP rows. Two of its
    # assumptions were false in practice:
    #   * it assumed the judge always returns {"score": x} — one row
    #     returned a bare float, and .get() on a float raised
    #     AttributeError, recorded as judge_error;
    #   * it assumed any JSON failure means no score — but a judge
    #     that wraps its JSON in prose still gave a score.
    # The parser now accepts a dict, a bare number, or a numeric
    # string, and falls back to the first {...} block in the text.
    # What it still does NOT do: invent a score. If no JSON object
    # or number can be found, it raises, and the row is honestly
    # recorded as judge_error with score 0 — not silently scored.
    if judge_text is None:
        raise ValueError("judge returned no text")
    text = judge_text.strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        import re
        match = re.search(r"\{.*?\}", text, re.DOTALL)
        if not match:
            raise
        result = json.loads(match.group(0))
    if isinstance(result, (int, float)):
        score = float(result)
    elif isinstance(result, dict):
        score = float(result.get("score", 0.0))
    else:
        raise ValueError(f"unexpected judge output type: {type(result).__name__}")
    return max(0.0, min(1.0, score))


_JUDGE_LOCK = threading.Lock()
# Run 16 lesson: 6 TP rows lost to judge 429s. Judge calls were
# clustered in the TP phase of a parallel run, and each failing
# call retried 3x, amplifying quota use. Space judge requests at
# least this far apart (well under a 10/min free-tier rate) and
# back off longer on 429/503, so a retry lands in a fresh window
# instead of the same exhausted one.
_JUDGE_MIN_INTERVAL_S = 12.0
_JUDGE_LAST_TIME = 0.0


def _judge_error_type(e: Exception) -> str:
    """Format a judge failure with status + body snippet, like the
    providers' _http_error_type. Before this fix a judge failure
    recorded only "HTTPError: 429 Client Error" with no body, so a
    quota-exhausted 429 and a capacity-overload 429 were
    indistinguishable in the database — the exact ambiguity behind
    the run 13–19 judge-429 debate. The body is an error message
    from Google, never a key (keys travel only in headers)."""
    try:
        resp = getattr(e, "response", None)
        if resp is not None:
            status = resp.status_code
            body = " ".join((resp.text or "").split())[:500]
            if body:
                return f"HTTPError {status}: {body}"
            return f"HTTPError {status}"
    except Exception:
        pass
    return f"{type(e).__name__}: {e}"


def judge_response_with_raw(response: str, rubric: str):
    """Judge call returning (score, judge_text, judge_finish_reason,
    judge_usage, error_str). score is None on failure; error_str is
    None on success and already in _judge_error_type format on
    failure. Never raises for judge failures (missing key, HTTP,
    unparseable output) — the evaluator records them. The raw judge
    text is returned even when parsing fails, so capture never loses
    what the judge actually said. Transport behaviour is unchanged
    from judge_response (same spacing, same 502/503 retries, same
    fail-fast 429); only the return shape is new, so existing scores
    cannot change. This function is observational plumbing: the
    caller decides the row, and nothing here touches scoring.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        # Raised, not returned as 0.0, in the old judge_response;
        # here returned as an error string so the evaluator records
        # error_type "judge_error" exactly as before, so a judge
        # failure is no longer indistinguishable from a bad plan
        # (the run 10 trap).
        return None, None, None, None, "ValueError: GEMINI_API_KEY missing for judge"

    judge_prompt = f"""You are an expert evaluator. Score the following response on a scale of 0.0 to 1.0 based on this rubric:

{rubric}

Response to evaluate:
{response}

Return ONLY a JSON object with a single key "score" containing a float between 0.0 and 1.0. No other text."""

    # 2026-10-29 retry change: 429 FAILS FAST, no retry. Evidence:
    # judge 429s NEVER recovered via retry in runs 13, 16, 17, 19 —
    # every retried judge 429 ended as judge_error anyway, and each
    # retry burned one more request against a daily budget (Flash:
    # 20/day; even Flash Lite's 500/day is not infinite). Retrying a
    # 429 therefore costs budget and buys nothing. 502/503 are still
    # retried (3 attempts, 30s-then-60s backoff): those are transient
    # server overload by definition, and the run-18 judge 503s show
    # the server can be down for a stretch — but unlike 429, a 503
    # is not a budget signal, so one retry cycle is worth it.
    # (Run 12's lesson stands: 503 used to raise at once and lose a
    # plan; that is why 503 stays retryable while 429 does not.)
    _RETRYABLE = (502, 503)
    last_error = None
    for attempt in range(3):
        try:
            global _JUDGE_LAST_TIME
            _wait = _JUDGE_MIN_INTERVAL_S - (time.time() - _JUDGE_LAST_TIME)
            if _wait > 0:
                time.sleep(_wait)
            _JUDGE_LAST_TIME = time.time()
            resp = requests.post(
                JUDGE_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": JUDGE_MODEL,
                    "messages": [{"role": "user", "content": judge_prompt}],
                    "stream": False,
                },
                timeout=120,
            )
            if resp.status_code in _RETRYABLE and attempt < 2:
                time.sleep(30 * (attempt + 1))
                continue
            resp.raise_for_status()
            data = resp.json()
            judge_text = data["choices"][0]["message"]["content"]
            judge_finish = data["choices"][0].get("finish_reason")
            judge_usage_raw = data.get("usage")
            judge_usage = judge_usage_raw if isinstance(judge_usage_raw, dict) else None
            try:
                score = _parse_judge_score(judge_text)
            except Exception as e:
                return None, judge_text, judge_finish, judge_usage, _judge_error_type(e)
            return score, judge_text, judge_finish, judge_usage, None
        except Exception as e:
            last_error = e
            # A retryable status already retried above; other failures
            # return at once with their formatted error.
            if isinstance(e, requests.exceptions.HTTPError) and e.response is not None and e.response.status_code in _RETRYABLE:
                continue
            return None, None, None, None, _judge_error_type(e)
    return None, None, None, None, (_judge_error_type(last_error)
                                    if last_error is not None else "RuntimeError: judge failed")


def judge_response(response: str, rubric: str) -> float:
    """Backward-compatible wrapper: returns the parsed score, raising
    on judge failure as before. New code should call
    judge_response_with_raw to also capture the raw judge output."""
    score, _text, _finish, _usage, error = judge_response_with_raw(response, rubric)
    if error is not None:
        raise ValueError(error)
    return score


def evaluate_thinking_planning(problem: dict, provider_name: str, model: str) -> dict:
    provider_info = PROVIDERS[provider_name]
    provider_module = provider_info["module"]
    
    prompt = problem["prompt"]
    rubric = problem["judge_rubric"]
    
    result = provider_module.run_prompt(model, prompt, max_tokens=4096)
    if not result.success:
        # Observational capture (2026-11-02, run 31): the prompt and
        # the provider failure are recorded even though no judge ran.
        # getattr defaults keep this working with any provider result
        # shape; missing metadata stays None, never inferred.
        capture = {
            "prompt": prompt,
            "response": "",
            "finish_reason": getattr(result, "finish_reason", None),
            "usage": getattr(result, "usage", None),
            "truncated": getattr(result, "truncated", False),
            "latency_ms": result.latency_ms,
            "error_type": result.error_type,
            "rubric": rubric,
            "judge": None,
        }
        return {
            "problem_id": problem["id"],
            "model": model,
            "provider": provider_name,
            "category": "thinking-planning",
            "score": 0.0,
            "latency_ms": result.latency_ms,
            "status": "failed",
            "error_type": result.error_type,
            "tp_capture": capture,
        }
    
    response_text = result.response
    try:
        # Judge calls are serialised: with 5 provider threads running,
        # concurrent judge requests would burst Gemini's free-tier
        # rate limit (the run-13 judge-429 lesson). Judge calls are
        # fast when not rate-limited, so this lock costs little.
        # The try/except preserves the old catch-all: any unforeseen
        # judge-path exception becomes a judge_error row, never a
        # crashed evaluation.
        with _JUDGE_LOCK:
            score, judge_text, judge_finish, judge_usage, judge_error = \
                judge_response_with_raw(response_text, rubric)
    except Exception as e:
        score, judge_text, judge_finish, judge_usage = 0.0, None, None, None
        judge_error = _judge_error_type(e)
    if judge_error is not None:
        score = 0.0
        error_type = f"judge_error: {judge_error}"
        judge_block = {"raw": judge_text, "score": None,
                       "finish_reason": judge_finish, "usage": judge_usage}
    else:
        error_type = None
        judge_block = {"raw": judge_text, "score": score,
                       "finish_reason": judge_finish, "usage": judge_usage}
    
    # Output-time package: if the provider cut the answer at the token
    # cap (finish_reason/done_reason == "length"), say so in the row.
    # The score above is measured from the code as returned; the flag
    # keeps a truncation from being read as a model failure.
    if getattr(result, "truncated", False):
        error_type = "truncated_at_cap" if error_type is None \
            else f"{error_type}; truncated_at_cap"
    # Observational capture (2026-11-02, run 31): the complete model
    # response as received (including truncation), the provider
    # metadata exactly as supplied, and the judge's raw output next
    # to its parsed score. The evaluator stays run-ID unaware by
    # design; the engine attaches the run ID when it writes the
    # artifact. This key never feeds scoring, classification,
    # reliability, model selection, or ranking.
    capture = {
        "prompt": prompt,
        "response": response_text,
        "finish_reason": getattr(result, "finish_reason", None),
        "usage": getattr(result, "usage", None),
        "truncated": getattr(result, "truncated", False),
        "latency_ms": result.latency_ms,
        "error_type": error_type,
        "rubric": rubric,
        "judge": judge_block,
    }
    return {
        "problem_id": problem["id"],
        "model": model,
        "provider": provider_name,
        "category": "thinking-planning",
        "score": score,
        "latency_ms": result.latency_ms,
        "status": "passed" if score > 0 else "failed",
        "error_type": error_type,
        "tp_capture": capture,
    }