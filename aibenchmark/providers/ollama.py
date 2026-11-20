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


OLLAMA_HOST = "http://localhost:11434"


def list_models() -> list[str]:
    try:
        resp = _session().get(f"{OLLAMA_HOST}/api/tags", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


def _http_error_type(e: requests.exceptions.HTTPError) -> str:
    """Format an HTTP failure with status + body snippet, not just the
    exception class name. Body is whitespace-collapsed and truncated
    to 500 chars; it is an error message from the provider, never a
    key (keys are only ever sent in request headers, never echoed in
    error bodies)."""
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
    start = time.time()
    call_timeout = timeout if timeout is not None else 300
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
                f"{OLLAMA_HOST}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False,
                "options": {"num_predict": max_tokens if max_tokens is not None else 2048}},
                timeout=call_timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            response = data.get("response") or ""
            if not isinstance(response, str):
                response = ""
            # Ollama's done_reason mirrors finish_reason: 'length'
            # means the answer was cut at num_predict (see the
            # cloud providers' comment for why this is flagged,
            # not auto-zeroed).
            truncated = data.get("done_reason") == "length"
            # TP-capture metadata (2026-11-02): done_reason mirrors
            # finish_reason. Ollama's generate API returns no OpenAI
            # usage object; its eval counts are recorded under the
            # token keys when supplied, and total_tokens is never
            # summed (absent stays absent).
            finish_reason = data.get("done_reason")
            usage = {}
            if isinstance(data.get("prompt_eval_count"), int):
                usage["prompt_tokens"] = data["prompt_eval_count"]
            if isinstance(data.get("eval_count"), int):
                usage["completion_tokens"] = data["eval_count"]
            if not usage:
                usage = None
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
    latency_ms = int((time.time() - start) * 1000)
    return ProviderResult(
        response="", success=False, latency_ms=latency_ms, error_type="error: retry_exhausted"
    )
