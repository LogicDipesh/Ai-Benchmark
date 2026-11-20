from aibenchmark.providers import PROVIDERS
import os

print('=== FAILURE INJECTION TESTS ===')

# 1. Invalid API key
print('\n1. Invalid API key (Groq)')
os.environ['GROQ_API_KEY'] = 'invalid-key'
module = PROVIDERS['groq']['module']
result = module.run_prompt('openai/gpt-oss-120b', 'test')
print(f'  Success: {result.success}, Error: {result.error_type}')
os.environ['GROQ_API_KEY'] = ''  # restore

# 2. Unreachable Ollama (wrong port)
print('\n2. Unreachable Ollama')
import aibenchmark.providers.ollama as ollama_module
original_host = ollama_module.OLLAMA_HOST
ollama_module.OLLAMA_HOST = "http://localhost:9999"
result = ollama_module.run_prompt('hhao/qwen2.5-coder-tools:3b', 'test')
print(f'  Success: {result.success}, Error: {result.error_type}')
ollama_module.OLLAMA_HOST = original_host

# 3. Very short timeout (via provider - not easily testable without code change)
# Would need to modify provider to use shorter timeout
print('\n3. Short timeout - not testable without code change (provider has 300s timeout)')

# 4. Model returning garbage (non-code)
print('\n4. Model returning garbage (Ollama)')
# We can't easily test this without mocking the provider response
# But we can test extract_code with garbage
from aibenchmark.sandbox import extract_code
garbage = "This is not code at all, just random text"
extracted = extract_code(garbage)
print(f'  Garbage input extracted as: {repr(extracted)}')

# 5. Test with missing API key for Groq
print('\n5. Groq with missing API key (temporarily unset)')
saved_key = os.environ.get('GROQ_API_KEY', '')
os.environ['GROQ_API_KEY'] = ''
result = PROVIDERS['groq']['module'].run_prompt('openai/gpt-oss-120b', 'test')
print(f'  Success: {result.success}, Error: {result.error_type}')
os.environ['GROQ_API_KEY'] = saved_key

print('\n=== Failure injection tests complete ===')