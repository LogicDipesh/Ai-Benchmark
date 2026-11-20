import subprocess
import sys
import os
import textwrap
import tempfile

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

test_code = textwrap.dedent('''
import pytest
from solution import is_valid

def test_valid():
    assert is_valid("()") == True
    assert is_valid("()[]{}") == True
    assert is_valid("(]") == False
    assert is_valid("([]") == False
    assert is_valid("([])") == True
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
    test_dest = os.path.join(tmpdir, "test_generated.py")
    with open(test_dest, "w") as f:
        f.write(test_code)
    solution_dir = os.path.join(tmpdir, "solution_dir")
    os.makedirs(solution_dir)
    solution_path = os.path.join(solution_dir, "solution.py")
    with open(solution_path, "w") as f:
        f.write(ref_impl)
    
    # Test reference implementation
    print("=== Reference Implementation Test ===")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "../test_generated.py", "-v", "--tb=short", "--no-header"],
        cwd=solution_dir,
        capture_output=True,
        text=True,
        timeout=SANDBOX_TIMEOUT,
        env=os.environ.copy(),
    )
    print("STDOUT:", result.stdout)
    print("Return code:", result.returncode)
    
    # Test each mutant
    print("\n=== Mutant Tests ===")
    mutants_killed = 0
    for mutant_id, mutant_data in mutants.items():
        mutant_code = textwrap.dedent(mutant_data["code"])
        with open(solution_path, "w") as f:
            f.write(mutant_code)
        print(f"\n--- {mutant_id} ---")
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "../test_generated.py", "-v", "--tb=short", "--no-header"],
            cwd=solution_dir,
            capture_output=True,
            text=True,
            timeout=SANDBOX_TIMEOUT,
            env=os.environ.copy(),
        )
        print("STDOUT:", result.stdout)
        print("Return code:", result.returncode)
        failed = result.stdout.count(" FAILED")
        if failed > 0 or result.returncode != 0:
            if not ("no tests ran" in result.stdout.lower()):
                mutants_killed += 1
                print(f"  -> KILLED")
            else:
                print(f"  -> NO TESTS RAN")
        else:
            print(f"  -> SURVIVED")
    
    print(f"\nTotal mutants: {len(mutants)}, Killed: {mutants_killed}")
    print(f"Score: {mutants_killed / len(mutants) if mutants else 0}")