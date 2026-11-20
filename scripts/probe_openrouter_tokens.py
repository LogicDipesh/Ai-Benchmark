"""probe_openrouter_tokens.py — OpenRouter token-accounting probe.

Purpose: reconcile the run-26 coding_001 anomaly (stored response of
only three lines, yet the truncated_at_cap flag fired at the 8192
token cap) by recording, for a FRESH coding_001 call, the metadata
the benchmark itself does not store:

  1. provider finish_reason
  2. prompt and completion token counts (usage)
  3. raw response content length
  4. stored response length (what the bench would store)
  5. truncation flag before and after extraction
  6. HTTP status and selected response headers (quota headers included)
  7. UTC timestamps (call start/end, for quota-reset correlation)
  8. the full raw response content, plus a JSON record file with
     everything above (so one successful call is enough evidence)

v1.1 changes: response headers, UTC timestamps, "unavailable" labels
for missing metadata (never inferred), full raw content printed, and
a probe_output_<UTC stamp>.json record file. No API keys or
authorization headers are ever printed or saved.

What it does NOT do: it does not modify any benchmark code, does not
write to history.db, does not run any evaluation or scoring, and does
not create a run. It burns exactly ONE OpenRouter free-model call.

Usage (from the project root, E:\\AI-Benchmark):
  python probe_openrouter_tokens.py [artifact_path]

The artifact path defaults to the run-26 OpenRouter artifact
(failure_artifacts/coding_001_palindrome_linked_list__openrouter__20261030-174937.md).
The probe reads the EXACT prompt the bench sent from that artifact's
prompt section, so the call mirrors run 26's input.

Requirements: OPENROUTER_API_KEY set in the environment (it is never
printed), requests installed, and the artifact present.

Call parity with the bench's current settings: model from the
registry (fallback cohere/north-mini-code:free), max_tokens 8192,
and NO temperature field (provider defaults, as since the run-17
revert). Headers here are minimal (Authorization + Content-Type);
the bench may send additional referer/title headers, which do not
affect token accounting.

Scope limit, stated honestly: this probe measures the pipeline's
CURRENT behavior on a fresh generation. It can reveal a systematic
metadata or extraction bug, but it cannot retroactively prove what
happened in run 26's specific generation (output varies run to
run). If this probe comes back clean, run 26 stays a
single-occurrence note, not a systematic bug — and that is still a
useful answer.
"""

import ast
import json
import os
import re
import sys
import time
from datetime import datetime, timezone

DEFAULT_ARTIFACT = os.path.join(
    "failure_artifacts",
    "coding_001_palindrome_linked_list__openrouter__20261030-174937.md",
)
FALLBACK_MODEL = "cohere/north-mini-code:free"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_TOKENS = 8192

# Section keywords the failure artifacts use, in file order. The prompt
# section is found by its keyword; the section after it is whichever
# known keyword appears next, so a prompt that itself contains a
# "## " line cannot cut the extraction short.
SECTION_KEYWORDS = [
    "prompt",
    "raw model response",
    "executed code",
    "reference implementation",
    "test file content",
]


def extract_section(text, keyword):
    """Return the body of the section whose header contains `keyword`.

    The body runs until the next section header (a line starting with
    "## " whose text contains a known later keyword) or end of file.
    Returns None when the header is not found.
    """
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith("## ") and keyword.lower() in line.lower():
            start = i + 1
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start, len(lines)):
        line = lines[j]
        if line.startswith("## "):
            lowered = line.lower()
            if any(k in lowered for k in SECTION_KEYWORDS):
                end = j
                break
    return "\n".join(lines[start:end]).strip("\n")


def strip_outer_fence(body):
    """Remove one outer Markdown fence pair, if the body is fenced."""
    if body is None:
        return None
    lines = body.splitlines()
    if len(lines) >= 2 and lines[0].lstrip().startswith("```"):
        if lines[-1].strip() == "```":
            return "\n".join(lines[1:-1])
        # Unclosed fence: drop only the opening fence line.
        return "\n".join(lines[1:])
    return body


def one_line(text, limit=120):
    """Collapse whitespace and truncate for a preview line."""
    flat = re.sub(r"\s+", " ", text or "").strip()
    return flat if len(flat) <= limit else flat[:limit] + "..."


def fmt(value):
    """Missing metadata prints as 'unavailable', never inferred."""
    return "unavailable" if value is None else value


def format_reset_header(raw):
    """X-RateLimit-Reset may be ms or s epoch; render both raw and UTC."""
    if raw is None:
        return "unavailable"
    try:
        seconds = int(raw)
    except (TypeError, ValueError):
        return raw
    if seconds > 10 ** 12:  # milliseconds
        seconds = seconds / 1000
    try:
        utc = datetime.fromtimestamp(seconds, tz=timezone.utc)
        return f"{raw} (= {utc.strftime('%Y-%m-%d %H:%M:%S')} UTC)"
    except (OverflowError, OSError, ValueError):
        return raw


def get_model():
    """Model from the registry when importable, else the fallback."""
    try:
        from aibenchmark.providers import PROVIDERS

        models = PROVIDERS["openrouter"]["models"]
        assert len(models) == 1
        return models[0], "registry"
    except Exception as exc:  # registry unavailable; fallback is explicit
        print(f"note: registry unreadable ({exc}); using fallback model")
        return FALLBACK_MODEL, "fallback"


def bench_extract_message_text(message):
    """The bench's stored-response step, when its module imports."""
    try:
        from aibenchmark.providers.openrouter import _extract_message_text

        return _extract_message_text(message), "bench _extract_message_text"
    except Exception as exc:
        print(f"note: bench message extractor unavailable ({exc}); "
              "using raw content as the stored response")
        content = message.get("content")
        if isinstance(content, str):
            return content, "raw content (fallback)"
        if isinstance(content, list):
            joined = "".join(
                part.get("text", "") for part in content
                if isinstance(part, dict)
            )
            return joined, "raw content parts joined (fallback)"
        return "", "empty (fallback)"


def bench_extract_code(stored):
    """The bench's code extractor, when its module imports."""
    try:
        from aibenchmark.sandbox import extract_code

        return extract_code(stored), "bench extract_code"
    except Exception as exc:
        print(f"note: bench code extractor unavailable ({exc}); "
              "extraction checks skipped")
        return None, "unavailable"


def call_openrouter(model, prompt):
    """One direct OpenRouter call.

    Returns (status, latency_ms, payload, response_headers, started_utc,
    ended_utc). Only response headers are captured; request headers
    (which carry the Authorization bearer token) are never returned,
    printed, or saved.
    """
    import requests

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY is not set in this window.")
        print("Set it (User-scope persistent variable) and re-run; the key")
        print("is never printed by this script.")
        sys.exit(1)
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": MAX_TOKENS,
        # No temperature field: provider defaults, as the bench sends.
    }
    headers = {
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json",
    }
    started = time.time()
    started_utc = datetime.now(timezone.utc)
    try:
        resp = requests.post(
            OPENROUTER_URL, headers=headers, json=payload, timeout=300
        )
    except Exception as exc:
        print(f"ERROR: request failed: {type(exc).__name__}: {exc}")
        sys.exit(1)
    ended_utc = datetime.now(timezone.utc)
    latency_ms = int((time.time() - started) * 1000)
    if resp.status_code != 200:
        snippet = re.sub(r"\s+", " ", resp.text or "")[:500]
        print(f"ERROR: HTTP {resp.status_code}: {snippet}")
        sys.exit(1)
    return (resp.status_code, latency_ms, resp.json(),
            dict(getattr(resp, "headers", {}) or {}),
            started_utc, ended_utc)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    artifact_path = args[0] if args else DEFAULT_ARTIFACT
    if not os.path.isfile(artifact_path):
        print(f"ERROR: artifact not found: {artifact_path}")
        print("Run this script from the project root, where")
        print("failure_artifacts/ holds the run-26 artifacts.")
        return 1

    with open(artifact_path, encoding="utf-8") as f:
        artifact_text = f.read()

    prompt = strip_outer_fence(extract_section(artifact_text, "prompt"))
    if not prompt:
        print("ERROR: could not find the prompt section in the artifact.")
        return 1
    run26_raw = strip_outer_fence(
        extract_section(artifact_text, "raw model response")
    )

    print("=== probe setup ===")
    print(f"artifact: {artifact_path}")
    print(f"prompt length: {len(prompt)} chars")
    print(f"prompt first line: {one_line(prompt.splitlines()[0])}")
    print(f"prompt last line: {one_line(prompt.splitlines()[-1])}")
    if run26_raw is not None:
        print(f"run-26 stored raw response length: {len(run26_raw)} chars")
        print(f"run-26 stored raw response first line: "
              f"{one_line(run26_raw.splitlines()[0] if run26_raw else '')}")

    model, model_source = get_model()
    print(f"model: {model} (source: {model_source})")
    print(f"max_tokens: {MAX_TOKENS}; temperature: omitted (provider default)")
    print("calling OpenRouter (exactly one call)...")

    (status, latency_ms, data, resp_headers, started_utc,
     ended_utc) = call_openrouter(model, prompt)

    choices = data.get("choices") or []
    if not choices:
        print("ERROR: response has no choices; top-level keys: "
              f"{sorted(data.keys())}")
        return 1
    choice = choices[0]
    finish_reason = choice.get("finish_reason")
    message = choice.get("message") or {}
    raw_content = message.get("content")
    if isinstance(raw_content, str):
        raw_text = raw_content
        raw_kind = "string"
    elif isinstance(raw_content, list):
        raw_text = "".join(
            part.get("text", "") for part in raw_content
            if isinstance(part, dict)
        )
        raw_kind = "content-parts list (joined)"
    else:
        raw_text = ""
        raw_kind = "none (tool-call-only reply?)"
    tool_calls = message.get("tool_calls")
    usage = data.get("usage") or {}

    stored, stored_method = bench_extract_message_text(message)
    executed, executed_method = bench_extract_code(stored)

    truncated_before = finish_reason == "length"
    fence_left = executed.startswith("```") if executed is not None else None
    parse_error = None
    if executed is not None:
        try:
            ast.parse(executed)
        except SyntaxError as exc:
            parse_error = f"{exc.msg} (line {exc.lineno})"
    has_function = (
        "def is_palindrome" in executed if executed is not None else None
    )

    print()
    print("=== probe results (fresh generation) ===")
    print(f"http status: {status}")
    print(f"call started (UTC): {started_utc.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"call ended (UTC): {ended_utc.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"latency: {latency_ms} ms")
    print(f"response id: {fmt(data.get('id'))}")
    print(f"model returned: {fmt(data.get('model'))}")
    print("response headers (selected; no authorization data):")
    for header in ("x-ratelimit-limit", "x-ratelimit-remaining",
                   "x-ratelimit-reset", "date", "content-type"):
        value = None
        for key, val in resp_headers.items():
            if key.lower() == header:
                value = val
                break
        if header == "x-ratelimit-reset":
            value = format_reset_header(value)
        print(f"   {header}: {fmt(value)}")
    print(f"1. finish_reason: {fmt(finish_reason)}")
    print(f"2. usage prompt_tokens: {fmt(usage.get('prompt_tokens'))}")
    print(f"   usage completion_tokens: {fmt(usage.get('completion_tokens'))}")
    print(f"   usage total_tokens: {fmt(usage.get('total_tokens'))}")
    print(f"3. raw content length: {len(raw_text)} chars ({raw_kind})")
    print(f"   tool_calls present: {bool(tool_calls)}")
    print(f"4. stored response length: {len(stored)} chars "
          f"(method: {stored_method})")
    print(f"   stored == raw: {stored == raw_text}")
    print(f"5. truncated flag before extraction "
          f"(finish_reason == 'length'): {truncated_before}")
    if executed is not None:
        print(f"   extracted code length: {len(executed)} chars "
              f"(method: {executed_method})")
        print(f"   extracted code starts with fence marker: {fence_left}")
        print(f"   extracted code parses: {parse_error is None}"
              + (f" (SyntaxError: {parse_error})" if parse_error else ""))
        print(f"   extracted code contains 'def is_palindrome': "
              f"{has_function}")
    else:
        print("   extraction checks skipped (bench extractor unavailable)")
    print()
    print("=== full raw response content (exactly as returned) ===")
    print(raw_text)
    print("=== end of raw response content ===")

    record = {
        "timestamp_utc": started_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "artifact": artifact_path,
        "prompt_length_chars": len(prompt),
        "model_requested": model,
        "model_requested_source": model_source,
        "max_tokens_requested": MAX_TOKENS,
        "temperature": "omitted (provider default)",
        "http_status": status,
        "call_started_utc": started_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "call_ended_utc": ended_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "latency_ms": latency_ms,
        "response_id": data.get("id"),
        "model_returned": data.get("model"),
        "response_headers_selected": {
            k: v for k, v in resp_headers.items()
            if k.lower() in ("x-ratelimit-limit", "x-ratelimit-remaining",
                             "x-ratelimit-reset", "date", "content-type")
        },
        "finish_reason": finish_reason,
        "usage": usage,
        "raw_content": raw_text,
        "raw_content_length_chars": len(raw_text),
        "raw_content_kind": raw_kind,
        "tool_calls_present": bool(tool_calls),
        "stored_response": stored,
        "stored_response_length_chars": len(stored),
        "stored_response_method": stored_method,
        "stored_equals_raw": stored == raw_text,
        "truncated_before_extraction": truncated_before,
        "extracted_code": executed,
        "extracted_code_length_chars": len(executed) if executed else None,
        "extracted_code_method": executed_method,
        "extracted_starts_with_fence": fence_left,
        "extracted_parses": parse_error is None if executed else None,
        "extracted_parse_error": parse_error,
        "extracted_contains_is_palindrome": has_function,
        "run26_stored_raw_length_chars": len(run26_raw) if run26_raw else None,
    }
    record_name = ("probe_output_"
                   + started_utc.strftime("%Y%m%d-%H%M%S") + ".json")
    with open(record_name, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
    print(f"full record saved to: {record_name}")

    print()
    print("=== how to read this ===")
    print("- finish_reason=length with completion_tokens near 8192 and a")
    print("  long raw response: the model genuinely filled the cap this")
    print("  time; run 26's short stored response is then NOT explained")
    print("  by this probe and stays a single-occurrence note.")
    print("- finish_reason=length with completion_tokens far below 8192")
    print("  and a short raw response: provider-side accounting quirk")
    print("  reproduced — the flag fires without near-cap usage.")
    print("- finish_reason=stop with complete, parsing code: clean")
    print("  generation this time; run 26 stays a single-occurrence note.")
    print("- stored length far below raw length: content was dropped in")
    print("  the bench's message-extraction step (content-parts or")
    print("  tool-call path) — an extraction-side drop, identified here.")
    print("- extracted code starts with a fence marker: the unclosed-fence")
    print("  fallback reproduced live (secondary issue, already known).")
    print()
    print("This probe wrote nothing to history.db and changed no bench code.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
