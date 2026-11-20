import os
import json
import time
import requests

# Check if OPENROUTER_API_KEY is set
api_key = os.environ.get("OPENROUTER_API_KEY")
print(f'OPENROUTER_API_KEY set: {bool(api_key)}')

if not api_key:
    print('BLOCKED: OPENROUTER_API_KEY not set - judge cannot run')
else:
    JUDGE_MODEL = "google/gemini-2.0-flash:free"
    
    def judge_response(response: str, rubric: str) -> float:
        judge_prompt = f"""You are an expert evaluator. Score the following response on a scale of 0.0 to 1.0 based on this rubric:

{rubric}

Response to evaluate:
{response}

Return ONLY a JSON object with a single key "score" containing a float between 0.0 and 1.0. No other text."""

        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": JUDGE_MODEL,
                    "messages": [{"role": "user", "content": judge_prompt}],
                    "stream": False,
                },
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            judge_text = data["choices"][0]["message"]["content"]
            
            result = json.loads(judge_text.strip())
            score = float(result.get("score", 0.0))
            return max(0.0, min(1.0, score))
        except Exception as e:
            return f"ERROR: {type(e).__name__}: {e}"

    rubric = """
Score 1.0 if the response addresses all points with specific, technically sound reasoning.
Score 0.5 if some points addressed but with gaps.
Score 0.0 if incoherent or ignores prompt.
"""

    # Test 1: Good answer
    print('Test 1: Good answer')
    good = """I would use a write-through cache with Redis. For invalidation, use TTL + explicit invalidation on writes. For stampedes, use mutex locks. For node failure, use Redis Sentinel. Monitor hit rate, latency, error rates."""
    score = judge_response(good, rubric)
    print(f'Good answer score: {score}')

    # Test 2: Bad answer
    print('\nTest 2: Bad answer')
    bad = "I don't know."
    score = judge_response(bad, rubric)
    print(f'Bad answer score: {score}')

    # Test 3: Variance check (run 3 times)
    print('\nTest 3: Variance (3 runs on good answer)')
    scores = []
    for i in range(3):
        s = judge_response(good, rubric)
        scores.append(s)
        print(f'  Run {i+1}: {s}')
        time.sleep(1)
    print(f'Variance: {max(scores) - min(scores):.3f}')

    # Test 4: Judge unreachable simulation (would need network manipulation)
    print('\nTest 4: Judge unreachable - would need network block, skipping')