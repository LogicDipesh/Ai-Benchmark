# Failure artifact: testing_002_dedupe_preserve_order (testing)

- Provider: nvidia
- Model: nvidia/nemotron-3-ultra-550b-a55b
- Score: 0.0
- Status: failed
- Error: reference_impl_failed
- Latency (ms): 14036
- Written (UTC): 20261102-101640
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
        self.assertEqual(dedupe_preserve_order(["a"]), ["a"])
        self.assertEqual(dedupe_preserve_order([None]), [None])
    
    def test_no_duplicates(self):
        self.assertEqual(dedupe_preserve_order([1, 2, 3]), [1, 2, 3])
        self.assertEqual(dedupe_preserve_order(["a", "b", "c"]), ["a", "b", "c"])
        self.assertEqual(dedupe_preserve_order([1, "a", 2.5, None]), [1, "a", 2.5, None])
    
    def test_all_duplicates(self):
        self.assertEqual(dedupe_preserve_order([1, 1, 1]), [1])
        self.assertEqual(dedupe_preserve_order(["a", "a", "a", "a"]), ["a"])
        self.assertEqual(dedupe_preserve_order([None, None]), [None])
    
    def test_duplicates_at_start(self):
        self.assertEqual(dedupe_preserve_order([1, 1, 2, 3]), [1, 2, 3])
        self.assertEqual(dedupe_preserve_order([5, 5, 5, 1, 2]), [5, 1, 2])
    
    def test_duplicates_at_end(self):
        self.assertEqual(dedupe_preserve_order([1, 2, 3, 3]), [1, 2, 3])
        self.assertEqual(dedupe_preserve_order([1, 2, 3, 3, 3, 3]), [1, 2, 3])
    
    def test_duplicates_in_middle(self):
        self.assertEqual(dedupe_preserve_order([1, 2, 2, 3]), [1, 2, 3])
        self.assertEqual(dedupe_preserve_order([1, 2, 2, 2, 3, 3, 4]), [1, 2, 3, 4])
    
    def test_order_preservation(self):
        input_list = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
        expected = [3, 1, 4, 5, 9, 2, 6]
        self.assertEqual(dedupe_preserve_order(input_list), expected)
    
    def test_mixed_types(self):
        input_list = [1, "1", 1.0, "1", 1, 2, "2", 2.0]
        expected = [1, "1", 1.0, 2, "2", 2.0]
        self.assertEqual(dedupe_preserve_order(input_list), expected)
    
    def test_strings(self):
        self.assertEqual(dedupe_preserve_order(["apple", "banana", "apple", "cherry"]), 
                         ["apple", "banana", "cherry"])
        self.assertEqual(dedupe_preserve_order(["a", "b", "a", "c", "b"]), 
                         ["a", "b", "c"])
    
    def test_none_values(self):
        self.assertEqual(dedupe_preserve_order([None, 1, None, 2, None]), [None, 1, 2])
        self.assertEqual(dedupe_preserve_order([1, None, None, 2]), [1, None, 2])
    
    def test_boolean_values(self):
        self.assertEqual(dedupe_preserve_order([True, False, True, False]), [True, False])
        self.assertEqual(dedupe_preserve_order([True, 1, False, 0]), [True, False])
    
    def test_negative_numbers(self):
        self.assertEqual(dedupe_preserve_order([-1, -2, -1, -3, -2]), [-1, -2, -3])
        self.assertEqual(dedupe_preserve_order([0, -0, 0.0, -0.0]), [0])
    
    def test_floats(self):
        self.assertEqual(dedupe_preserve_order([1.5, 2.5, 1.5, 3.5]), [1.5, 2.5, 3.5])
        self.assertEqual(dedupe_preserve_order([1.0, 1, 1.00]), [1.0])
    
    def test_tuples_as_elements(self):
        input_list = [(1, 2), (3, 4), (1, 2), (5, 6)]
        expected = [(1, 2), (3, 4), (5, 6)]
        self.assertEqual(dedupe_preserve_order(input_list), expected)
    
    def test_large_list(self):
        input_list = list(range(1000)) + list(range(500))
        expected = list(range(1000))
        self.assertEqual(dedupe_preserve_order(input_list), expected)
    
    def test_return_type_is_list(self):
        result = dedupe_preserve_order([1, 2, 2, 3])
        self.assertIsInstance(result, list)
    
    def test_original_list_unmodified(self):
        original = [1, 2, 2, 3, 1]
        original_copy = original.copy()
        dedupe_preserve_order(original)
        self.assertEqual(original, original_copy)
    
    def test_custom_objects_with_eq_hash(self):
        class Item:
            def __init__(self, value):
                self.value = value
            def __eq__(self, other):
                return isinstance(other, Item) and self.value == other.value
            def __hash__(self):
                return hash(self.value)
            def __repr__(self):
                return f"Item({self.value})"
        
        items = [Item(1), Item(2), Item(1), Item(3)]
        result = dedupe_preserve_order(items)
        self.assertEqual(len(result), 3)
        self.assertEqual([item.value for item in result], [1, 2, 3])


if __name__ == "__main__":
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
        self.assertEqual(dedupe_preserve_order(["a"]), ["a"])
        self.assertEqual(dedupe_preserve_order([None]), [None])
    
    def test_no_duplicates(self):
        self.assertEqual(dedupe_preserve_order([1, 2, 3]), [1, 2, 3])
        self.assertEqual(dedupe_preserve_order(["a", "b", "c"]), ["a", "b", "c"])
        self.assertEqual(dedupe_preserve_order([1, "a", 2.5, None]), [1, "a", 2.5, None])
    
    def test_all_duplicates(self):
        self.assertEqual(dedupe_preserve_order([1, 1, 1]), [1])
        self.assertEqual(dedupe_preserve_order(["a", "a", "a", "a"]), ["a"])
        self.assertEqual(dedupe_preserve_order([None, None]), [None])
    
    def test_duplicates_at_start(self):
        self.assertEqual(dedupe_preserve_order([1, 1, 2, 3]), [1, 2, 3])
        self.assertEqual(dedupe_preserve_order([5, 5, 5, 1, 2]), [5, 1, 2])
    
    def test_duplicates_at_end(self):
        self.assertEqual(dedupe_preserve_order([1, 2, 3, 3]), [1, 2, 3])
        self.assertEqual(dedupe_preserve_order([1, 2, 3, 3, 3, 3]), [1, 2, 3])
    
    def test_duplicates_in_middle(self):
        self.assertEqual(dedupe_preserve_order([1, 2, 2, 3]), [1, 2, 3])
        self.assertEqual(dedupe_preserve_order([1, 2, 2, 2, 3, 3, 4]), [1, 2, 3, 4])
    
    def test_order_preservation(self):
        input_list = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
        expected = [3, 1, 4, 5, 9, 2, 6]
        self.assertEqual(dedupe_preserve_order(input_list), expected)
    
    def test_mixed_types(self):
        input_list = [1, "1", 1.0, "1", 1, 2, "2", 2.0]
        expected = [1, "1", 1.0, 2, "2", 2.0]
        self.assertEqual(dedupe_preserve_order(input_list), expected)
    
    def test_strings(self):
        self.assertEqual(dedupe_preserve_order(["apple", "banana", "apple", "cherry"]), 
                         ["apple", "banana", "cherry"])
        self.assertEqual(dedupe_preserve_order(["a", "b", "a", "c", "b"]), 
                         ["a", "b", "c"])
    
    def test_none_values(self):
        self.assertEqual(dedupe_preserve_order([None, 1, None, 2, None]), [None, 1, 2])
        self.assertEqual(dedupe_preserve_order([1, None, None, 2]), [1, None, 2])
    
    def test_boolean_values(self):
        self.assertEqual(dedupe_preserve_order([True, False, True, False]), [True, False])
        self.assertEqual(dedupe_preserve_order([True, 1, False, 0]), [True, False])
    
    def test_negative_numbers(self):
        self.assertEqual(dedupe_preserve_order([-1, -2, -1, -3, -2]), [-1, -2, -3])
        self.assertEqual(dedupe_preserve_order([0, -0, 0.0, -0.0]), [0])
    
    def test_floats(self):
        self.assertEqual(dedupe_preserve_order([1.5, 2.5, 1.5, 3.5]), [1.5, 2.5, 3.5])
        self.assertEqual(dedupe_preserve_order([1.0, 1, 1.00]), [1.0])
    
    def test_tuples_as_elements(self):
        input_list = [(1, 2), (3, 4), (1, 2), (5, 6)]
        expected = [(1, 2), (3, 4), (5, 6)]
        self.assertEqual(dedupe_preserve_order(input_list), expected)
    
    def test_large_list(self):
        input_list = list(range(1000)) + list(range(500))
        expected = list(range(1000))
        self.assertEqual(dedupe_preserve_order(input_list), expected)
    
    def test_return_type_is_list(self):
        result = dedupe_preserve_order([1, 2, 2, 3])
        self.assertIsInstance(result, list)
    
    def test_original_list_unmodified(self):
        original = [1, 2, 2, 3, 1]
        original_copy = original.copy()
        dedupe_preserve_order(original)
        self.assertEqual(original, original_copy)
    
    def test_custom_objects_with_eq_hash(self):
        class Item:
            def __init__(self, value):
                self.value = value
            def __eq__(self, other):
                return isinstance(other, Item) and self.value == other.value
            def __hash__(self):
                return hash(self.value)
            def __repr__(self):
                return f"Item({self.value})"
        
        items = [Item(1), Item(2), Item(1), Item(3)]
        result = dedupe_preserve_order(items)
        self.assertEqual(len(result), 3)
        self.assertEqual([item.value for item in result], [1, 2, 3])


if __name__ == "__main__":
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
        self.assertEqual(dedupe_preserve_order(["a"]), ["a"])
        self.assertEqual(dedupe_preserve_order([None]), [None])
    
    def test_no_duplicates(self):
        self.assertEqual(dedupe_preserve_order([1, 2, 3]), [1, 2, 3])
        self.assertEqual(dedupe_preserve_order(["a", "b", "c"]), ["a", "b", "c"])
        self.assertEqual(dedupe_preserve_order([1, "a", 2.5, None]), [1, "a", 2.5, None])
    
    def test_all_duplicates(self):
        self.assertEqual(dedupe_preserve_order([1, 1, 1]), [1])
        self.assertEqual(dedupe_preserve_order(["a", "a", "a", "a"]), ["a"])
        self.assertEqual(dedupe_preserve_order([None, None]), [None])
    
    def test_duplicates_at_start(self):
        self.assertEqual(dedupe_preserve_order([1, 1, 2, 3]), [1, 2, 3])
        self.assertEqual(dedupe_preserve_order([5, 5, 5, 1, 2]), [5, 1, 2])
    
    def test_duplicates_at_end(self):
        self.assertEqual(dedupe_preserve_order([1, 2, 3, 3]), [1, 2, 3])
        self.assertEqual(dedupe_preserve_order([1, 2, 3, 3, 3, 3]), [1, 2, 3])
    
    def test_duplicates_in_middle(self):
        self.assertEqual(dedupe_preserve_order([1, 2, 2, 3]), [1, 2, 3])
        self.assertEqual(dedupe_preserve_order([1, 2, 2, 2, 3, 3, 4]), [1, 2, 3, 4])
    
    def test_order_preservation(self):
        input_list = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
        expected = [3, 1, 4, 5, 9, 2, 6]
        self.assertEqual(dedupe_preserve_order(input_list), expected)
    
    def test_mixed_types(self):
        input_list = [1, "1", 1.0, "1", 1, 2, "2", 2.0]
        expected = [1, "1", 1.0, 2, "2", 2.0]
        self.assertEqual(dedupe_preserve_order(input_list), expected)
    
    def test_strings(self):
        self.assertEqual(dedupe_preserve_order(["apple", "banana", "apple", "cherry"]), 
                         ["apple", "banana", "cherry"])
        self.assertEqual(dedupe_preserve_order(["a", "b", "a", "c", "b"]), 
                         ["a", "b", "c"])
    
    def test_none_values(self):
        self.assertEqual(dedupe_preserve_order([None, 1, None, 2, None]), [None, 1, 2])
        self.assertEqual(dedupe_preserve_order([1, None, None, 2]), [1, None, 2])
    
    def test_boolean_values(self):
        self.assertEqual(dedupe_preserve_order([True, False, True, False]), [True, False])
        self.assertEqual(dedupe_preserve_order([True, 1, False, 0]), [True, False])
    
    def test_negative_numbers(self):
        self.assertEqual(dedupe_preserve_order([-1, -2, -1, -3, -2]), [-1, -2, -3])
        self.assertEqual(dedupe_preserve_order([0, -0, 0.0, -0.0]), [0])
    
    def test_floats(self):
        self.assertEqual(dedupe_preserve_order([1.5, 2.5, 1.5, 3.5]), [1.5, 2.5, 3.5])
        self.assertEqual(dedupe_preserve_order([1.0, 1, 1.00]), [1.0])
    
    def test_tuples_as_elements(self):
        input_list = [(1, 2), (3, 4), (1, 2), (5, 6)]
        expected = [(1, 2), (3, 4), (5, 6)]
        self.assertEqual(dedupe_preserve_order(input_list), expected)
    
    def test_large_list(self):
        input_list = list(range(1000)) + list(range(500))
        expected = list(range(1000))
        self.assertEqual(dedupe_preserve_order(input_list), expected)
    
    def test_return_type_is_list(self):
        result = dedupe_preserve_order([1, 2, 2, 3])
        self.assertIsInstance(result, list)
    
    def test_original_list_unmodified(self):
        original = [1, 2, 2, 3, 1]
        original_copy = original.copy()
        dedupe_preserve_order(original)
        self.assertEqual(original, original_copy)
    
    def test_custom_objects_with_eq_hash(self):
        class Item:
            def __init__(self, value):
                self.value = value
            def __eq__(self, other):
                return isinstance(other, Item) and self.value == other.value
            def __hash__(self):
                return hash(self.value)
            def __repr__(self):
                return f"Item({self.value})"
        
        items = [Item(1), Item(2), Item(1), Item(3)]
        result = dedupe_preserve_order(items)
        self.assertEqual(len(result), 3)
        self.assertEqual([item.value for item in result], [1, 2, 3])


if __name__ == "__main__":
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
