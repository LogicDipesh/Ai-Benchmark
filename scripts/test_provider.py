from aibenchmark.providers import PROVIDERS
import time

for name in ['openrouter', 'huggingface', 'nvidia']:
    print(f'Testing {name}...')
    info = PROVIDERS[name]
    for model in info['models']:
        module = info['module']
        start = time.time()
        result = module.run_prompt(model, 'Say hello')
        elapsed = int((time.time() - start) * 1000)
        print(f'  {model}: Success={result.success}, Latency={elapsed}ms (reported: {result.latency_ms}ms), Error={result.error_type}')
        if result.success:
            print(f'    Response: {result.response[:50]}')