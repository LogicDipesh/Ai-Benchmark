# Failure artifact: testing_002_dedupe_preserve_order (testing)

- Provider: nvidia
- Model: nvidia/nemotron-3-ultra-550b-a55b
- Score: 0.0
- Status: failed
- Error: reference_impl_failed
- Latency (ms): 82411
- Written (UTC): 20261101-181923
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

    def test_all_unique_elements(self):
        assert dedupe_preserve_order([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]
        assert dedupe_preserve_order(["a", "b", "c"]) == ["a", "b", "c"]

    def test_all_duplicates(self):
        assert dedupe_preserve_order([1, 1, 1, 1]) == [1]
        assert dedupe_preserve_order(["x", "x", "x"]) == ["x"]

    def test_duplicates_preserve_first_occurrence_order(self):
        assert dedupe_preserve_order([3, 1, 2, 1, 3, 2]) == [3, 1, 2]
        assert dedupe_preserve_order(["b", "a", "b", "c", "a"]) == ["b", "a", "c"]

    def test_mixed_types_hashable(self):
        assert dedupe_preserve_order([1, "1", 1.0, True]) == [1, "1", 1.0]
        assert dedupe_preserve_order([None, 0, False, ""]) == [None, 0, False, ""]

    def test_none_values(self):
        assert dedupe_preserve_order([None, 1, None, 2, None]) == [None, 1, 2]
        assert dedupe_preserve_order([None, None, None]) == [None]

    def test_boolean_values(self):
        assert dedupe_preserve_order([True, False, True, False]) == [True, False]
        assert dedupe_preserve_order([False, True, False]) == [False, True]

    def test_numeric_types(self):
        assert dedupe_preserve_order([1, 1.0, 2, 2.0]) == [1, 2]
        assert dedupe_preserve_order([1.5, 1, 1.5, 2]) == [1.5, 1, 2]

    def test_string_case_sensitivity(self):
        assert dedupe_preserve_order(["a", "A", "a", "A"]) == ["a", "A"]
        assert dedupe_preserve_order(["Hello", "hello", "HELLO"]) == ["Hello", "hello", "HELLO"]

    def test_complex_objects_hashable(self):
        assert dedupe_preserve_order([(1, 2), (3, 4), (1, 2)]) == [(1, 2), (3, 4)]
        assert dedupe_preserve_order([frozenset([1, 2]), frozenset([3]), frozenset([1, 2])]) == [frozenset([1, 2]), frozenset([3])]

    def test_large_list_performance(self):
        large_list = list(range(1000)) + list(range(500))
        result = dedupe_preserve_order(large_list)
        assert result == list(range(1000))
        assert len(result) == 1000

    def test_unhashable_type_raises_error(self):
        with pytest.raises(TypeError):
            dedupe_preserve_order([[1], [2], [1]])
        with pytest.raises(TypeError):
            dedupe_preserve_order([{"a": 1}, {"b": 2}, {"a": 1}])

    def test_returns_new_list_not_same_object(self):
        original = [1, 2, 2, 3]
        result = dedupe_preserve_order(original)
        assert result is not original
        assert result == [1, 2, 3]

    def test_original_list_unmodified(self):
        original = [1, 2, 2, 3]
        original_copy = original.copy()
        dedupe_preserve_order(original)
        assert original == original_copy

    def test_custom_objects_with_hash_and_eq(self):
        class CustomObj:
            def __init__(self, value):
                self.value = value
            def __hash__(self):
                return hash(self.value)
            def __eq__(self, other):
                return isinstance(other, CustomObj) and self.value == other.value
            def __repr__(self):
                return f"CustomObj({self.value})"

        objs = [CustomObj(1), CustomObj(2), CustomObj(1), CustomObj(3)]
        result = dedupe_preserve_order(objs)
        assert len(result) == 3
        assert [o.value for o in result] == [1, 2, 3]

    def test_generator_input_consumed(self):
        def gen():
            yield 1
            yield 2
            yield 1
            yield 3
        assert dedupe_preserve_order(gen()) == [1, 2, 3]

    def test_tuple_input(self):
        assert dedupe_preserve_order((1, 2, 2, 3)) == [1, 2, 3]

    def test_set_input_order_not_guaranteed_but_function_works(self):
        input_set = {1, 2, 3}
        result = dedupe_preserve_order(input_set)
        assert set(result) == {1, 2, 3}
        assert len(result) == 3
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

    def test_all_unique_elements(self):
        assert dedupe_preserve_order([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]
        assert dedupe_preserve_order(["a", "b", "c"]) == ["a", "b", "c"]

    def test_all_duplicates(self):
        assert dedupe_preserve_order([1, 1, 1, 1]) == [1]
        assert dedupe_preserve_order(["x", "x", "x"]) == ["x"]

    def test_duplicates_preserve_first_occurrence_order(self):
        assert dedupe_preserve_order([3, 1, 2, 1, 3, 2]) == [3, 1, 2]
        assert dedupe_preserve_order(["b", "a", "b", "c", "a"]) == ["b", "a", "c"]

    def test_mixed_types_hashable(self):
        assert dedupe_preserve_order([1, "1", 1.0, True]) == [1, "1", 1.0]
        assert dedupe_preserve_order([None, 0, False, ""]) == [None, 0, False, ""]

    def test_none_values(self):
        assert dedupe_preserve_order([None, 1, None, 2, None]) == [None, 1, 2]
        assert dedupe_preserve_order([None, None, None]) == [None]

    def test_boolean_values(self):
        assert dedupe_preserve_order([True, False, True, False]) == [True, False]
        assert dedupe_preserve_order([False, True, False]) == [False, True]

    def test_numeric_types(self):
        assert dedupe_preserve_order([1, 1.0, 2, 2.0]) == [1, 2]
        assert dedupe_preserve_order([1.5, 1, 1.5, 2]) == [1.5, 1, 2]

    def test_string_case_sensitivity(self):
        assert dedupe_preserve_order(["a", "A", "a", "A"]) == ["a", "A"]
        assert dedupe_preserve_order(["Hello", "hello", "HELLO"]) == ["Hello", "hello", "HELLO"]

    def test_complex_objects_hashable(self):
        assert dedupe_preserve_order([(1, 2), (3, 4), (1, 2)]) == [(1, 2), (3, 4)]
        assert dedupe_preserve_order([frozenset([1, 2]), frozenset([3]), frozenset([1, 2])]) == [frozenset([1, 2]), frozenset([3])]

    def test_large_list_performance(self):
        large_list = list(range(1000)) + list(range(500))
        result = dedupe_preserve_order(large_list)
        assert result == list(range(1000))
        assert len(result) == 1000

    def test_unhashable_type_raises_error(self):
        with pytest.raises(TypeError):
            dedupe_preserve_order([[1], [2], [1]])
        with pytest.raises(TypeError):
            dedupe_preserve_order([{"a": 1}, {"b": 2}, {"a": 1}])

    def test_returns_new_list_not_same_object(self):
        original = [1, 2, 2, 3]
        result = dedupe_preserve_order(original)
        assert result is not original
        assert result == [1, 2, 3]

    def test_original_list_unmodified(self):
        original = [1, 2, 2, 3]
        original_copy = original.copy()
        dedupe_preserve_order(original)
        assert original == original_copy

    def test_custom_objects_with_hash_and_eq(self):
        class CustomObj:
            def __init__(self, value):
                self.value = value
            def __hash__(self):
                return hash(self.value)
            def __eq__(self, other):
                return isinstance(other, CustomObj) and self.value == other.value
            def __repr__(self):
                return f"CustomObj({self.value})"

        objs = [CustomObj(1), CustomObj(2), CustomObj(1), CustomObj(3)]
        result = dedupe_preserve_order(objs)
        assert len(result) == 3
        assert [o.value for o in result] == [1, 2, 3]

    def test_generator_input_consumed(self):
        def gen():
            yield 1
            yield 2
            yield 1
            yield 3
        assert dedupe_preserve_order(gen()) == [1, 2, 3]

    def test_tuple_input(self):
        assert dedupe_preserve_order((1, 2, 2, 3)) == [1, 2, 3]

    def test_set_input_order_not_guaranteed_but_function_works(self):
        input_set = {1, 2, 3}
        result = dedupe_preserve_order(input_set)
        assert set(result) == {1, 2, 3}
        assert len(result) == 3
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

    def test_all_unique_elements(self):
        assert dedupe_preserve_order([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]
        assert dedupe_preserve_order(["a", "b", "c"]) == ["a", "b", "c"]

    def test_all_duplicates(self):
        assert dedupe_preserve_order([1, 1, 1, 1]) == [1]
        assert dedupe_preserve_order(["x", "x", "x"]) == ["x"]

    def test_duplicates_preserve_first_occurrence_order(self):
        assert dedupe_preserve_order([3, 1, 2, 1, 3, 2]) == [3, 1, 2]
        assert dedupe_preserve_order(["b", "a", "b", "c", "a"]) == ["b", "a", "c"]

    def test_mixed_types_hashable(self):
        assert dedupe_preserve_order([1, "1", 1.0, True]) == [1, "1", 1.0]
        assert dedupe_preserve_order([None, 0, False, ""]) == [None, 0, False, ""]

    def test_none_values(self):
        assert dedupe_preserve_order([None, 1, None, 2, None]) == [None, 1, 2]
        assert dedupe_preserve_order([None, None, None]) == [None]

    def test_boolean_values(self):
        assert dedupe_preserve_order([True, False, True, False]) == [True, False]
        assert dedupe_preserve_order([False, True, False]) == [False, True]

    def test_numeric_types(self):
        assert dedupe_preserve_order([1, 1.0, 2, 2.0]) == [1, 2]
        assert dedupe_preserve_order([1.5, 1, 1.5, 2]) == [1.5, 1, 2]

    def test_string_case_sensitivity(self):
        assert dedupe_preserve_order(["a", "A", "a", "A"]) == ["a", "A"]
        assert dedupe_preserve_order(["Hello", "hello", "HELLO"]) == ["Hello", "hello", "HELLO"]

    def test_complex_objects_hashable(self):
        assert dedupe_preserve_order([(1, 2), (3, 4), (1, 2)]) == [(1, 2), (3, 4)]
        assert dedupe_preserve_order([frozenset([1, 2]), frozenset([3]), frozenset([1, 2])]) == [frozenset([1, 2]), frozenset([3])]

    def test_large_list_performance(self):
        large_list = list(range(1000)) + list(range(500))
        result = dedupe_preserve_order(large_list)
        assert result == list(range(1000))
        assert len(result) == 1000

    def test_unhashable_type_raises_error(self):
        with pytest.raises(TypeError):
            dedupe_preserve_order([[1], [2], [1]])
        with pytest.raises(TypeError):
            dedupe_preserve_order([{"a": 1}, {"b": 2}, {"a": 1}])

    def test_returns_new_list_not_same_object(self):
        original = [1, 2, 2, 3]
        result = dedupe_preserve_order(original)
        assert result is not original
        assert result == [1, 2, 3]

    def test_original_list_unmodified(self):
        original = [1, 2, 2, 3]
        original_copy = original.copy()
        dedupe_preserve_order(original)
        assert original == original_copy

    def test_custom_objects_with_hash_and_eq(self):
        class CustomObj:
            def __init__(self, value):
                self.value = value
            def __hash__(self):
                return hash(self.value)
            def __eq__(self, other):
                return isinstance(other, CustomObj) and self.value == other.value
            def __repr__(self):
                return f"CustomObj({self.value})"

        objs = [CustomObj(1), CustomObj(2), CustomObj(1), CustomObj(3)]
        result = dedupe_preserve_order(objs)
        assert len(result) == 3
        assert [o.value for o in result] == [1, 2, 3]

    def test_generator_input_consumed(self):
        def gen():
            yield 1
            yield 2
            yield 1
            yield 3
        assert dedupe_preserve_order(gen()) == [1, 2, 3]

    def test_tuple_input(self):
        assert dedupe_preserve_order((1, 2, 2, 3)) == [1, 2, 3]

    def test_set_input_order_not_guaranteed_but_function_works(self):
        input_set = {1, 2, 3}
        result = dedupe_preserve_order(input_set)
        assert set(result) == {1, 2, 3}
        assert len(result) == 3
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
