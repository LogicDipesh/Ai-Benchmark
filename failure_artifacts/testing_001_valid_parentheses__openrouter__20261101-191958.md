# Failure artifact: testing_001_valid_parentheses (testing)

- Provider: openrouter
- Model: nvidia/nemotron-3.5-lightning:free
- Score: 0.0
- Status: failed
- Error: reference_impl_failed
- Latency (ms): 50292
- Written (UTC): 20261101-191958
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
import unittest
from solution import is_valid


class TestIsValid(unittest.TestCase):
    def test_basic_valid(self):
        self.assertTrue(is_valid("()"))
        self.assertTrue(is_valid("[]"))
        self.assertTrue(is_valid("{}"))

    def test_nested_valid(self):
        self.assertTrue(is_valid("({[]})"))
        self.assertTrue(is_valid("([{}])"))
        self.assertTrue(is_valid("{[]}"))

    def test_invalid_mismatch(self):
        self.assertFalse(is_valid("(]"))
        self.assertFalse(is_valid("([)]"))
        self.assertFalse(is_valid("{[}]"))

    def test_unbalanced_open(self):
        self.assertFalse(is_valid("("))
        self.assertFalse(is_valid("["))
        self.assertFalse(is_valid("{"))
        self.assertFalse(is_valid("((("))
        self.assertFalse(is_valid("({["))
        self.assertFalse(is_valid("("))

    def test_unbalanced_close(self):
        self.assertFalse(is_valid(")"))
        self.assertFalse(is_valid("]"))
        self.assertFalse(is_valid("}"))
        self.assertFalse(is_valid(")("))
        self.assertFalse(is_valid("())"))

    def test_empty_string(self):
        self.assertTrue(is_valid(""))

    def test_non_bracket_characters(self):
        self.assertFalse(is_valid("a"))
        self.assertFalse(is_valid("(a)"))
        self.assertFalse(is_valid("123"))
        self.assertFalse(is_valid(" "))

    def test_single_bracket(self):
        self.assertFalse(is_valid("("))
        self.assertFalse(is_valid(")"))
        self.assertFalse(is_valid("["))
        self.assertFalse(is_valid("]"))
        self.assertFalse(is_valid("{"))
        self.assertFalse(is_valid("}"))

    def test_valid_multiple_pairs(self):
        self.assertTrue(is_valid("()[]{}"))
        self.assertTrue(is_valid("([]{})"))
        self.assertTrue(is_valid("()()[]"))

    def test_complex_invalid(self):
        self.assertFalse(is_valid("([)]"))
        self.assertFalse(is_valid("{[}"))
        self.assertFalse(is_valid("((]"))

    def test_string_starting_with_close(self):
        self.assertFalse(is_valid(")("))
        self.assertFalse(is_valid(")())"))

    def test_long_valid(self):
        self.assertTrue(is_valid("((({{[]}}}))"))
        self.assertTrue(is_valid("[[{{(())}}]]"))
        self.assertTrue(is_valid("(((())))"))
        self.assertTrue(is_valid("[[[[]]]]"))

    def test_almost_valid(self):
        self.assertFalse(is_valid("("))
        self.assertFalse(is_valid(")"))
        self.assertFalse(is_valid(")())"))
        self.assertFalse(is_valid("(()"))


if __name__ == "__main__":
    unittest.main()
```
```

## Extracted code, before import fix

```python
import unittest
from solution import is_valid


class TestIsValid(unittest.TestCase):
    def test_basic_valid(self):
        self.assertTrue(is_valid("()"))
        self.assertTrue(is_valid("[]"))
        self.assertTrue(is_valid("{}"))

    def test_nested_valid(self):
        self.assertTrue(is_valid("({[]})"))
        self.assertTrue(is_valid("([{}])"))
        self.assertTrue(is_valid("{[]}"))

    def test_invalid_mismatch(self):
        self.assertFalse(is_valid("(]"))
        self.assertFalse(is_valid("([)]"))
        self.assertFalse(is_valid("{[}]"))

    def test_unbalanced_open(self):
        self.assertFalse(is_valid("("))
        self.assertFalse(is_valid("["))
        self.assertFalse(is_valid("{"))
        self.assertFalse(is_valid("((("))
        self.assertFalse(is_valid("({["))
        self.assertFalse(is_valid("("))

    def test_unbalanced_close(self):
        self.assertFalse(is_valid(")"))
        self.assertFalse(is_valid("]"))
        self.assertFalse(is_valid("}"))
        self.assertFalse(is_valid(")("))
        self.assertFalse(is_valid("())"))

    def test_empty_string(self):
        self.assertTrue(is_valid(""))

    def test_non_bracket_characters(self):
        self.assertFalse(is_valid("a"))
        self.assertFalse(is_valid("(a)"))
        self.assertFalse(is_valid("123"))
        self.assertFalse(is_valid(" "))

    def test_single_bracket(self):
        self.assertFalse(is_valid("("))
        self.assertFalse(is_valid(")"))
        self.assertFalse(is_valid("["))
        self.assertFalse(is_valid("]"))
        self.assertFalse(is_valid("{"))
        self.assertFalse(is_valid("}"))

    def test_valid_multiple_pairs(self):
        self.assertTrue(is_valid("()[]{}"))
        self.assertTrue(is_valid("([]{})"))
        self.assertTrue(is_valid("()()[]"))

    def test_complex_invalid(self):
        self.assertFalse(is_valid("([)]"))
        self.assertFalse(is_valid("{[}"))
        self.assertFalse(is_valid("((]"))

    def test_string_starting_with_close(self):
        self.assertFalse(is_valid(")("))
        self.assertFalse(is_valid(")())"))

    def test_long_valid(self):
        self.assertTrue(is_valid("((({{[]}}}))"))
        self.assertTrue(is_valid("[[{{(())}}]]"))
        self.assertTrue(is_valid("(((())))"))
        self.assertTrue(is_valid("[[[[]]]]"))

    def test_almost_valid(self):
        self.assertFalse(is_valid("("))
        self.assertFalse(is_valid(")"))
        self.assertFalse(is_valid(")())"))
        self.assertFalse(is_valid("(()"))


if __name__ == "__main__":
    unittest.main()
```

## Executed code

```python
import unittest
from solution import is_valid


class TestIsValid(unittest.TestCase):
    def test_basic_valid(self):
        self.assertTrue(is_valid("()"))
        self.assertTrue(is_valid("[]"))
        self.assertTrue(is_valid("{}"))

    def test_nested_valid(self):
        self.assertTrue(is_valid("({[]})"))
        self.assertTrue(is_valid("([{}])"))
        self.assertTrue(is_valid("{[]}"))

    def test_invalid_mismatch(self):
        self.assertFalse(is_valid("(]"))
        self.assertFalse(is_valid("([)]"))
        self.assertFalse(is_valid("{[}]"))

    def test_unbalanced_open(self):
        self.assertFalse(is_valid("("))
        self.assertFalse(is_valid("["))
        self.assertFalse(is_valid("{"))
        self.assertFalse(is_valid("((("))
        self.assertFalse(is_valid("({["))
        self.assertFalse(is_valid("("))

    def test_unbalanced_close(self):
        self.assertFalse(is_valid(")"))
        self.assertFalse(is_valid("]"))
        self.assertFalse(is_valid("}"))
        self.assertFalse(is_valid(")("))
        self.assertFalse(is_valid("())"))

    def test_empty_string(self):
        self.assertTrue(is_valid(""))

    def test_non_bracket_characters(self):
        self.assertFalse(is_valid("a"))
        self.assertFalse(is_valid("(a)"))
        self.assertFalse(is_valid("123"))
        self.assertFalse(is_valid(" "))

    def test_single_bracket(self):
        self.assertFalse(is_valid("("))
        self.assertFalse(is_valid(")"))
        self.assertFalse(is_valid("["))
        self.assertFalse(is_valid("]"))
        self.assertFalse(is_valid("{"))
        self.assertFalse(is_valid("}"))

    def test_valid_multiple_pairs(self):
        self.assertTrue(is_valid("()[]{}"))
        self.assertTrue(is_valid("([]{})"))
        self.assertTrue(is_valid("()()[]"))

    def test_complex_invalid(self):
        self.assertFalse(is_valid("([)]"))
        self.assertFalse(is_valid("{[}"))
        self.assertFalse(is_valid("((]"))

    def test_string_starting_with_close(self):
        self.assertFalse(is_valid(")("))
        self.assertFalse(is_valid(")())"))

    def test_long_valid(self):
        self.assertTrue(is_valid("((({{[]}}}))"))
        self.assertTrue(is_valid("[[{{(())}}]]"))
        self.assertTrue(is_valid("(((())))"))
        self.assertTrue(is_valid("[[[[]]]]"))

    def test_almost_valid(self):
        self.assertFalse(is_valid("("))
        self.assertFalse(is_valid(")"))
        self.assertFalse(is_valid(")())"))
        self.assertFalse(is_valid("(()"))


if __name__ == "__main__":
    unittest.main()
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
