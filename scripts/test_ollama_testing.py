from aibenchmark.sandbox import run_mutant_tests_sandboxed
from aibenchmark.categories.testing import list_testing_problems

p = list_testing_problems()[0]
test_code = """
import unittest
from solution import is_valid

class TestIsValid(unittest.TestCase):
    def test_empty_string(self):
        self.assertTrue(is_valid(""))

    def test_single_char(self):
        self.assertFalse(is_valid("("))
        self.assertFalse(is_valid(")"))
        self.assertFalse(is_valid("{"))
        self.assertFalse(is_valid("}"))
        self.assertFalse(is_valid("["))

    def test_balanced_parentheses(self):
        self.assertTrue(is_valid("()"))
        self.assertTrue(is_valid("[]"))
        self.assertTrue(is_valid("{}"))

    def test_multiple_pairs(self):
        self.assertTrue(is_valid("()[]{}"))
        self.assertTrue(is_valid("{}[]()"))

    def test_mismatched_closing_bracket(self):
        self.assertFalse(is_valid("([)]"))

    def test_unmatched_opening_bracket(self):
        self.assertFalse(is_valid("[("))

    def test_nested_parentheses(self):
        self.assertTrue(is_valid("(())"))
        self.assertTrue(is_valid("(()())"))

    def test_multiple_types_of_brackets(self):
        self.assertTrue(is_valid("{[()]}"))
        self.assertTrue(is_valid("({[]})"))

    def test_mismatched_brackets(self):
        self.assertFalse(is_valid("{[(])}"))
"""
ref_impl = p['reference_implementation']
mutants = p['mutants']
score, error = run_mutant_tests_sandboxed('problems/testing', test_code, ref_impl, mutants)
print('Score:', score, 'Error:', error)