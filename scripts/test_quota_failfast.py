"""test_quota_failfast.py — regression tests for provider quota fail-fast.

Runs OFFLINE: no API calls, no real keys, no database writes. The HTTP
layer and the retry sleeps are mocked; the provider code under test is
the real code (aibenchmark.providers.*), imported from the project.

Run from the project root:
  python test_quota_failfast.py

What it proves (doc: "test the quota fail-fast behavior without
contacting OpenRouter"):
  1. A 429 carrying a daily-quota marker is classified as quota
     exhaustion and returns immediately (1 attempt, no sleep).
  2. A transient 429 (no daily marker) follows the retry policy
     (3 attempts, sleeps mocked away) — status alone does not fail fast.
  3. A 503 is still retried (existing retryable set).
  4. The failure is recorded as an HTTP error with the quota message
     in error_type, with truncated=False — it is NOT misclassified as
     model output or as truncation.
  5. The truncation flag still works on the success path and depends
     on finish_reason alone (length -> True, stop -> False).

Coverage note: matcher units run for all five providers (the matcher
is duplicated per provider file); the full run_prompt path is tested
for OpenRouter, the quota owner. Zhipu's transient 1305 body is
covered as a matcher unit (must NOT match) plus an OpenRouter
transient case through the full path.
"""

import os
import sys
import time

import requests

PROVIDERS = ["openrouter", "groq", "nvidia", "zhipu", "ollama"]

DAILY_BODY = (
    '{"error": {"message": "Rate limit exceeded: free-models-per-day. '
    "Add 10 credits to unlock 1000 free model requests per day\", "
    '"code": 429}}'
)
DAILY_BODY_PER_DAY = '{"error": {"message": "Rate limit reached for requests per day"}}'
TRANSIENT_1305_BODY = (
    '{"error": {"message": "service may be temporarily overloaded", '
    '"code": 1305}}'
)
GENERIC_429_BODY = '{"error": {"message": "Rate limit exceeded. Try again later."}}'

FAILURES = []


def check(name, condition, detail=""):
    if condition:
        print(f"  PASS: {name}")
    else:
        print(f"  FAIL: {name} {detail}")
        FAILURES.append(name)


def make_http_error(status, body):
    resp = requests.Response()
    resp.status_code = status
    resp._content = body.encode("utf-8")
    return requests.exceptions.HTTPError(response=resp)


class FakeSession:
    """Session whose post() pops scripted outcomes (exception or response)."""

    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.posts = 0

    def post(self, *args, **kwargs):
        self.posts += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class FakeSuccessResponse:
    def __init__(self, finish_reason):
        self._payload = {
            "choices": [{
                "finish_reason": finish_reason,
                "message": {"role": "assistant", "content": "```python\nx = 1\n```"},
            }]
        }

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_matchers():
    print("== matcher units (all five providers) ==")
    import importlib
    for provider in PROVIDERS:
        mod = importlib.import_module(f"aibenchmark.providers.{provider}")
        fn = mod._is_daily_quota
        check(f"{provider}: free-models-per-day matches",
              fn(make_http_error(429, DAILY_BODY)) is True)
        check(f"{provider}: 'requests per day' matches",
              fn(make_http_error(429, DAILY_BODY_PER_DAY)) is True)
        check(f"{provider}: transient 1305 does not match",
              fn(make_http_error(429, TRANSIENT_1305_BODY)) is False)
        check(f"{provider}: generic 429 does not match",
              fn(make_http_error(429, GENERIC_429_BODY)) is False)
        check(f"{provider}: empty body does not match",
              fn(make_http_error(429, "")) is False)
        no_resp = requests.exceptions.HTTPError()
        check(f"{provider}: no response object does not match",
              fn(no_resp) is False)


def run_openrouter_path(name, outcomes, expect_posts, expect_sleeps,
                        expect_success, expect_truncated,
                        expect_error_substr=None):
    import aibenchmark.providers.openrouter as mod

    fake = FakeSession(outcomes)
    sleeps = []
    real_session = mod._session
    real_sleep = time.sleep
    mod._session = lambda: fake
    time.sleep = lambda s: sleeps.append(s)
    os.environ[mod.OPENROUTER_API_KEY_ENV] = "test-key"
    try:
        result = mod.run_prompt("cohere/north-mini-code:free", "test prompt",
                                max_tokens=8192)
    finally:
        mod._session = real_session
        time.sleep = real_sleep
    check(f"{name}: posts == {expect_posts}", fake.posts == expect_posts,
          f"(got {fake.posts})")
    check(f"{name}: sleeps == {expect_sleeps}", sleeps == expect_sleeps,
          f"(got {sleeps})")
    check(f"{name}: success == {expect_success}",
          result.success is expect_success)
    check(f"{name}: truncated == {expect_truncated}",
          result.truncated is expect_truncated)
    if expect_error_substr is not None:
        check(f"{name}: error_type contains {expect_error_substr!r}",
              result.error_type is not None
              and expect_error_substr in result.error_type,
              f"(got {result.error_type!r})")


def test_openrouter_paths():
    print("== full run_prompt path (openrouter) ==")
    run_openrouter_path(
        "daily quota fails fast",
        [make_http_error(429, DAILY_BODY)],
        expect_posts=1, expect_sleeps=[], expect_success=False,
        expect_truncated=False, expect_error_substr="free-models-per-day")
    run_openrouter_path(
        "transient 429 retries 3 attempts",
        [make_http_error(429, TRANSIENT_1305_BODY)] * 3,
        expect_posts=3, expect_sleeps=[15, 30], expect_success=False,
        expect_truncated=False, expect_error_substr="1305")
    run_openrouter_path(
        "generic 429 (no marker) retries, status alone does not fail fast",
        [make_http_error(429, GENERIC_429_BODY)] * 3,
        expect_posts=3, expect_sleeps=[15, 30], expect_success=False,
        expect_truncated=False)
    run_openrouter_path(
        "503 retries 3 attempts",
        [make_http_error(503, '{"error": "Service Unavailable"}')] * 3,
        expect_posts=3, expect_sleeps=[15, 30], expect_success=False,
        expect_truncated=False)
    run_openrouter_path(
        "success with finish_reason length sets truncated",
        [FakeSuccessResponse("length")],
        expect_posts=1, expect_sleeps=[], expect_success=True,
        expect_truncated=True)
    run_openrouter_path(
        "success with finish_reason stop clears truncated",
        [FakeSuccessResponse("stop")],
        expect_posts=1, expect_sleeps=[], expect_success=True,
        expect_truncated=False)


def main():
    test_matchers()
    test_openrouter_paths()
    print()
    if FAILURES:
        print(f"FAIL: {len(FAILURES)} check(s) failed: {FAILURES}")
        return 1
    print("PASS: all quota fail-fast checks passed (offline, no API calls)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
