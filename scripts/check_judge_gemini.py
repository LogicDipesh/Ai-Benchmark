"""Direct-call test for the NEW direct-Gemini judge only.
Saves in the project root, runs, then delete or move to scripts/.
Prints only status + first 300 chars of the body, never the key.
Stops early if GEMINI_API_KEY is not set in this window.
Sends a real judge-style prompt (rubric + sample plan) and parses the
score exactly like judge_response does, so a 200 here means the bench
judge path works, not just that the endpoint answers.
"""
import os
import json
import requests

key = os.environ.get("GEMINI_API_KEY")
print("gemini judge key set:", bool(key))
if not key:
    raise SystemExit(1)

judge_prompt = """You are an expert evaluator. Score the following response on a scale of 0.0 to 1.0 based on this rubric:

The plan must list steps in order and name the data structure used.

Response to evaluate:
1. Create an empty list. 2. Append items in order. 3. Return the list.

Return ONLY a JSON object with a single key "score" containing a float between 0.0 and 1.0. No other text."""

try:
    r = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": "gemini-2.5-flash",
            "messages": [{"role": "user", "content": judge_prompt}],
            "stream": False,
        },
        timeout=120,
    )
    print("gemini-judge", r.status_code, r.text[:300])
    if r.status_code == 200:
        text = r.json()["choices"][0]["message"]["content"].strip()
        if text.startswith("```"):
            text = text.strip("`").strip()
            if text.lower().startswith("json"):
                text = text[4:].strip()
        print("parsed score:", json.loads(text).get("score"))
except Exception as e:
    print("gemini-judge EXCEPTION", type(e).__name__, str(e)[:300])
