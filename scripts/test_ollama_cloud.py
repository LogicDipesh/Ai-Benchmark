"""Test the ollama slot's cloud model through the bench's OWN provider
code, before any full run. Run AFTER copying the new providers/
__init__.py into place, and AFTER `ollama signin` (+ pull if the
model is not already listed).

v2 NOTE: the v1 pick, qwen3-coder:480b-cloud, is RETIRED (live API
410, 2026-10-30). The v2 pick, gemma4:31b-cloud, is the model
Ollama's own error message recommended, and it was already in this
machine's /api/tags list.

Burns exactly ONE small cloud call (max_tokens=256, so minimal
tokens and minimal cost). Reads the model name from the registry, so
it tests exactly what `bench run` will use — if the tag is wrong,
this fails here, not halfway through a run.

Run from the project root (E:\\AI-Benchmark), then delete or move
to scripts/. No keys involved: cloud auth is the machine's Ollama
sign-in, not a key in code, so nothing secret is printed.

If it fails:
  - connection_error  -> Ollama is not running; start the Ollama app
  - HTTPError 401     -> not signed in; run `ollama signin` (browser
                         flow, one-time), then re-run this script
  - HTTPError 404     -> model not pulled, or the tag changed; run
                         `ollama pull gemma4:31b-cloud`, or check
                         the cloud models list at ollama.com and
                         correct the one model string in providers/
                         __init__.py
  - HTTPError 410     -> the model was retired (this is how v1
                         died); pick the replacement Ollama's message
                         recommends, or another live cloud tag
  - HTTPError 429     -> cloud quota/credits; check the usage page
                         in your Ollama account
Do NOT start a full bench run on a failing test.
"""
from aibenchmark.providers import PROVIDERS, ollama

MODEL = PROVIDERS["ollama"]["models"][0]
print(f"Ollama slot model (from registry): {MODEL}")

listed = ollama.list_models()
print(f"Models in /api/tags: {listed}")
print(f"Registry model listed locally: {MODEL in listed} "
      f"(informational only — the real test is the call below)")

PROMPT = ("Write a Python function add(a, b) that returns a + b. "
          "Return only code, no prose.")
result = ollama.run_prompt(MODEL, PROMPT, max_tokens=256, timeout=120)

print(f"Success: {result.success}")
print(f"Latency: {result.latency_ms} ms")
print(f"Truncated: {getattr(result, 'truncated', None)}")
if result.success:
    print("Ollama cloud OK — reply preview:")
    print(result.response[:200])
else:
    print(f"Ollama cloud FAILED — error: {result.error_type}")
    print("See the failure guide at the top of this script.")
