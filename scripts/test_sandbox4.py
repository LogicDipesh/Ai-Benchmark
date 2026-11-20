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

# Fixed test - "([]" should return False (unmatched)
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

with tempfile.TemporaryDirectory() as tmpdir:
    test_dest = os.path.join(tmpdir, "test_generated.py")
    with open(test_dest, "w") as f:
        f.write(test_code)
    solution_dir = os.path.join(tmpdir, "solution_dir")
    os.makedirs(solution_dir)
    solution_path = os.path.join(solution_dir, "solution.py")
    with open(solution_path, "w") as f:
        f.write(ref_impl)
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "../test_generated.py", "-v", "--tb=short", "--no-header"],
        cwd=solution_dir,
        capture_output=True,
        text=True,
        timeout=10,
        env=os.environ.copy(),
    )
    print("STDOUT:")
    print(result.stdout)
    print("STDERR:")
    print(result.stderr)
    print("Return code:", result.returncode)