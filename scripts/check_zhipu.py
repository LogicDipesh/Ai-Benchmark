"""Direct-call test for the new Zhipu (Z.ai) GLM provider only.
Saves in the project root, runs, then delete or move to scripts/.
Prints only status + first 300 chars of the body, never the key.
Stops early if ZAI_API_KEY is not set in this window, so a missing key
cannot produce a misleading 401.
"""
import os
import requests

key = os.environ.get("ZAI_API_KEY")
print("zhipu key set:", bool(key))
if not key:
    raise SystemExit(1)

try:
    r = requests.post(
        "https://api.z.ai/api/paas/v4/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": "glm-4.7-flash",
            "messages": [{"role": "user", "content": "Say hi"}],
            "stream": False,
            "thinking": {"type": "disabled"},
        },
        timeout=120,
    )
    print("zhipu", r.status_code, r.text[:300])
except Exception as e:
    print("zhipu EXCEPTION", type(e).__name__, str(e)[:300])
