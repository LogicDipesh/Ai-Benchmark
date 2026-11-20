from dataclasses import dataclass
from typing import Optional
import threading
import time
import requests

_thread_local = threading.local()


def _session() -> requests.Session:
    """One HTTP session per thread (2026-10-30 API optimisation).

    Reuses the TCP/TLS connection across calls instead of
    re-handshaking every time. Thread-local because a provider's
    calls now run on up to 2 worker threads; sessions carry no
    cookies or auth state here (keys go in per-request headers),
    but thread-local costs nothing and removes the question.
    """
    sess = getattr(_thread_local, "session", None)
    if sess is None:
        sess = requests.Session()
        _thread_local.session = sess
    return sess


@dataclass
class ProviderResult:
    response: str
    success: bool
    latency_ms: int
    error_type: Optional[str] = None
    truncated: bool = False
    # TP-capture metadata (2026-11-02, run 31; observational only):
    # finish_reason and usage are recorded exactly as the provider
    # supplied them. Absent values stay None; nothing is inferred
    # (in particular total_tokens is never summed from prompt +
    # completion). These fields never affect scores, classification,
    # reliability, model selection, or ranking.
    finish_reason: Optional[str] = None
    usage: Optional[dict] = None


NVIDIA_BASE = "https://integrate.api.nvidia.com/v1"
NVIDIA_API_KEY_ENV = "NVIDIA_API_KEY"


def _http_error_type(e: requests.exceptions.HTTPError) -> str:
    """Format an HTTP failure with status + body snippet, not just the
    exception class name. Before this fix every provider failure
    collapsed to "error: HTTPError", which made run 11's 6 fast
    HTTPError rows undiagnosable (429? 500? something else?).
    Body is whitespace-collapsed and truncated to 500 chars; it is
    an error message from the provider, never a key (keys are only
    ever sent in request headers, never echoed in error bodies)."""
    status = "?"
    body = ""
    try:
        if e.response is not None:
            status = e.response.status_code
            body = " ".join((e.response.text or "").split())[:500]
    except Exception:
        pass
    return f"error: HTTPError {status}: {body}" if body else f"error: HTTPError {status}"


def _http_status(e: requests.exceptions.HTTPError):
    try:
        return e.response.status_code if e.response is not None else None
    except Exception:
        return None


def _extract_message_text(message: dict) -> str:
    """Return the model's text, never None.

    Run 13 proved a provider can return message.content = None (a
    tool-call-only reply, e.g. north-mini-code on testing_001).
    The old code passed that None straight through as the response,
    and extract_code() then crashed with TypeError, losing the
    evaluation as an evaluator crash. Recovery order:
    1. a plain string content, as usual;
    2. a content-parts list, joined from its text parts;
    3. the first tool call's arguments, if they carry a "code"
       field (JSON or dict) — the model did answer, just in tool
       form;
    4. "" — an empty response scores honestly as a failed suite
       instead of crashing the evaluator.
    """
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            p.get("text", "") for p in content
            if isinstance(p, dict) and isinstance(p.get("text"), str)
        )
    for call in message.get("tool_calls") or []:
        fn = call.get("function", {}) if isinstance(call, dict) else {}
        args = fn.get("arguments", "")
        if isinstance(args, dict):
            if isinstance(args.get("code"), str):
                return args["code"]
            continue
        if isinstance(args, str) and args:
            try:
                import json
                parsed = json.loads(args)
                if isinstance(parsed, dict) and isinstance(parsed.get("code"), str):
                    return parsed["code"]
            except Exception:
                pass
            return args
    return ""


def _is_daily_quota(e: requests.exceptions.HTTPError) -> bool:
    """True when a 429 is a DAILY quota, not transient overload.

    Run 17 proved the difference matters: OpenRouter returned 429
    "Rate limit exceeded: free-models-per-day" (limit 50/day) for
    ALL 10 of its calls, because runs 12-16 had already used the
    day's 50 free-model requests. Retrying a daily quota is futile
    (it cannot clear until the quota resets) and burns 45s per
    call plus further requests. Fail fast instead, with the full
    error preserved so the cause is visible in the database.
    Zhipu's transient 429 ("service may be temporarily overloaded",
    code 1305) does NOT match this and is still retried.
    """
    try:
        body = (e.response.text or "") if e.response is not None else ""
    except Exception:
        return False
    lowered = body.lower()
    return "free-models-per-day" in lowered or "requests per day" in lowered


def run_prompt(model: str, prompt: str, max_tokens: int = None,
               timeout: int = None) -> ProviderResult:
    import os
    api_key = os.environ.get(NVIDIA_API_KEY_ENV)
    start = time.time()
    call_timeout = timeout if timeout is not None else 300
    if not api_key:
        latency_ms = int((time.time() - start) * 1000)
        return ProviderResult(
            response="", success=False, latency_ms=latency_ms, error_type="missing_api_key"
        )
    # 2026-10-28 retry fix: a 429 is transient overload, not a model
    # failure — run 12 proved this with GLM (5x 429 code 1305
    # "service may be temporarily overloaded"). Retry 429s up to
    # 3 attempts total, sleeping 15s then 30s (same backoff as the
    # judge). Latency includes the waits, so a retried success
    # honestly reports its total time. Non-429 failures return at
    # once; only 429 is retried.
    for attempt in range(3):
        try:
            resp = _session().post(
                f"{NVIDIA_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "max_tokens": max_tokens if max_tokens is not None else 4096,
                },
                timeout=call_timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            choice = data["choices"][0]
            response = _extract_message_text(choice.get("message", {}))
            # finish_reason == 'length' means the provider cut the
            # answer at the token cap. That is a cap failure, not
            # a model failure: flag it (the evaluator appends
            # 'truncated_at_cap' to error_type) and still score
            # the code as returned, instead of silently scoring
            # truncated code as a wrong answer.
            truncated = choice.get("finish_reason") == "length"
            # TP-capture metadata (2026-11-02): record the finish
            # reason and usage exactly as supplied; absent stays
            # absent (see the ProviderResult field comment).
            finish_reason = choice.get("finish_reason")
            usage_raw = data.get("usage")
            usage = usage_raw if isinstance(usage_raw, dict) else None
            latency_ms = int((time.time() - start) * 1000)
            return ProviderResult(
                response=response, success=True, latency_ms=latency_ms,
                error_type=None, truncated=truncated,
                finish_reason=finish_reason, usage=usage,
            )
        except requests.exceptions.ConnectionError:
            latency_ms = int((time.time() - start) * 1000)
            return ProviderResult(
                response="", success=False, latency_ms=latency_ms, error_type="connection_error"
            )
        except requests.exceptions.HTTPError as e:
            if _http_status(e) in (429, 502, 503) and not _is_daily_quota(e) \
                    and attempt < 2:
                time.sleep(15 * (attempt + 1))
                continue
            latency_ms = int((time.time() - start) * 1000)
            return ProviderResult(
                response="", success=False, latency_ms=latency_ms, error_type=_http_error_type(e)
            )
        except Exception as e:
            latency_ms = int((time.time() - start) * 1000)
            return ProviderResult(
                response="", success=False, latency_ms=latency_ms, error_type=f"error: {type(e).__name__}"
            )
    # Unreachable: every path above returns or continues, but keep a
    # fallback so a loop exit can never return None.
    latency_ms = int((time.time() - start) * 1000)
    return ProviderResult(
        response="", success=False, latency_ms=latency_ms, error_type="error: retry_exhausted"
    )
