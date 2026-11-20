import subprocess
import sys
import os
import textwrap
import tempfile

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

SANDBOX_TIMEOUT = 10

with tempfile.TemporaryDirectory() as tmpdir:
    test_dest = os.path.join(tmpdir, 'test_generated.py')
    with open(test_dest, 'w') as f:
        f.write(test_code)
    solution_dir = os.path.join(tmpdir, 'solution_dir')
    os.makedirs(solution_dir)
    solution_path = os.path.join(solution_dir, 'solution.py')
    with open(solution_path, 'w') as f:
        f.write(ref_impl)
    
    print('=== Reference Implementation Test ===')
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', '../test_generated.py', '-v', '--tb=short', '--no-header'],
        cwd=solution_dir,
        capture_output=True,
        text=True,
        timeout=SANDBOX_TIMEOUT,
        env=os.environ.copy(),
    )
    output = result.stdout + result.stderr
    print('Return code:', result.returncode)
    passed = output.count(' PASSED')
    failed = output.count(' FAILED')
    print(f'passed={passed}, failed={failed}')
    
    # Test each mutant
    print('\n=== Mutant Tests ===')
    mutants_killed = 0
    for mutant_id, mutant_data in mutants.items():
        mutant_code = textwrap.dedent(mutant_data["code"])
        with open(solution_path, "w") as f:
            f.write(mutant_code)
        print(f'\n--- {mutant_id} ---')
        result = subprocess.run(
            [sys.executable, '-m', 'pytest', '../test_generated.py', '-v', '--tb=short', '--no-header'],
            cwd=solution_dir,
            capture_output=True,
            text=True,
            timeout=SANDBOX_TIMEOUT,
            env=os.environ.copy(),
        )
        output = result.stdout + result.stderr
        print(output[:500])
        failed = output.count(" FAILED")
        if failed > 0 or result.returncode != 0:
            if not ("no tests ran" in output.lower()):
                mutants_killed += 1
                print(f"  -> KILLED")
            else:
                print(f"  -> NO TESTS RAN")
        else:
            print(f"  -> SURVIVED")
    
    print(f'\nTotal mutants: {len(mutants)}, Killed: {mutants_killed}')
    print(f'Score: {mutants_killed / len(mutants) if mutants else 0}')