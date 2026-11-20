"""Check ALL current AI-Benchmark providers in one run (2026-10-27).

Current registry (after HF removal + GLM addition):
  ollama, openrouter, nvidia, groq, zhipu
Plus the thinking-planning judge (OpenRouter, gemma) — doctor does NOT
check the judge, so it is tested here explicitly.

Hugging Face is intentionally ABSENT: removed 2026-10-27 because its
Inference Providers require paid credits/PRO (402), violating the
free-tier-only scheme.

Save in the project root (E:\\AI-Benchmark), run, then delete or move
to scripts/. Prints only status + first 300 chars of each body, never
any API key. A provider whose key is missing in this window is SKIPPED,
not tested — a missing key must never produce a misleading 401.
Ollama is checked via /api/tags only (no generation call: a CPU
generation test would take minutes on this machine).
"""
import os
import requests

RESULTS = []


def _report(name, status):
    RESULTS.append((name, status))
    print(f"{name}: {status}")


def test_chat(name, url, env, model, extra=None):
    key = os.environ.get(env)
    print(f"{name} key set: {bool(key)}")
    if not key:
        _report(name, "SKIPPED (key not set in this window)")
        return
    try:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Say hi"}],
            "stream": False,
        }
        if extra:
            payload.update(extra)
        r = requests.post(
            url,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json=payload,
            timeout=120,
        )
        print(f"{name} {r.status_code} {r.text[:300]}")
        _report(name, f"{r.status_code} {'OK' if r.status_code == 200 else 'FAILED'}")
    except Exception as e:
        print(f"{name} EXCEPTION {type(e).__name__} {str(e)[:300]}")
        _report(name, f"EXCEPTION {type(e).__name__}")


def test_ollama():
    model = "hhao/qwen2.5-coder-tools:3b"
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=10)
        if r.status_code != 200:
            print(f"ollama HTTP {r.status_code}")
            _report("ollama", f"FAILED HTTP {r.status_code}")
            return
        models = [m["name"] for m in r.json().get("models", [])]
        if model in models:
            print(f"ollama OK model found: {model}")
            _report("ollama", "OK (model found)")
        else:
            print(f"ollama model NOT found. Available: {models}")
            _report("ollama", "FAILED (model not found)")
    except Exception as e:
        print(f"ollama not reachable: {type(e).__name__} {str(e)[:200]}")
        _report("ollama", "FAILED (not running)")


test_ollama()
test_chat(
    "openrouter",
    "https://openrouter.ai/api/v1/chat/completions",
    "OPENROUTER_API_KEY",
    "cohere/north-mini-code:free",
)
test_chat(
    "openrouter-judge",
    "https://openrouter.ai/api/v1/chat/completions",
    "OPENROUTER_API_KEY",
    "google/gemma-4-31b-it:free",
)
test_chat(
    "nvidia",
    "https://integrate.api.nvidia.com/v1/chat/completions",
    "NVIDIA_API_KEY",
    "nvidia/nemotron-3-ultra-550b-a55b",
)
test_chat(
    "groq",
    "https://api.groq.com/openai/v1/chat/completions",
    "GROQ_API_KEY",
    "openai/gpt-oss-120b",
)
test_chat(
    "zhipu",
    "https://api.z.ai/api/paas/v4/chat/completions",
    "ZAI_API_KEY",
    "glm-4.7-flash",
    extra={"thinking": {"type": "disabled"}},
)

print("\nSummary:")
for name, status in RESULTS:
    print(f"  {name:<16} {status}")
