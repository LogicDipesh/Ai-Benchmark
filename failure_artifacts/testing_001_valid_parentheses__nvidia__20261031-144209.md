# Failure artifact: testing_001_valid_parentheses (testing)

- Provider: nvidia
- Model: nvidia/nemotron-3-ultra-550b-a55b
- Score: 0.0
- Status: failed
- Error: reference_impl_failed
- Latency (ms): 45850
- Written (UTC): 20261031-144209
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

    def test_single_opening_brackets(self):
        for bracket in "({[":
            with self.subTest(bracket=bracket):
                self.assertFalse(is_valid(bracket))

    def test_single_closing_brackets(self):
        for bracket in ")}]":
            with self.subTest(bracket=bracket):
                self.assertFalse(is_valid(bracket))

    def test_valid_pairs(self):
        valid_pairs = ["()", "[]", "{}"]
        for pair in valid_pairs:
            with self.subTest(pair=pair):
                self.assertTrue(is_valid(pair))

    def test_valid_nested(self):
        valid_nested = [
            "({[]})",
            "((()))",
            "[{()}]",
            "({})[]",
            "()[]{}",
            "([]){}",
        ]
        for s in valid_nested:
            with self.subTest(s=s):
                self.assertTrue(is_valid(s))

    def test_invalid_mismatched(self):
        invalid_mismatched = [
            "(]",
            "([)]",
            "({)}",
            "[(])",
            "{[}]",
            "({)}",
        ]
        for s in invalid_mismatched:
            with self.subTest(s=s):
                self.assertFalse(is_valid(s))

    def test_extra_opening_brackets(self):
        extra_opening = [
            "(((",
            "{{",
            "[[",
            "({[",
            "((()))(",
            "({[]}){",
        ]
        for s in extra_opening:
            with self.subTest(s=s):
                self.assertFalse(is_valid(s))

    def test_extra_closing_brackets(self):
        extra_closing = [
            ")))",
            "}}",
            "]]",
            ")}]",
            "())))",
            "({[]})}",
        ]
        for s in extra_closing:
            with self.subTest(s=s):
                self.assertFalse(is_valid(s))

    def test_non_bracket_characters(self):
        non_brackets = [
            "a",
            "()a",
            "a()",
            "(a)",
            "123",
            "()[]{}!",
            " ( ) ",
            "",
        ]
        for s in non_brackets:
            with self.subTest(s=s):
                if s == "":
                    self.assertTrue(is_valid(s))
                else:
                    self.assertFalse(is_valid(s))

    def test_long_valid_string(self):
        long_valid = "()" * 1000
        self.assertTrue(is_valid(long_valid))
        long_nested = "(" * 1000 + ")" * 1000
        self.assertTrue(is_valid(long_nested))

    def test_valid_sequential_mixed(self):
        self.assertTrue(is_valid("()[]{}"))
        self.assertTrue(is_valid("{}[]()"))
        self.assertTrue(is_valid("[]{()}"))

    def test_invalid_sequential_mixed(self):
        self.assertFalse(is_valid("(]"))
        self.assertFalse(is_valid("([)]"))
        self.assertFalse(is_valid("({)}"))

    def test_complex_valid(self):
        complex_valid = [
            "([]){()}[{}]",
            "(((((([[[[]]]))))))",
            "{[()()]}",
        ]
        for s in complex_valid:
            with self.subTest(s=s):
                self.assertTrue(is_valid(s))

    def test_complex_invalid(self):
        complex_invalid = [
            "([]){()}[{}](",
            "(((((([[[[]]])))))))",
            "{[()())]}",
        ]
        for s in complex_invalid:
            with self.subTest(s=s):
                self.assertFalse(is_valid(s))


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

    def test_single_opening_brackets(self):
        for bracket in "({[":
            with self.subTest(bracket=bracket):
                self.assertFalse(is_valid(bracket))

    def test_single_closing_brackets(self):
        for bracket in ")}]":
            with self.subTest(bracket=bracket):
                self.assertFalse(is_valid(bracket))

    def test_valid_pairs(self):
        valid_pairs = ["()", "[]", "{}"]
        for pair in valid_pairs:
            with self.subTest(pair=pair):
                self.assertTrue(is_valid(pair))

    def test_valid_nested(self):
        valid_nested = [
            "({[]})",
            "((()))",
            "[{()}]",
            "({})[]",
            "()[]{}",
            "([]){}",
        ]
        for s in valid_nested:
            with self.subTest(s=s):
                self.assertTrue(is_valid(s))

    def test_invalid_mismatched(self):
        invalid_mismatched = [
            "(]",
            "([)]",
            "({)}",
            "[(])",
            "{[}]",
            "({)}",
        ]
        for s in invalid_mismatched:
            with self.subTest(s=s):
                self.assertFalse(is_valid(s))

    def test_extra_opening_brackets(self):
        extra_opening = [
            "(((",
            "{{",
            "[[",
            "({[",
            "((()))(",
            "({[]}){",
        ]
        for s in extra_opening:
            with self.subTest(s=s):
                self.assertFalse(is_valid(s))

    def test_extra_closing_brackets(self):
        extra_closing = [
            ")))",
            "}}",
            "]]",
            ")}]",
            "())))",
            "({[]})}",
        ]
        for s in extra_closing:
            with self.subTest(s=s):
                self.assertFalse(is_valid(s))

    def test_non_bracket_characters(self):
        non_brackets = [
            "a",
            "()a",
            "a()",
            "(a)",
            "123",
            "()[]{}!",
            " ( ) ",
            "",
        ]
        for s in non_brackets:
            with self.subTest(s=s):
                if s == "":
                    self.assertTrue(is_valid(s))
                else:
                    self.assertFalse(is_valid(s))

    def test_long_valid_string(self):
        long_valid = "()" * 1000
        self.assertTrue(is_valid(long_valid))
        long_nested = "(" * 1000 + ")" * 1000
        self.assertTrue(is_valid(long_nested))

    def test_valid_sequential_mixed(self):
        self.assertTrue(is_valid("()[]{}"))
        self.assertTrue(is_valid("{}[]()"))
        self.assertTrue(is_valid("[]{()}"))

    def test_invalid_sequential_mixed(self):
        self.assertFalse(is_valid("(]"))
        self.assertFalse(is_valid("([)]"))
        self.assertFalse(is_valid("({)}"))

    def test_complex_valid(self):
        complex_valid = [
            "([]){()}[{}]",
            "(((((([[[[]]]))))))",
            "{[()()]}",
        ]
        for s in complex_valid:
            with self.subTest(s=s):
                self.assertTrue(is_valid(s))

    def test_complex_invalid(self):
        complex_invalid = [
            "([]){()}[{}](",
            "(((((([[[[]]])))))))",
            "{[()())]}",
        ]
        for s in complex_invalid:
            with self.subTest(s=s):
                self.assertFalse(is_valid(s))


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

    def test_single_opening_brackets(self):
        for bracket in "({[":
            with self.subTest(bracket=bracket):
                self.assertFalse(is_valid(bracket))

    def test_single_closing_brackets(self):
        for bracket in ")}]":
            with self.subTest(bracket=bracket):
                self.assertFalse(is_valid(bracket))

    def test_valid_pairs(self):
        valid_pairs = ["()", "[]", "{}"]
        for pair in valid_pairs:
            with self.subTest(pair=pair):
                self.assertTrue(is_valid(pair))

    def test_valid_nested(self):
        valid_nested = [
            "({[]})",
            "((()))",
            "[{()}]",
            "({})[]",
            "()[]{}",
            "([]){}",
        ]
        for s in valid_nested:
            with self.subTest(s=s):
                self.assertTrue(is_valid(s))

    def test_invalid_mismatched(self):
        invalid_mismatched = [
            "(]",
            "([)]",
            "({)}",
            "[(])",
            "{[}]",
            "({)}",
        ]
        for s in invalid_mismatched:
            with self.subTest(s=s):
                self.assertFalse(is_valid(s))

    def test_extra_opening_brackets(self):
        extra_opening = [
            "(((",
            "{{",
            "[[",
            "({[",
            "((()))(",
            "({[]}){",
        ]
        for s in extra_opening:
            with self.subTest(s=s):
                self.assertFalse(is_valid(s))

    def test_extra_closing_brackets(self):
        extra_closing = [
            ")))",
            "}}",
            "]]",
            ")}]",
            "())))",
            "({[]})}",
        ]
        for s in extra_closing:
            with self.subTest(s=s):
                self.assertFalse(is_valid(s))

    def test_non_bracket_characters(self):
        non_brackets = [
            "a",
            "()a",
            "a()",
            "(a)",
            "123",
            "()[]{}!",
            " ( ) ",
            "",
        ]
        for s in non_brackets:
            with self.subTest(s=s):
                if s == "":
                    self.assertTrue(is_valid(s))
                else:
                    self.assertFalse(is_valid(s))

    def test_long_valid_string(self):
        long_valid = "()" * 1000
        self.assertTrue(is_valid(long_valid))
        long_nested = "(" * 1000 + ")" * 1000
        self.assertTrue(is_valid(long_nested))

    def test_valid_sequential_mixed(self):
        self.assertTrue(is_valid("()[]{}"))
        self.assertTrue(is_valid("{}[]()"))
        self.assertTrue(is_valid("[]{()}"))

    def test_invalid_sequential_mixed(self):
        self.assertFalse(is_valid("(]"))
        self.assertFalse(is_valid("([)]"))
        self.assertFalse(is_valid("({)}"))

    def test_complex_valid(self):
        complex_valid = [
            "([]){()}[{}]",
            "(((((([[[[]]]))))))",
            "{[()()]}",
        ]
        for s in complex_valid:
            with self.subTest(s=s):
                self.assertTrue(is_valid(s))

    def test_complex_invalid(self):
        complex_invalid = [
            "([]){()}[{}](",
            "(((((([[[[]]])))))))",
            "{[()())]}",
        ]
        for s in complex_invalid:
            with self.subTest(s=s):
                self.assertFalse(is_valid(s))


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
