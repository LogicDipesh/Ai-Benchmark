# Failure artifact: testing_001_valid_parentheses (testing)

- Provider: nvidia
- Model: nvidia/nemotron-3-ultra-550b-a55b
- Score: 0.0
- Status: failed
- Error: reference_impl_failed
- Latency (ms): 16109
- Written (UTC): 20261102-101616
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

    def test_empty_string(self):
        self.assertTrue(is_valid(""))

    def test_single_opening_bracket(self):
        self.assertFalse(is_valid("("))
        self.assertFalse(is_valid("{"))
        self.assertFalse(is_valid("["))

    def test_single_closing_bracket(self):
        self.assertFalse(is_valid(")"))
        self.assertFalse(is_valid("}"))
        self.assertFalse(is_valid("]"))

    def test_valid_pairs(self):
        self.assertTrue(is_valid("()"))
        self.assertTrue(is_valid("{}"))
        self.assertTrue(is_valid("[]"))

    def test_nested_valid(self):
        self.assertTrue(is_valid("({[]})"))
        self.assertTrue(is_valid("([{}])"))
        self.assertTrue(is_valid("{[()]}"))
        self.assertTrue(is_valid("((()))"))
        self.assertTrue(is_valid("{{{{}}}}"))
        self.assertTrue(is_valid("[[[]]]"))

    def test_multiple_adjacent_valid(self):
        self.assertTrue(is_valid("()[]{}"))
        self.assertTrue(is_valid("(){}[]"))
        self.assertTrue(is_valid("[](){}"))
        self.assertTrue(is_valid("{}[]()"))
        self.assertTrue(is_valid("[][][]"))
        self.assertTrue(is_valid("()()()"))
        self.assertTrue(is_valid("{}{}{}"))

    def test_mismatched_brackets(self):
        self.assertFalse(is_valid("(]"))
        self.assertFalse(is_valid("([)]"))
        self.assertFalse(is_valid("{[}]"))
        self.assertFalse(is_valid("(}"))
        self.assertFalse(is_valid("[)"))
        self.assertFalse(is_valid("{)"))
        self.assertFalse(is_valid("([)]"))
        self.assertFalse(is_valid("([}]"))
        self.assertFalse(is_valid("({)}"))

    def test_extra_opening_brackets(self):
        self.assertFalse(is_valid("((("))
        self.assertFalse(is_valid("{{{"))
        self.assertFalse(is_valid("[[["))
        self.assertFalse(is_valid("(()"))
        self.assertFalse(is_valid("({}"))
        self.assertFalse(is_valid("[[]"))
        self.assertFalse(is_valid("({[]"))

    def test_extra_closing_brackets(self):
        self.assertFalse(is_valid(")))"))
        self.assertFalse(is_valid("}}}"))
        self.assertFalse(is_valid("]]]"))
        self.assertFalse(is_valid("())"))
        self.assertFalse(is_valid("{}))"))
        self.assertFalse(is_valid("[]]]"))
        self.assertFalse(is_valid("()]]"))

    def test_non_bracket_characters(self):
        self.assertFalse(is_valid("a"))
        self.assertFalse(is_valid("(a)"))
        self.assertFalse(is_valid("()a"))
        self.assertFalse(is_valid("a()"))
        self.assertFalse(is_valid("( )"))
        self.assertFalse(is_valid(""))
        self.assertFalse(is_valid("1"))
        self.assertFalse(is_valid("()1[]"))

    def test_long_valid_string(self):
        long_valid = "()" * 1000
        self.assertTrue(is_valid(long_valid))
        long_nested = "(" * 500 + ")" * 500
        self.assertTrue(is_valid(long_nested))
        mixed = "({[]})" * 100
        self.assertTrue(is_valid(mixed))

    def test_long_invalid_string(self):
        long_invalid = "(" * 1000
        self.assertFalse(is_valid(long_invalid))
        long_invalid2 = "()" * 500 + "("
        self.assertFalse(is_valid(long_invalid2))
        long_invalid3 = "(" + "()" * 500
        self.assertFalse(is_valid(long_invalid3))
        mismatched_long = "([)]" * 250
        self.assertFalse(is_valid(mismatched_long))

    def test_complex_valid_cases(self):
        self.assertTrue(is_valid("({[]})"))
        self.assertTrue(is_valid("{[()]}"))
        self.assertTrue(is_valid("(({{[[]]}}))"))
        self.assertTrue(is_valid("()[]{}[({})]"))
        self.assertTrue(is_valid("(((({{{{[[[]]]}}}}))))"))

    def test_complex_invalid_cases(self):
        self.assertFalse(is_valid("({[}])"))
        self.assertFalse(is_valid("{[(])}"))
        self.assertFalse(is_valid("([)]"))
        self.assertFalse(is_valid("(({{[[]]}})"))
        self.assertFalse(is_valid("()[]{}[({})"))
        self.assertFalse(is_valid("(((({{{{[[[]]]}}}})))))"))

if __name__ == "__main__":
    unittest.main()
```
```

## Extracted code, before import fix

```python
import unittest
from solution import is_valid

class TestIsValid(unittest.TestCase):

    def test_empty_string(self):
        self.assertTrue(is_valid(""))

    def test_single_opening_bracket(self):
        self.assertFalse(is_valid("("))
        self.assertFalse(is_valid("{"))
        self.assertFalse(is_valid("["))

    def test_single_closing_bracket(self):
        self.assertFalse(is_valid(")"))
        self.assertFalse(is_valid("}"))
        self.assertFalse(is_valid("]"))

    def test_valid_pairs(self):
        self.assertTrue(is_valid("()"))
        self.assertTrue(is_valid("{}"))
        self.assertTrue(is_valid("[]"))

    def test_nested_valid(self):
        self.assertTrue(is_valid("({[]})"))
        self.assertTrue(is_valid("([{}])"))
        self.assertTrue(is_valid("{[()]}"))
        self.assertTrue(is_valid("((()))"))
        self.assertTrue(is_valid("{{{{}}}}"))
        self.assertTrue(is_valid("[[[]]]"))

    def test_multiple_adjacent_valid(self):
        self.assertTrue(is_valid("()[]{}"))
        self.assertTrue(is_valid("(){}[]"))
        self.assertTrue(is_valid("[](){}"))
        self.assertTrue(is_valid("{}[]()"))
        self.assertTrue(is_valid("[][][]"))
        self.assertTrue(is_valid("()()()"))
        self.assertTrue(is_valid("{}{}{}"))

    def test_mismatched_brackets(self):
        self.assertFalse(is_valid("(]"))
        self.assertFalse(is_valid("([)]"))
        self.assertFalse(is_valid("{[}]"))
        self.assertFalse(is_valid("(}"))
        self.assertFalse(is_valid("[)"))
        self.assertFalse(is_valid("{)"))
        self.assertFalse(is_valid("([)]"))
        self.assertFalse(is_valid("([}]"))
        self.assertFalse(is_valid("({)}"))

    def test_extra_opening_brackets(self):
        self.assertFalse(is_valid("((("))
        self.assertFalse(is_valid("{{{"))
        self.assertFalse(is_valid("[[["))
        self.assertFalse(is_valid("(()"))
        self.assertFalse(is_valid("({}"))
        self.assertFalse(is_valid("[[]"))
        self.assertFalse(is_valid("({[]"))

    def test_extra_closing_brackets(self):
        self.assertFalse(is_valid(")))"))
        self.assertFalse(is_valid("}}}"))
        self.assertFalse(is_valid("]]]"))
        self.assertFalse(is_valid("())"))
        self.assertFalse(is_valid("{}))"))
        self.assertFalse(is_valid("[]]]"))
        self.assertFalse(is_valid("()]]"))

    def test_non_bracket_characters(self):
        self.assertFalse(is_valid("a"))
        self.assertFalse(is_valid("(a)"))
        self.assertFalse(is_valid("()a"))
        self.assertFalse(is_valid("a()"))
        self.assertFalse(is_valid("( )"))
        self.assertFalse(is_valid(""))
        self.assertFalse(is_valid("1"))
        self.assertFalse(is_valid("()1[]"))

    def test_long_valid_string(self):
        long_valid = "()" * 1000
        self.assertTrue(is_valid(long_valid))
        long_nested = "(" * 500 + ")" * 500
        self.assertTrue(is_valid(long_nested))
        mixed = "({[]})" * 100
        self.assertTrue(is_valid(mixed))

    def test_long_invalid_string(self):
        long_invalid = "(" * 1000
        self.assertFalse(is_valid(long_invalid))
        long_invalid2 = "()" * 500 + "("
        self.assertFalse(is_valid(long_invalid2))
        long_invalid3 = "(" + "()" * 500
        self.assertFalse(is_valid(long_invalid3))
        mismatched_long = "([)]" * 250
        self.assertFalse(is_valid(mismatched_long))

    def test_complex_valid_cases(self):
        self.assertTrue(is_valid("({[]})"))
        self.assertTrue(is_valid("{[()]}"))
        self.assertTrue(is_valid("(({{[[]]}}))"))
        self.assertTrue(is_valid("()[]{}[({})]"))
        self.assertTrue(is_valid("(((({{{{[[[]]]}}}}))))"))

    def test_complex_invalid_cases(self):
        self.assertFalse(is_valid("({[}])"))
        self.assertFalse(is_valid("{[(])}"))
        self.assertFalse(is_valid("([)]"))
        self.assertFalse(is_valid("(({{[[]]}})"))
        self.assertFalse(is_valid("()[]{}[({})"))
        self.assertFalse(is_valid("(((({{{{[[[]]]}}}})))))"))

if __name__ == "__main__":
    unittest.main()
```

## Executed code

```python
import unittest
from solution import is_valid

class TestIsValid(unittest.TestCase):

    def test_empty_string(self):
        self.assertTrue(is_valid(""))

    def test_single_opening_bracket(self):
        self.assertFalse(is_valid("("))
        self.assertFalse(is_valid("{"))
        self.assertFalse(is_valid("["))

    def test_single_closing_bracket(self):
        self.assertFalse(is_valid(")"))
        self.assertFalse(is_valid("}"))
        self.assertFalse(is_valid("]"))

    def test_valid_pairs(self):
        self.assertTrue(is_valid("()"))
        self.assertTrue(is_valid("{}"))
        self.assertTrue(is_valid("[]"))

    def test_nested_valid(self):
        self.assertTrue(is_valid("({[]})"))
        self.assertTrue(is_valid("([{}])"))
        self.assertTrue(is_valid("{[()]}"))
        self.assertTrue(is_valid("((()))"))
        self.assertTrue(is_valid("{{{{}}}}"))
        self.assertTrue(is_valid("[[[]]]"))

    def test_multiple_adjacent_valid(self):
        self.assertTrue(is_valid("()[]{}"))
        self.assertTrue(is_valid("(){}[]"))
        self.assertTrue(is_valid("[](){}"))
        self.assertTrue(is_valid("{}[]()"))
        self.assertTrue(is_valid("[][][]"))
        self.assertTrue(is_valid("()()()"))
        self.assertTrue(is_valid("{}{}{}"))

    def test_mismatched_brackets(self):
        self.assertFalse(is_valid("(]"))
        self.assertFalse(is_valid("([)]"))
        self.assertFalse(is_valid("{[}]"))
        self.assertFalse(is_valid("(}"))
        self.assertFalse(is_valid("[)"))
        self.assertFalse(is_valid("{)"))
        self.assertFalse(is_valid("([)]"))
        self.assertFalse(is_valid("([}]"))
        self.assertFalse(is_valid("({)}"))

    def test_extra_opening_brackets(self):
        self.assertFalse(is_valid("((("))
        self.assertFalse(is_valid("{{{"))
        self.assertFalse(is_valid("[[["))
        self.assertFalse(is_valid("(()"))
        self.assertFalse(is_valid("({}"))
        self.assertFalse(is_valid("[[]"))
        self.assertFalse(is_valid("({[]"))

    def test_extra_closing_brackets(self):
        self.assertFalse(is_valid(")))"))
        self.assertFalse(is_valid("}}}"))
        self.assertFalse(is_valid("]]]"))
        self.assertFalse(is_valid("())"))
        self.assertFalse(is_valid("{}))"))
        self.assertFalse(is_valid("[]]]"))
        self.assertFalse(is_valid("()]]"))

    def test_non_bracket_characters(self):
        self.assertFalse(is_valid("a"))
        self.assertFalse(is_valid("(a)"))
        self.assertFalse(is_valid("()a"))
        self.assertFalse(is_valid("a()"))
        self.assertFalse(is_valid("( )"))
        self.assertFalse(is_valid(""))
        self.assertFalse(is_valid("1"))
        self.assertFalse(is_valid("()1[]"))

    def test_long_valid_string(self):
        long_valid = "()" * 1000
        self.assertTrue(is_valid(long_valid))
        long_nested = "(" * 500 + ")" * 500
        self.assertTrue(is_valid(long_nested))
        mixed = "({[]})" * 100
        self.assertTrue(is_valid(mixed))

    def test_long_invalid_string(self):
        long_invalid = "(" * 1000
        self.assertFalse(is_valid(long_invalid))
        long_invalid2 = "()" * 500 + "("
        self.assertFalse(is_valid(long_invalid2))
        long_invalid3 = "(" + "()" * 500
        self.assertFalse(is_valid(long_invalid3))
        mismatched_long = "([)]" * 250
        self.assertFalse(is_valid(mismatched_long))

    def test_complex_valid_cases(self):
        self.assertTrue(is_valid("({[]})"))
        self.assertTrue(is_valid("{[()]}"))
        self.assertTrue(is_valid("(({{[[]]}}))"))
        self.assertTrue(is_valid("()[]{}[({})]"))
        self.assertTrue(is_valid("(((({{{{[[[]]]}}}}))))"))

    def test_complex_invalid_cases(self):
        self.assertFalse(is_valid("({[}])"))
        self.assertFalse(is_valid("{[(])}"))
        self.assertFalse(is_valid("([)]"))
        self.assertFalse(is_valid("(({{[[]]}})"))
        self.assertFalse(is_valid("()[]{}[({})"))
        self.assertFalse(is_valid("(((({{{{[[[]]]}}}})))))"))

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
