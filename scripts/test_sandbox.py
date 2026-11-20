from aibenchmark.sandbox import run_mutant_tests_sandboxed, extract_code
from aibenchmark.providers import PROVIDERS

# Test the reference implementation first
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

# Test with a simple test code
test_code = '''
import pytest
from solution import is_valid

def test_valid():
    assert is_valid("()") == True
    assert is_valid("()[]{}") == True
    assert is_valid("(]") == False
    assert is_valid("([]") == True
'''

mutants = {
    'mutant_001': {
        'code': '''
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
'''
    },
    'mutant_002': {
        'code': '''
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
'''
    },
    'mutant_003': {
        'code': '''
def is_valid(s):
    stack = []
    mapping = {')': '(', '}': '{', ']': '['}
    for char in s:
        if char in mapping.values():
            stack.append(char)
        elif char in mapping.keys():
            if not stack or stack.pop() != mapping[char]:
                return False
    return not stack
'''
    }
}

score = run_mutant_tests_sandboxed('problems/testing', test_code, ref_impl, mutants)
print(f'Score: {score}')