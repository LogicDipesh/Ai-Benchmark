from aibenchmark.categories.testing import evaluate_testing, list_testing_problems
from aibenchmark.categories.thinking_planning import evaluate_thinking_planning, list_thinking_planning_problems
from aibenchmark.providers import PROVIDERS

problems_testing = list_testing_problems()
problems_thinking = list_thinking_planning_problems()

print('=== OLLAMA TESTING ===')
for p in problems_testing:
    result = evaluate_testing(p, 'ollama', 'hhao/qwen2.5-coder-tools:3b')
    print(p['id'] + ': score=' + str(result['score']) + ', status=' + result['status'] + ', error_type=' + str(result['error_type']))

print()
print('=== OLLAMA THINKING-PLANNING ===')
for p in problems_thinking:
    result = evaluate_thinking_planning(p, 'ollama', 'hhao/qwen2.5-coder-tools:3b')
    print(p['id'] + ': score=' + str(result['score']) + ', status=' + result['status'] + ', error_type=' + str(result['error_type']))