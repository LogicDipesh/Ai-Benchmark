import os, requests

tests = [
    ("openrouter", "https://openrouter.ai/api/v1/chat/completions", "OPENROUTER_API_KEY", "cohere/north-mini-code:free"),
    ("openrouter-judge", "https://openrouter.ai/api/v1/chat/completions", "OPENROUTER_API_KEY", "google/gemma-4-31b-it:free"),
    ("nvidia", "https://integrate.api.nvidia.com/v1/chat/completions", "NVIDIA_API_KEY", "nvidia/nemotron-3-ultra-550b-a55b"),
    ("huggingface", "https://router.huggingface.co/v1/chat/completions", "HF_API_KEY", "meta-llama/Llama-3.3-70B-Instruct"),
    ("groq", "https://api.groq.com/openai/v1/chat/completions", "GROQ_API_KEY", "openai/gpt-oss-120b"),
]

for name, url, env, model in tests:
    key = os.environ.get(env)
    print(name, "key set:", bool(key))
    if not key:
        continue
    try:
        r = requests.post(url, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": "Say hi"}], "stream": False}, timeout=120)
        print(name, r.status_code, r.text[:300])
    except Exception as e:
        print(name, "EXCEPTION", type(e).__name__, str(e)[:300])
