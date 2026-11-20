# Failure artifact: testing_001_valid_parentheses (testing)

- Provider: groq
- Model: openai/gpt-oss-120b
- Score: 0.0
- Status: failed
- Error: reference_impl_failed
- Latency (ms): 1679
- Written (UTC): 20261031-144133
- Run id: not recorded (evaluators do not receive one); match by timestamp + problem + provider.

## Prompt sent

```
Write comprehensive tests for the following function:

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

The function checks if a string of parentheses is valid.
Write tests covering edge cases. Output only the test code
in a Python code block.


Return ONLY one Python code block containing the test code and nothing else. No explanation, no preamble, no text outside the block. Import the function from 'solution' module (e.g., 'from solution import is_valid').
```

## Raw model response

```
```python
import pytest
from solution import is_valid

@pytest.mark.parametrize(
    "s, expected",
    [
        # Valid cases
        ("", True),                               # empty string
        ("()", True),
        ("[]", True),
        ("{}", True),
        ("()[]{}", True),
        ("({[]})", True),
        ("[({})]", True),
        ("(((())))", True),                      # nested same type
        ("{}[]()", True),
        ("{[()()]}", True),
        ("(((([[[{{{}}}]]] ))))", True),         # mixed deep nesting
        ("()" * 500, True),                      # long repetitive valid sequence
        ("({})" * 250, True),                    # long mixed valid sequence
        # Invalid cases
        ("(", False),                             # single opening
        (")", False),                             # single closing
        ("(]", False),                            # mismatched pair
        ("([)]", False),                          # wrong order
        ("((()", False),                          # incomplete
        ("())", False),                           # extra closing
        ("{[}", False),                           # missing closing
        ("{[)]}", False),                         # complex mismatch
        ("abc", False),                           # invalid characters
        ("(a)", False),                           # mixed valid and invalid characters
        ("[)", False),                            # mismatched types
        ("{)(", False),                           # completely wrong order
        ("(()))((()", False),                     # unbalanced multiple issues
        ("(" * 1000, False),                     # very long only openings
        (")" * 1000, False),                     # very long only closings
    ]
)
def test_is_valid(s, expected):
    assert is_valid(s) is expected
```
```

## Extracted code, before import fix

```python
import pytest
from solution import is_valid

@pytest.mark.parametrize(
    "s, expected",
    [
        # Valid cases
        ("", True),                               # empty string
        ("()", True),
        ("[]", True),
        ("{}", True),
        ("()[]{}", True),
        ("({[]})", True),
        ("[({})]", True),
        ("(((())))", True),                      # nested same type
        ("{}[]()", True),
        ("{[()()]}", True),
        ("(((([[[{{{}}}]]] ))))", True),         # mixed deep nesting
        ("()" * 500, True),                      # long repetitive valid sequence
        ("({})" * 250, True),                    # long mixed valid sequence
        # Invalid cases
        ("(", False),                             # single opening
        (")", False),                             # single closing
        ("(]", False),                            # mismatched pair
        ("([)]", False),                          # wrong order
        ("((()", False),                          # incomplete
        ("())", False),                           # extra closing
        ("{[}", False),                           # missing closing
        ("{[)]}", False),                         # complex mismatch
        ("abc", False),                           # invalid characters
        ("(a)", False),                           # mixed valid and invalid characters
        ("[)", False),                            # mismatched types
        ("{)(", False),                           # completely wrong order
        ("(()))((()", False),                     # unbalanced multiple issues
        ("(" * 1000, False),                     # very long only openings
        (")" * 1000, False),                     # very long only closings
    ]
)
def test_is_valid(s, expected):
    assert is_valid(s) is expected
```

## Executed code

```python
import pytest
from solution import is_valid

@pytest.mark.parametrize(
    "s, expected",
    [
        # Valid cases
        ("", True),                               # empty string
        ("()", True),
        ("[]", True),
        ("{}", True),
        ("()[]{}", True),
        ("({[]})", True),
        ("[({})]", True),
        ("(((())))", True),                      # nested same type
        ("{}[]()", True),
        ("{[()()]}", True),
        ("(((([[[{{{}}}]]] ))))", True),         # mixed deep nesting
        ("()" * 500, True),                      # long repetitive valid sequence
        ("({})" * 250, True),                    # long mixed valid sequence
        # Invalid cases
        ("(", False),                             # single opening
        (")", False),                             # single closing
        ("(]", False),                            # mismatched pair
        ("([)]", False),                          # wrong order
        ("((()", False),                          # incomplete
        ("())", False),                           # extra closing
        ("{[}", False),                           # missing closing
        ("{[)]}", False),                         # complex mismatch
        ("abc", False),                           # invalid characters
        ("(a)", False),                           # mixed valid and invalid characters
        ("[)", False),                            # mismatched types
        ("{)(", False),                           # completely wrong order
        ("(()))((()", False),                     # unbalanced multiple issues
        ("(" * 1000, False),                     # very long only openings
        (")" * 1000, False),                     # very long only closings
    ]
)
def test_is_valid(s, expected):
    assert is_valid(s) is expected
```

## Reference implementation (what the suite was tested against)

```python
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

```

## Mutants in this problem: mutant_001, mutant_002, mutant_003

## How to reproduce the detail

The bench ran this suite sandboxed: the executed test code was saved as test_generated.py, the reference as solution.py in a solution_dir, and pytest ran with `-v --tb=short` (10 s timeout, Python-level network blocked). First the suite must pass cleanly against the reference, else the row is reference_impl_failed; then each mutant's code replaces solution.py and the suite must fail it to count a kill. To see which mutants survived, re-run the suite above against the reference and then against each mutant from the problem YAML.

Diagnostic only: this file changes no score, no row, and no database entry.
