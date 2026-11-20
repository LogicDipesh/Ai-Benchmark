# Failure artifact: testing_002_dedupe_preserve_order (testing)

- Provider: openrouter
- Model: cohere/north-mini-code:free
- Score: 0.0
- Status: failed
- Error: reference_impl_failed
- Latency (ms): 18258
- Written (UTC): 20261031-174417
- Run id: not recorded (evaluators do not receive one); match by timestamp + problem + provider.

## Prompt sent

```
Write comprehensive tests for the following function:

def dedupe_preserve_order(lst):
    seen = set()
    result = []
    for item in lst:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

The function removes duplicates from a list while preserving
the order of first occurrence. Write tests covering edge cases.
Output only the test code in a Python code block.


Return ONLY one Python code block containing the test code and nothing else. No explanation, no preamble, no text outside the block. Import the function from 'solution' module (e.g., 'from solution import is_valid').
```

## Raw model response

```
```python
import unittest
from solution import dedupe_preserve_order

class TestDedupePreserveOrder(unittest.TestCase):
    def test_empty_list(self):
        self.assertEqual(dedupe_preserve_order([]), [])

    def test_single_element(self):
        self.assertEqual(dedupe_preserve_order([1]), [1])

    def test_no_duplicates(self):
        self.assertEqual(dedupe_preserve_order([1, 2, 3, 4]), [1, 2, 3, 4])

    def test_all_duplicates(self):
        self.assertEqual(dedupe_preserve_order([5, 5, 5, 5]), [5])

    def test_mixed_duplicates(self):
        self.assertEqual(dedupe_preserve_order([1, 2, 3, 2, 1, 4, 5, 4]), [1, 2, 3, 4, 5])

    def test_preserve_order_first_occurrence(self):
        self.assertEqual(dedupe_preserve_order(['a', 'b', 'a', 'c', 'b', 'a']), ['a', 'b', 'c'])

    def test_different_types(self):
        self.assertEqual(dedupe_preserve_order([1, '1', 2.0, (1, 2), None, True]), [1, '1', 2.0, (1, 2), None, True])

    def test_input_not_modified(self):
        original = [1, 2, 3, 2, 1]
        result = dedupe_preserve_order(original)
        self.assertEqual(original, [1, 2, 3, 2, 1])

    def test_result_is_list(self):
        result = dedupe_preserve_order([1, 2, 2])
        self.assertIsInstance(result, list)

    def test_unhashable_item(self):
        with self.assertRaises(TypeError):
            dedupe_preserve_order([[1, 2], [3, 4]])

if __name__ == '__main__':
    unittest.main()
```
```

## Extracted code, before import fix

```python
import unittest
from solution import dedupe_preserve_order

class TestDedupePreserveOrder(unittest.TestCase):
    def test_empty_list(self):
        self.assertEqual(dedupe_preserve_order([]), [])

    def test_single_element(self):
        self.assertEqual(dedupe_preserve_order([1]), [1])

    def test_no_duplicates(self):
        self.assertEqual(dedupe_preserve_order([1, 2, 3, 4]), [1, 2, 3, 4])

    def test_all_duplicates(self):
        self.assertEqual(dedupe_preserve_order([5, 5, 5, 5]), [5])

    def test_mixed_duplicates(self):
        self.assertEqual(dedupe_preserve_order([1, 2, 3, 2, 1, 4, 5, 4]), [1, 2, 3, 4, 5])

    def test_preserve_order_first_occurrence(self):
        self.assertEqual(dedupe_preserve_order(['a', 'b', 'a', 'c', 'b', 'a']), ['a', 'b', 'c'])

    def test_different_types(self):
        self.assertEqual(dedupe_preserve_order([1, '1', 2.0, (1, 2), None, True]), [1, '1', 2.0, (1, 2), None, True])

    def test_input_not_modified(self):
        original = [1, 2, 3, 2, 1]
        result = dedupe_preserve_order(original)
        self.assertEqual(original, [1, 2, 3, 2, 1])

    def test_result_is_list(self):
        result = dedupe_preserve_order([1, 2, 2])
        self.assertIsInstance(result, list)

    def test_unhashable_item(self):
        with self.assertRaises(TypeError):
            dedupe_preserve_order([[1, 2], [3, 4]])

if __name__ == '__main__':
    unittest.main()
```

## Executed code

```python
import unittest
from solution import dedupe_preserve_order

class TestDedupePreserveOrder(unittest.TestCase):
    def test_empty_list(self):
        self.assertEqual(dedupe_preserve_order([]), [])

    def test_single_element(self):
        self.assertEqual(dedupe_preserve_order([1]), [1])

    def test_no_duplicates(self):
        self.assertEqual(dedupe_preserve_order([1, 2, 3, 4]), [1, 2, 3, 4])

    def test_all_duplicates(self):
        self.assertEqual(dedupe_preserve_order([5, 5, 5, 5]), [5])

    def test_mixed_duplicates(self):
        self.assertEqual(dedupe_preserve_order([1, 2, 3, 2, 1, 4, 5, 4]), [1, 2, 3, 4, 5])

    def test_preserve_order_first_occurrence(self):
        self.assertEqual(dedupe_preserve_order(['a', 'b', 'a', 'c', 'b', 'a']), ['a', 'b', 'c'])

    def test_different_types(self):
        self.assertEqual(dedupe_preserve_order([1, '1', 2.0, (1, 2), None, True]), [1, '1', 2.0, (1, 2), None, True])

    def test_input_not_modified(self):
        original = [1, 2, 3, 2, 1]
        result = dedupe_preserve_order(original)
        self.assertEqual(original, [1, 2, 3, 2, 1])

    def test_result_is_list(self):
        result = dedupe_preserve_order([1, 2, 2])
        self.assertIsInstance(result, list)

    def test_unhashable_item(self):
        with self.assertRaises(TypeError):
            dedupe_preserve_order([[1, 2], [3, 4]])

if __name__ == '__main__':
    unittest.main()
```

## Reference implementation (what the suite was tested against)

```python
def dedupe_preserve_order(lst):
    seen = set()
    result = []
    for item in lst:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

```

## Mutants in this problem: mutant_001, mutant_002, mutant_003

## How to reproduce the detail

The bench ran this suite sandboxed: the executed test code was saved as test_generated.py, the reference as solution.py in a solution_dir, and pytest ran with `-v --tb=short` (10 s timeout, Python-level network blocked). First the suite must pass cleanly against the reference, else the row is reference_impl_failed; then each mutant's code replaces solution.py and the suite must fail it to count a kill. To see which mutants survived, re-run the suite above against the reference and then against each mutant from the problem YAML.

Diagnostic only: this file changes no score, no row, and no database entry.
