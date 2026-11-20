from aibenchmark.sandbox import run_mutant_tests_sandboxed

# Test with the fixed code from Groq
test_code = '''
import pytest
from solution import is_valid

@pytest.mark.parametrize(
    "s,expected",
    [
        # Empty string (edge case)
        ("", True),
        # Single characters
        ("(", False),
        (")", False),
        ("{", False),
        ("}", False),
        ("[", False),
        ("]", False),
        # Simple valid pairs
        ("()", True),
        ("[]", True),
        ("{}", True),
        # Simple invalid mismatches
        ("(]", False),
        ("{)", False),
        ("[}", False),
        # Nested valid cases
        ("(())", True),
        ("([])", True),
        ("({[]})", True),
        ("([{}])", True),
        ("{[()()]}", True),
        # Interleaved invalid cases
        ("([)]", False),
        ("{[(])}", False),
        ("({)}", False),
        # Strings containing invalid characters
        ("a", False),
        ("()", True),
        ("(a)", False),
        ("( )", False),
        ("{[a]}", False),
        # Long valid sequence
        ("()" * 10, True),
        # Deeply nested
        ("(" * 10 + ")" * 10, True),
    ],
)
def test_is_valid_various_inputs(s, expected):
    assert is_valid(s) is expected


def test_is_valid_type_error():
    with pytest.raises(TypeError):
        is_valid(None)
    with pytest.raises(TypeError):
        is_valid(123)
    assert is_valid(b"()") is False
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
    'mutant_001': {'code': '''def is_valid(s):
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
    return not stack'''},
    'mutant_002': {'code': '''def is_valid(s):
    stack = []
    mapping = {')': '(', '}': '{', ']': '['}
    for char in s:
        if char in mapping.values():
            stack.append(char)
        elif char in mapping.keys():
            if stack and stack.pop() != mapping[char]:
                return False
    return True'''},
    'mutant_003': {'code': '''def is_valid(s):
    stack = []
    mapping = {')': '(', '}': '{', ']': '['}
    for char in s:
        if char in mapping.values():
            stack.append(char)
        elif char in mapping.keys():
            if not stack or stack.pop() != mapping[char]:
                return False
    return not stack'''}
}

print('Calling sandbox...')
score, error_type = run_mutant_tests_sandboxed('problems/testing', test_code, ref_impl, mutants)
print(f'Score: {score}, Error: {error_type}')