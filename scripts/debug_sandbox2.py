import subprocess
import sys
import os
import textwrap
import tempfile

# Fixed test code - import from solution, not paren_check
test_code = textwrap.dedent('''
import pytest

# Import from solution module
from solution import is_valid


@pytest.mark.parametrize(
    "s,expected",
    [
        # Empty string – trivially valid
        ("", True),

        # Simple matching pairs
        ("()", True),
        ("[]", True),
        ("{}", True),

        # Multiple consecutive pairs
        ("()[]{}", True),
        ("{}[]()", True),

        # Nested structures
        ("(())", True),
        ("({[]})", True),
        ("[({})]", True),

        # Interleaved but still valid
        ("([]{})", True),
        ("{[()()]}", True),

        # Long repetitive valid pattern
        ("()()()()()()()()()()", True),

        # Single opening or closing bracket – invalid
        ("(", False),
        (")", False),
        ("[", False),
        ("]", False),
        ("{", False),
        ("}", False),

        # Mismatched types
        ("(]", False),
        ("([)]", False),
        ("{[}]", False),

        # Unbalanced counts
        ("(()", False),
        ("())", False),
        ("[({})", False),
        ("[({})])", False),

        # Invalid characters
        ("abc", False),
        ("()a", False),
        ("[1]", False),
        ("{ }", False),   # space inside makes it invalid

        # Mixed valid and invalid characters
        ("()[]x", False),
        ("x()[]", False),

        # Very long invalid string (deeply nested but missing closing)
        ("(" * 1000, False),

        # Very long valid string (balanced deep nesting)
        ("(" * 500 + ")" * 500, True),
    ],
)
def test_is_valid_various_inputs(s, expected):
    """Parametrized test covering typical, edge-case and error inputs."""
    assert is_valid(s) is expected


def test_is_valid_type_error():
    """The function expects an iterable (string). Non-iterable should raise TypeError."""
    with pytest.raises(TypeError):
        is_valid(None)          # None is not iterable
    with pytest.raises(TypeError):
        is_valid(123)           # int is not iterable
    # Passing a bytes object is iterable but yields ints, which are not in mapping -> False
    assert is_valid(b"()") is False
''')

ref_impl = textwrap.dedent('''
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
''')

mutants = {
    'mutant_001': {
        'code': textwrap.dedent('''
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
''')
    },
    'mutant_002': {
        'code': textwrap.dedent('''
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
''')
    },
    'mutant_003': {
        'code': textwrap.dedent('''
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
''')
    }
}

with tempfile.TemporaryDirectory() as tmpdir:
    test_dest = os.path.join(tmpdir, 'test_generated.py')
    with open(test_dest, 'w') as f:
        f.write(test_code)
    solution_dir = os.path.join(tmpdir, 'solution_dir')
    os.makedirs(solution_dir)
    solution_path = os.path.join(solution_dir, 'solution.py')
    with open(solution_path, 'w') as f:
        f.write(ref_impl)
    
    print('=== Testing reference implementation (fixed import) ===')
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', '../test_generated.py', '-v', '--tb=long', '--no-header'],
        cwd=solution_dir,
        capture_output=True,
        text=True,
        timeout=10,
        env=os.environ.copy(),
    )
    print('STDOUT:')
    print(result.stdout)
    print('STDERR:')
    print(result.stderr)
    print('Return code:', result.returncode)