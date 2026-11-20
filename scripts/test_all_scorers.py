from aibenchmark.sandbox import run_tests_sandboxed, run_mutant_tests_sandboxed, extract_code

print('=== DEBUGGING SCORER ===')
# Correct fix for binary search off-by-one
code = """
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
"""
score, status, error = run_tests_sandboxed('problems/debugging', code, 'problems/debugging/test_debug_001.py')
print(f'Correct fix - Score: {score}, Status: {status}, Error: {error}')

# Wrong fix
wrong_code = """
def binary_search(arr, target):
    return 0
"""
score, status, error = run_tests_sandboxed('problems/debugging', wrong_code, 'problems/debugging/test_debug_001.py')
print(f'Wrong fix - Score: {score}, Status: {status}, Error: {error}')

print()
print('=== TESTING SCORER (mutant killing) ===')
# Test with correct test code that should kill mutants
test_code = """
import pytest
from solution import is_valid

def test_empty():
    assert is_valid("") == True

def test_simple():
    assert is_valid("()") == True
    assert is_valid("()[]{}") == True

def test_invalid():
    assert is_valid("(]") == False
    assert is_valid("([)]") == False
"""

ref_impl = """
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
"""

mutants = {
    'm1': {'code': """
def is_valid(s):
    if s == \"\":
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
"""},
    'm2': {'code': """
def is_valid(s):
    stack = []
    mapping = {')': '(', '}': '{', ']': '['}
    for char in s:
        if char in mapping.values():
            stack.append(char)
        elif char in mapping.keys():
            if stack and stack.pop() != mapping[char]:
                return False
    return True
"""},
}

score, error = run_mutant_tests_sandboxed('problems/testing', test_code, ref_impl, mutants)
print(f'Correct tests - Score: {score}, Error: {error}')

# Test with always-passing tests (should not kill mutants)
bad_test = """
import pytest
from solution import is_valid

def test_always():
    assert True
"""
score, error = run_mutant_tests_sandboxed('problems/testing', bad_test, test_code, mutants)
print(f'Always-pass tests - Score: {score}, Error: {error}')

# Test extract_code
print()
print('=== EXTRACT_CODE ===')
resp = '```python\ndef foo(): pass\n```'
print(f'Markdown: {extract_code(resp)}')

resp = '{"name": "modify_code", "arguments": {"code": "def foo():\\n    return 1"}}'
print(f'Tool call: {extract_code(resp)}')

resp = 'def foo(): pass'
print(f'Plain: {extract_code(resp)}')

print('\\n=== All basic control tests completed ===')