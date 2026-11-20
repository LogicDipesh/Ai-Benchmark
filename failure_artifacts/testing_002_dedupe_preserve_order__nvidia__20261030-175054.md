# Failure artifact: testing_002_dedupe_preserve_order (testing)

- Provider: nvidia
- Model: nvidia/nemotron-3-ultra-550b-a55b
- Score: 0.0
- Status: failed
- Error: reference_impl_failed
- Latency (ms): 67388
- Written (UTC): 20261030-175054
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
import pytest
from solution import dedupe_preserve_order


class TestDedupePreserveOrder:
    def test_empty_list(self):
        assert dedupe_preserve_order([]) == []

    def test_single_element(self):
        assert dedupe_preserve_order([1]) == [1]
        assert dedupe_preserve_order(["a"]) == ["a"]
        assert dedupe_preserve_order([None]) == [None]

    def test_no_duplicates(self):
        assert dedupe_preserve_order([1, 2, 3]) == [1, 2, 3]
        assert dedupe_preserve_order(["a", "b", "c"]) == ["a", "b", "c"]
        assert dedupe_preserve_order([1, "a", 2.0, None]) == [1, "a", 2.0, None]

    def test_all_duplicates(self):
        assert dedupe_preserve_order([1, 1, 1, 1]) == [1]
        assert dedupe_preserve_order(["a", "a", "a"]) == ["a"]
        assert dedupe_preserve_order([None, None]) == [None]

    def test_duplicates_at_start(self):
        assert dedupe_preserve_order([1, 1, 2, 3]) == [1, 2, 3]
        assert dedupe_preserve_order(["a", "a", "b", "c"]) == ["a", "b", "c"]

    def test_duplicates_at_end(self):
        assert dedupe_preserve_order([1, 2, 3, 3]) == [1, 2, 3]
        assert dedupe_preserve_order([1, 2, 2, 2]) == [1, 2]

    def test_duplicates_in_middle(self):
        assert dedupe_preserve_order([1, 2, 2, 3, 4]) == [1, 2, 3, 4]
        assert dedupe_preserve_order([1, 2, 3, 2, 4]) == [1, 2, 3, 4]

    def test_multiple_duplicate_groups(self):
        assert dedupe_preserve_order([1, 2, 1, 3, 2, 4]) == [1, 2, 3, 4]
        assert dedupe_preserve_order(["a", "b", "a", "c", "b", "d"]) == ["a", "b", "c", "d"]

    def test_preserves_order_of_first_occurrence(self):
        result = dedupe_preserve_order([3, 1, 4, 1, 5, 9, 2, 6, 5])
        assert result == [3, 1, 4, 5, 9, 2, 6]
        assert result.index(1) < result.index(5)
        assert result.index(3) < result.index(1)

    def test_with_strings(self):
        assert dedupe_preserve_order(["apple", "banana", "apple", "cherry"]) == ["apple", "banana", "cherry"]
        assert dedupe_preserve_order(["", "a", "", "b"]) == ["", "a", "b"]

    def test_with_none_values(self):
        assert dedupe_preserve_order([None, 1, None, 2, None]) == [None, 1, 2]
        assert dedupe_preserve_order([1, None, 2, None, 3]) == [1, None, 2, 3]

    def test_with_mixed_types(self):
        assert dedupe_preserve_order([1, "1", 1.0, "1"]) == [1, "1", 1.0]
        assert dedupe_preserve_order([True, 1, False, 0]) == [True, 1, False, 0]

    def test_with_tuples(self):
        assert dedupe_preserve_order([(1, 2), (3, 4), (1, 2), (5, 6)]) == [(1, 2), (3, 4), (5, 6)]

    def test_with_booleans(self):
        assert dedupe_preserve_order([True, False, True, False]) == [True, False]
        assert dedupe_preserve_order([False, True, False]) == [False, True]

    def test_with_floats(self):
        assert dedupe_preserve_order([1.0, 2.0, 1.0, 3.0]) == [1.0, 2.0, 3.0]
        assert dedupe_preserve_order([float('nan'), 1.0, float('nan')]) == [float('nan'), 1.0, float('nan')]

    def test_large_list(self):
        large_list = list(range(1000)) + list(range(500))
        result = dedupe_preserve_order(large_list)
        assert result == list(range(1000))
        assert len(result) == 1000

    def test_returns_new_list(self):
        original = [1, 2, 2, 3]
        result = dedupe_preserve_order(original)
        assert result is not original
        assert original == [1, 2, 2, 3]

    def test_original_list_unchanged(self):
        original = [1, 2, 2, 3]
        dedupe_preserve_order(original)
        assert original == [1, 2, 2, 3]

    def test_with_custom_objects(self):
        class CustomObj:
            def __init__(self, value):
                self.value = value
            def __eq__(self, other):
                return isinstance(other, CustomObj) and self.value == other.value
            def __hash__(self):
                return hash(self.value)
            def __repr__(self):
                return f"CustomObj({self.value})"

        obj1 = CustomObj(1)
        obj2 = CustomObj(2)
        obj1_dup = CustomObj(1)
        result = dedupe_preserve_order([obj1, obj2, obj1_dup])
        assert len(result) == 2
        assert result[0].value == 1
        assert result[1].value == 2
```
```

## Extracted code, before import fix

```python
import pytest
from solution import dedupe_preserve_order


class TestDedupePreserveOrder:
    def test_empty_list(self):
        assert dedupe_preserve_order([]) == []

    def test_single_element(self):
        assert dedupe_preserve_order([1]) == [1]
        assert dedupe_preserve_order(["a"]) == ["a"]
        assert dedupe_preserve_order([None]) == [None]

    def test_no_duplicates(self):
        assert dedupe_preserve_order([1, 2, 3]) == [1, 2, 3]
        assert dedupe_preserve_order(["a", "b", "c"]) == ["a", "b", "c"]
        assert dedupe_preserve_order([1, "a", 2.0, None]) == [1, "a", 2.0, None]

    def test_all_duplicates(self):
        assert dedupe_preserve_order([1, 1, 1, 1]) == [1]
        assert dedupe_preserve_order(["a", "a", "a"]) == ["a"]
        assert dedupe_preserve_order([None, None]) == [None]

    def test_duplicates_at_start(self):
        assert dedupe_preserve_order([1, 1, 2, 3]) == [1, 2, 3]
        assert dedupe_preserve_order(["a", "a", "b", "c"]) == ["a", "b", "c"]

    def test_duplicates_at_end(self):
        assert dedupe_preserve_order([1, 2, 3, 3]) == [1, 2, 3]
        assert dedupe_preserve_order([1, 2, 2, 2]) == [1, 2]

    def test_duplicates_in_middle(self):
        assert dedupe_preserve_order([1, 2, 2, 3, 4]) == [1, 2, 3, 4]
        assert dedupe_preserve_order([1, 2, 3, 2, 4]) == [1, 2, 3, 4]

    def test_multiple_duplicate_groups(self):
        assert dedupe_preserve_order([1, 2, 1, 3, 2, 4]) == [1, 2, 3, 4]
        assert dedupe_preserve_order(["a", "b", "a", "c", "b", "d"]) == ["a", "b", "c", "d"]

    def test_preserves_order_of_first_occurrence(self):
        result = dedupe_preserve_order([3, 1, 4, 1, 5, 9, 2, 6, 5])
        assert result == [3, 1, 4, 5, 9, 2, 6]
        assert result.index(1) < result.index(5)
        assert result.index(3) < result.index(1)

    def test_with_strings(self):
        assert dedupe_preserve_order(["apple", "banana", "apple", "cherry"]) == ["apple", "banana", "cherry"]
        assert dedupe_preserve_order(["", "a", "", "b"]) == ["", "a", "b"]

    def test_with_none_values(self):
        assert dedupe_preserve_order([None, 1, None, 2, None]) == [None, 1, 2]
        assert dedupe_preserve_order([1, None, 2, None, 3]) == [1, None, 2, 3]

    def test_with_mixed_types(self):
        assert dedupe_preserve_order([1, "1", 1.0, "1"]) == [1, "1", 1.0]
        assert dedupe_preserve_order([True, 1, False, 0]) == [True, 1, False, 0]

    def test_with_tuples(self):
        assert dedupe_preserve_order([(1, 2), (3, 4), (1, 2), (5, 6)]) == [(1, 2), (3, 4), (5, 6)]

    def test_with_booleans(self):
        assert dedupe_preserve_order([True, False, True, False]) == [True, False]
        assert dedupe_preserve_order([False, True, False]) == [False, True]

    def test_with_floats(self):
        assert dedupe_preserve_order([1.0, 2.0, 1.0, 3.0]) == [1.0, 2.0, 3.0]
        assert dedupe_preserve_order([float('nan'), 1.0, float('nan')]) == [float('nan'), 1.0, float('nan')]

    def test_large_list(self):
        large_list = list(range(1000)) + list(range(500))
        result = dedupe_preserve_order(large_list)
        assert result == list(range(1000))
        assert len(result) == 1000

    def test_returns_new_list(self):
        original = [1, 2, 2, 3]
        result = dedupe_preserve_order(original)
        assert result is not original
        assert original == [1, 2, 2, 3]

    def test_original_list_unchanged(self):
        original = [1, 2, 2, 3]
        dedupe_preserve_order(original)
        assert original == [1, 2, 2, 3]

    def test_with_custom_objects(self):
        class CustomObj:
            def __init__(self, value):
                self.value = value
            def __eq__(self, other):
                return isinstance(other, CustomObj) and self.value == other.value
            def __hash__(self):
                return hash(self.value)
            def __repr__(self):
                return f"CustomObj({self.value})"

        obj1 = CustomObj(1)
        obj2 = CustomObj(2)
        obj1_dup = CustomObj(1)
        result = dedupe_preserve_order([obj1, obj2, obj1_dup])
        assert len(result) == 2
        assert result[0].value == 1
        assert result[1].value == 2
```

## Executed code

```python
import pytest
from solution import dedupe_preserve_order


class TestDedupePreserveOrder:
    def test_empty_list(self):
        assert dedupe_preserve_order([]) == []

    def test_single_element(self):
        assert dedupe_preserve_order([1]) == [1]
        assert dedupe_preserve_order(["a"]) == ["a"]
        assert dedupe_preserve_order([None]) == [None]

    def test_no_duplicates(self):
        assert dedupe_preserve_order([1, 2, 3]) == [1, 2, 3]
        assert dedupe_preserve_order(["a", "b", "c"]) == ["a", "b", "c"]
        assert dedupe_preserve_order([1, "a", 2.0, None]) == [1, "a", 2.0, None]

    def test_all_duplicates(self):
        assert dedupe_preserve_order([1, 1, 1, 1]) == [1]
        assert dedupe_preserve_order(["a", "a", "a"]) == ["a"]
        assert dedupe_preserve_order([None, None]) == [None]

    def test_duplicates_at_start(self):
        assert dedupe_preserve_order([1, 1, 2, 3]) == [1, 2, 3]
        assert dedupe_preserve_order(["a", "a", "b", "c"]) == ["a", "b", "c"]

    def test_duplicates_at_end(self):
        assert dedupe_preserve_order([1, 2, 3, 3]) == [1, 2, 3]
        assert dedupe_preserve_order([1, 2, 2, 2]) == [1, 2]

    def test_duplicates_in_middle(self):
        assert dedupe_preserve_order([1, 2, 2, 3, 4]) == [1, 2, 3, 4]
        assert dedupe_preserve_order([1, 2, 3, 2, 4]) == [1, 2, 3, 4]

    def test_multiple_duplicate_groups(self):
        assert dedupe_preserve_order([1, 2, 1, 3, 2, 4]) == [1, 2, 3, 4]
        assert dedupe_preserve_order(["a", "b", "a", "c", "b", "d"]) == ["a", "b", "c", "d"]

    def test_preserves_order_of_first_occurrence(self):
        result = dedupe_preserve_order([3, 1, 4, 1, 5, 9, 2, 6, 5])
        assert result == [3, 1, 4, 5, 9, 2, 6]
        assert result.index(1) < result.index(5)
        assert result.index(3) < result.index(1)

    def test_with_strings(self):
        assert dedupe_preserve_order(["apple", "banana", "apple", "cherry"]) == ["apple", "banana", "cherry"]
        assert dedupe_preserve_order(["", "a", "", "b"]) == ["", "a", "b"]

    def test_with_none_values(self):
        assert dedupe_preserve_order([None, 1, None, 2, None]) == [None, 1, 2]
        assert dedupe_preserve_order([1, None, 2, None, 3]) == [1, None, 2, 3]

    def test_with_mixed_types(self):
        assert dedupe_preserve_order([1, "1", 1.0, "1"]) == [1, "1", 1.0]
        assert dedupe_preserve_order([True, 1, False, 0]) == [True, 1, False, 0]

    def test_with_tuples(self):
        assert dedupe_preserve_order([(1, 2), (3, 4), (1, 2), (5, 6)]) == [(1, 2), (3, 4), (5, 6)]

    def test_with_booleans(self):
        assert dedupe_preserve_order([True, False, True, False]) == [True, False]
        assert dedupe_preserve_order([False, True, False]) == [False, True]

    def test_with_floats(self):
        assert dedupe_preserve_order([1.0, 2.0, 1.0, 3.0]) == [1.0, 2.0, 3.0]
        assert dedupe_preserve_order([float('nan'), 1.0, float('nan')]) == [float('nan'), 1.0, float('nan')]

    def test_large_list(self):
        large_list = list(range(1000)) + list(range(500))
        result = dedupe_preserve_order(large_list)
        assert result == list(range(1000))
        assert len(result) == 1000

    def test_returns_new_list(self):
        original = [1, 2, 2, 3]
        result = dedupe_preserve_order(original)
        assert result is not original
        assert original == [1, 2, 2, 3]

    def test_original_list_unchanged(self):
        original = [1, 2, 2, 3]
        dedupe_preserve_order(original)
        assert original == [1, 2, 2, 3]

    def test_with_custom_objects(self):
        class CustomObj:
            def __init__(self, value):
                self.value = value
            def __eq__(self, other):
                return isinstance(other, CustomObj) and self.value == other.value
            def __hash__(self):
                return hash(self.value)
            def __repr__(self):
                return f"CustomObj({self.value})"

        obj1 = CustomObj(1)
        obj2 = CustomObj(2)
        obj1_dup = CustomObj(1)
        result = dedupe_preserve_order([obj1, obj2, obj1_dup])
        assert len(result) == 2
        assert result[0].value == 1
        assert result[1].value == 2
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
