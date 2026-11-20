import os, requests

models = [
    "google/gemma-4-31b-it:free",
    "cohere/north-mini-code:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "openrouter/free",
]

key = os.environ.get("OPENROUTER_API_KEY")
print("key set:", bool(key))
if not key:
    print("No key reached Python, stopping before any API call.")
    raise SystemExit(1)

for model in models:
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": "Say hi"}], "stream": False}, timeout=120)
        print(model, r.status_code, r.text[:300])
    except Exception as e:
        print(model, "EXCEPTION", type(e).__name__, str(e)[:300])
