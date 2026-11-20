from aibenchmark.categories.coding import evaluate_coding, list_coding_problems
from aibenchmark.categories.debugging import evaluate_debugging, list_debugging_problems
from aibenchmark.categories.testing import evaluate_testing, list_testing_problems
from aibenchmark.providers import PROVIDERS

# Test with Ollama and Groq only
print('=== SMOKE RUN: Ollama + Groq, 1 problem per category ===')

coding_problems = list_coding_problems()[:1]
debugging_problems = list_debugging_problems()[:1]
testing_problems = list_testing_problems()[:1]

for name in ['ollama', 'groq']:
    for model in PROVIDERS[name]['models']:
        print(f'\n--- {name} / {model} ---')
        
        if coding_problems:
            result = evaluate_coding(coding_problems[0], name, model)
            print(f'  coding: score={result["score"]}, status={result["status"]}, error={result["error_type"]}, latency={result["latency_ms"]}ms')
        
        if debugging_problems:
            result = evaluate_debugging(debugging_problems[0], name, model)
            print(f'  debugging: score={result["score"]}, status={result["status"]}, error={result["error_type"]}, latency={result["latency_ms"]}ms')
        
        if testing_problems:
            result = evaluate_testing(testing_problems[0], name, model)
            print(f'  testing: score={result["score"]}, status={result["status"]}, error={result["error_type"]}, latency={result["latency_ms"]}ms')

print('\n=== Smoke run complete ===')