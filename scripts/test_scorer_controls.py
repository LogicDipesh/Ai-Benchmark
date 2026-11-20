from aibenchmark.sandbox import run_tests_sandboxed, run_mutant_tests_sandboxed, extract_code

print('=== Scorer Control Tests ===')

# Test 1: run_tests_sandboxed with correct code
print('\n1. run_tests_sandboxed - known correct code')
code = '''
def reverse_words(s):
    if not s:
        return ""
    words = s.split()
    return " ".join(reversed(words))
'''
score, status, error = run_tests_sandboxed('problems/coding', code, 'problems/coding/test_coding_001.py')
print(f'  Score: {score}, Status: {status}, Error: {error}')
assert score == 1.0, f"Expected 1.0, got {score}"

# Test 2: run_tests_sandboxed with incorrect code
print('\n2. run_tests_sandboxed - known wrong code')
code = '''
def reverse_words(s):
    return s
'''
score, status, error = run_tests_sandboxed('problems/coding', code, 'problems/coding/test_coding_001.py')
print(f'  Score: {score}, Status: {status}, Error: {error}')
assert score == 0.0, f"Expected 0.0, got {score}"

# Test 3: run_tests_sandboxed with malformed/empty
print('\n3. run_tests_sandboxed - empty code')
code = ''
score, status, error = run_tests_sandboxed('problems/coding', code, 'problems/coding/test_coding_001.py')
print(f'  Score: {score}, Status: {status}, Error: {error}')
assert score == 0.0

# Test 4: run_tests_sandboxed with markdown fences and prose
print('\n4. run_tests_sandboxed - code in markdown')
code = '''
Here is my solution:
```python
def reverse_words(s):
    if not s:
        return ""
    words = s.split()
    return " ".join(reversed(words))
```
'''
from aibenchmark.sandbox import extract_code
extracted = extract_code(code)
print(f'  Extracted: {extracted[:50]}')
score, status, error = run_tests_sandboxed('problems/coding', extracted, 'problems/coding/test_coding_001.py')
print(f'  Score: {score}, Status: {status}, Error: {error}')
assert score == 1.0, f"Expected 1.0, got {score}"

# Test 5: run_mutant_tests_sandboxed - correct test code
print('\n5. run_mutant_tests_sandboxed - correct test code')
test_code = '''
import pytest
from solution import is_valid

def test_empty():
    assert is_valid("") == True

def test_simple():
    assert is_valid("()") == True
    assert is_valid("()[]{}") == True

def test_invalid():
    assert is_valid("(]") == False
'''
ref_impl = '''
def is_valid(s):
    stack = []
    mapping = {')': '(', '}': '{', ']': '['}
    for char in s:
        if char in mapping.values():
            stack.append(char)
        elif char in mapping.keys():
            if not stack or stack.pop() != mapping[char]:
                return False
        else:
            return False
    return not stack
'''
mutants = {
    'm1': {'code': '''
def is_valid(s):
    if s == "":
        return False
    stack = []
    mapping = {')': '(', '}': '{', ']': '['}
    for char in s:
        if char in mapping.values():
            stack.append(char)
        elif char in mapping.keys():
            if not stack or stack.pop() != mapping[char]:
                return False
        else:
            return False
    return not stack
'''},
}
score, error = run_mutant_tests_sandboxed('problems/testing', test_code, ref_impl, mutants)
print(f'  Score: {score}, Error: {error}')
assert score > 0.0, f"Expected >0, got {score}"

# Test 6: run_mutant_tests_sandboxed - wrong test code
print('\n6. run_mutant_tests_sandboxed - wrong test code (passes all)')
test_code = '''
import pytest
from solution import is_valid

def test_always_pass():
    assert True
'''
score, error = run_mutant_tests_sandboxed('problems/testing', test_code, ref_impl, mutants)
print(f'  Score: {score}, Error: {error}')
# Note: this might not kill mutants if tests don't assert on function output

# Test 7: extract_code - markdown
print('\n7. extract_code - markdown')
resp = 'Here is code:\n```python\nprint("hello")\n```'
extracted = extract_code(resp)
print(f'  Extracted: {extracted}')
assert extracted == 'print("hello")'

# Test 8: extract_code - tool call JSON
print('\n8. extract_code - tool call JSON')
resp = '{"name": "modify_code", "arguments": {"code": "def foo():\\n    return 1"}}'
extracted = extract_code(resp)
print(f'  Extracted: {extracted}')
assert 'def foo():' in extracted

# Test 9: extract_code - plain text
print('\n9. extract_code - plain text')
resp = 'def foo():\n    return 1'
extracted = extract_code(resp)
print(f'  Extracted: {extracted}')
assert extracted == 'def foo():\n    return 1'

print('\n=== All control tests passed! ===')