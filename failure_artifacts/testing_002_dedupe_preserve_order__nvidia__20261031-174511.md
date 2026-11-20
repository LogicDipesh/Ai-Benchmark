# Failure artifact: testing_002_dedupe_preserve_order (testing)

- Provider: nvidia
- Model: nvidia/nemotron-3-ultra-550b-a55b
- Score: 0.0
- Status: failed
- Error: reference_impl_failed
- Latency (ms): 63500
- Written (UTC): 20261031-174511
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

    def test_all_duplicates(self):
        assert dedupe_preserve_order([1, 1, 1]) == [1]
        assert dedupe_preserve_order(["a", "a", "a", "a"]) == ["a"]

    def test_duplicates_at_start(self):
        assert dedupe_preserve_order([1, 1, 2, 3]) == [1, 2, 3]
        assert dedupe_preserve_order([1, 1, 1, 2, 2, 3]) == [1, 2, 3]

    def test_duplicates_at_end(self):
        assert dedupe_preserve_order([1, 2, 3, 3]) == [1, 2, 3]
        assert dedupe_preserve_order([1, 2, 2, 2]) == [1, 2]

    def test_duplicates_in_middle(self):
        assert dedupe_preserve_order([1, 2, 2, 3]) == [1, 2, 3]
        assert dedupe_preserve_order([1, 2, 2, 2, 3, 3, 4]) == [1, 2, 3, 4]

    def test_preserves_order_of_first_occurrence(self):
        assert dedupe_preserve_order([3, 1, 2, 1, 3, 2]) == [3, 1, 2]
        assert dedupe_preserve_order(["c", "a", "b", "a", "c"]) == ["c", "a", "b"]

    def test_mixed_types(self):
        assert dedupe_preserve_order([1, "1", 1.0, "1"]) == [1, "1", 1.0]
        assert dedupe_preserve_order([True, 1, False, 0]) == [True, 1, False, 0]

    def test_none_values(self):
        assert dedupe_preserve_order([None, 1, None, 2, None]) == [None, 1, 2]
        assert dedupe_preserve_order([None, None, None]) == [None]

    def test_complex_objects(self):
        assert dedupe_preserve_order([[1], [2], [1], [3]]) == [[1], [2], [3]]
        assert dedupe_preserve_order([{"a": 1}, {"b": 2}, {"a": 1}]) == [{"a": 1}, {"b": 2}]

    def test_tuples(self):
        assert dedupe_preserve_order([(1, 2), (3, 4), (1, 2), (5, 6)]) == [(1, 2), (3, 4), (5, 6)]

    def test_strings(self):
        assert dedupe_preserve_order("hello") == ["h", "e", "l", "o"]
        assert dedupe_preserve_order(["hello", "world", "hello"]) == ["hello", "world"]

    def test_large_list(self):
        lst = list(range(1000)) + list(range(1000))
        result = dedupe_preserve_order(lst)
        assert result == list(range(1000))
        assert len(result) == 1000

    def test_returns_new_list(self):
        original = [1, 2, 2, 3]
        result = dedupe_preserve_order(original)
        assert result is not original
        result.append(99)
        assert 99 not in original

    def test_original_list_unchanged(self):
        original = [1, 2, 2, 3]
        original_copy = original.copy()
        dedupe_preserve_order(original)
        assert original == original_copy

    def test_custom_objects_with_hash(self):
        class Custom:
            def __init__(self, value):
                self.value = value
            def __hash__(self):
                return hash(self.value)
            def __eq__(self, other):
                return isinstance(other, Custom) and self.value == other.value
            def __repr__(self):
                return f"Custom({self.value})"

        objs = [Custom(1), Custom(2), Custom(1), Custom(3)]
        result = dedupe_preserve_order(objs)
        assert len(result) == 3
        assert [o.value for o in result] == [1, 2, 3]

    def test_generator_input(self):
        def gen():
            yield 1
            yield 2
            yield 2
            yield 3
        assert dedupe_preserve_order(gen()) == [1, 2, 3]

    def test_iterator_input(self):
        assert dedupe_preserve_order(iter([1, 2, 2, 3])) == [1, 2, 3]

    def test_boolean_and_int_distinction(self):
        assert dedupe_preserve_order([True, 1, False, 0]) == [True, 1, False, 0]
        assert dedupe_preserve_order([False, 0, True, 1]) == [False, 0, True, 1]

    def test_unhashable_types_raises_error(self):
        with pytest.raises(TypeError):
            dedupe_preserve_order([{1: 2}, {3: 4}])
        with pytest.raises(TypeError):
            dedupe_preserve_order([[1], [2], [1]])

    def test_preserves_order_with_multiple_duplicate_groups(self):
        input_list = [1, 2, 3, 2, 4, 1, 5, 3, 6]
        expected = [1, 2, 3, 4, 5, 6]
        assert dedupe_preserve_order(input_list) == expected

    def test_floats_and_ints(self):
        assert dedupe_preserve_order([1, 1.0, 2, 2.0]) == [1, 2]
        assert dedupe_preserve_order([1.0, 1, 2.0, 2]) == [1.0, 2.0]

    def test_complex_numbers(self):
        assert dedupe_preserve_order([1+2j, 3+4j, 1+2j, 5+6j]) == [1+2j, 3+4j, 5+6j]

    def test_frozensets(self):
        fs1 = frozenset([1, 2])
        fs2 = frozenset([3, 4])
        assert dedupe_preserve_order([fs1, fs2, fs1]) == [fs1, fs2]
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

    def test_all_duplicates(self):
        assert dedupe_preserve_order([1, 1, 1]) == [1]
        assert dedupe_preserve_order(["a", "a", "a", "a"]) == ["a"]

    def test_duplicates_at_start(self):
        assert dedupe_preserve_order([1, 1, 2, 3]) == [1, 2, 3]
        assert dedupe_preserve_order([1, 1, 1, 2, 2, 3]) == [1, 2, 3]

    def test_duplicates_at_end(self):
        assert dedupe_preserve_order([1, 2, 3, 3]) == [1, 2, 3]
        assert dedupe_preserve_order([1, 2, 2, 2]) == [1, 2]

    def test_duplicates_in_middle(self):
        assert dedupe_preserve_order([1, 2, 2, 3]) == [1, 2, 3]
        assert dedupe_preserve_order([1, 2, 2, 2, 3, 3, 4]) == [1, 2, 3, 4]

    def test_preserves_order_of_first_occurrence(self):
        assert dedupe_preserve_order([3, 1, 2, 1, 3, 2]) == [3, 1, 2]
        assert dedupe_preserve_order(["c", "a", "b", "a", "c"]) == ["c", "a", "b"]

    def test_mixed_types(self):
        assert dedupe_preserve_order([1, "1", 1.0, "1"]) == [1, "1", 1.0]
        assert dedupe_preserve_order([True, 1, False, 0]) == [True, 1, False, 0]

    def test_none_values(self):
        assert dedupe_preserve_order([None, 1, None, 2, None]) == [None, 1, 2]
        assert dedupe_preserve_order([None, None, None]) == [None]

    def test_complex_objects(self):
        assert dedupe_preserve_order([[1], [2], [1], [3]]) == [[1], [2], [3]]
        assert dedupe_preserve_order([{"a": 1}, {"b": 2}, {"a": 1}]) == [{"a": 1}, {"b": 2}]

    def test_tuples(self):
        assert dedupe_preserve_order([(1, 2), (3, 4), (1, 2), (5, 6)]) == [(1, 2), (3, 4), (5, 6)]

    def test_strings(self):
        assert dedupe_preserve_order("hello") == ["h", "e", "l", "o"]
        assert dedupe_preserve_order(["hello", "world", "hello"]) == ["hello", "world"]

    def test_large_list(self):
        lst = list(range(1000)) + list(range(1000))
        result = dedupe_preserve_order(lst)
        assert result == list(range(1000))
        assert len(result) == 1000

    def test_returns_new_list(self):
        original = [1, 2, 2, 3]
        result = dedupe_preserve_order(original)
        assert result is not original
        result.append(99)
        assert 99 not in original

    def test_original_list_unchanged(self):
        original = [1, 2, 2, 3]
        original_copy = original.copy()
        dedupe_preserve_order(original)
        assert original == original_copy

    def test_custom_objects_with_hash(self):
        class Custom:
            def __init__(self, value):
                self.value = value
            def __hash__(self):
                return hash(self.value)
            def __eq__(self, other):
                return isinstance(other, Custom) and self.value == other.value
            def __repr__(self):
                return f"Custom({self.value})"

        objs = [Custom(1), Custom(2), Custom(1), Custom(3)]
        result = dedupe_preserve_order(objs)
        assert len(result) == 3
        assert [o.value for o in result] == [1, 2, 3]

    def test_generator_input(self):
        def gen():
            yield 1
            yield 2
            yield 2
            yield 3
        assert dedupe_preserve_order(gen()) == [1, 2, 3]

    def test_iterator_input(self):
        assert dedupe_preserve_order(iter([1, 2, 2, 3])) == [1, 2, 3]

    def test_boolean_and_int_distinction(self):
        assert dedupe_preserve_order([True, 1, False, 0]) == [True, 1, False, 0]
        assert dedupe_preserve_order([False, 0, True, 1]) == [False, 0, True, 1]

    def test_unhashable_types_raises_error(self):
        with pytest.raises(TypeError):
            dedupe_preserve_order([{1: 2}, {3: 4}])
        with pytest.raises(TypeError):
            dedupe_preserve_order([[1], [2], [1]])

    def test_preserves_order_with_multiple_duplicate_groups(self):
        input_list = [1, 2, 3, 2, 4, 1, 5, 3, 6]
        expected = [1, 2, 3, 4, 5, 6]
        assert dedupe_preserve_order(input_list) == expected

    def test_floats_and_ints(self):
        assert dedupe_preserve_order([1, 1.0, 2, 2.0]) == [1, 2]
        assert dedupe_preserve_order([1.0, 1, 2.0, 2]) == [1.0, 2.0]

    def test_complex_numbers(self):
        assert dedupe_preserve_order([1+2j, 3+4j, 1+2j, 5+6j]) == [1+2j, 3+4j, 5+6j]

    def test_frozensets(self):
        fs1 = frozenset([1, 2])
        fs2 = frozenset([3, 4])
        assert dedupe_preserve_order([fs1, fs2, fs1]) == [fs1, fs2]
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

    def test_all_duplicates(self):
        assert dedupe_preserve_order([1, 1, 1]) == [1]
        assert dedupe_preserve_order(["a", "a", "a", "a"]) == ["a"]

    def test_duplicates_at_start(self):
        assert dedupe_preserve_order([1, 1, 2, 3]) == [1, 2, 3]
        assert dedupe_preserve_order([1, 1, 1, 2, 2, 3]) == [1, 2, 3]

    def test_duplicates_at_end(self):
        assert dedupe_preserve_order([1, 2, 3, 3]) == [1, 2, 3]
        assert dedupe_preserve_order([1, 2, 2, 2]) == [1, 2]

    def test_duplicates_in_middle(self):
        assert dedupe_preserve_order([1, 2, 2, 3]) == [1, 2, 3]
        assert dedupe_preserve_order([1, 2, 2, 2, 3, 3, 4]) == [1, 2, 3, 4]

    def test_preserves_order_of_first_occurrence(self):
        assert dedupe_preserve_order([3, 1, 2, 1, 3, 2]) == [3, 1, 2]
        assert dedupe_preserve_order(["c", "a", "b", "a", "c"]) == ["c", "a", "b"]

    def test_mixed_types(self):
        assert dedupe_preserve_order([1, "1", 1.0, "1"]) == [1, "1", 1.0]
        assert dedupe_preserve_order([True, 1, False, 0]) == [True, 1, False, 0]

    def test_none_values(self):
        assert dedupe_preserve_order([None, 1, None, 2, None]) == [None, 1, 2]
        assert dedupe_preserve_order([None, None, None]) == [None]

    def test_complex_objects(self):
        assert dedupe_preserve_order([[1], [2], [1], [3]]) == [[1], [2], [3]]
        assert dedupe_preserve_order([{"a": 1}, {"b": 2}, {"a": 1}]) == [{"a": 1}, {"b": 2}]

    def test_tuples(self):
        assert dedupe_preserve_order([(1, 2), (3, 4), (1, 2), (5, 6)]) == [(1, 2), (3, 4), (5, 6)]

    def test_strings(self):
        assert dedupe_preserve_order("hello") == ["h", "e", "l", "o"]
        assert dedupe_preserve_order(["hello", "world", "hello"]) == ["hello", "world"]

    def test_large_list(self):
        lst = list(range(1000)) + list(range(1000))
        result = dedupe_preserve_order(lst)
        assert result == list(range(1000))
        assert len(result) == 1000

    def test_returns_new_list(self):
        original = [1, 2, 2, 3]
        result = dedupe_preserve_order(original)
        assert result is not original
        result.append(99)
        assert 99 not in original

    def test_original_list_unchanged(self):
        original = [1, 2, 2, 3]
        original_copy = original.copy()
        dedupe_preserve_order(original)
        assert original == original_copy

    def test_custom_objects_with_hash(self):
        class Custom:
            def __init__(self, value):
                self.value = value
            def __hash__(self):
                return hash(self.value)
            def __eq__(self, other):
                return isinstance(other, Custom) and self.value == other.value
            def __repr__(self):
                return f"Custom({self.value})"

        objs = [Custom(1), Custom(2), Custom(1), Custom(3)]
        result = dedupe_preserve_order(objs)
        assert len(result) == 3
        assert [o.value for o in result] == [1, 2, 3]

    def test_generator_input(self):
        def gen():
            yield 1
            yield 2
            yield 2
            yield 3
        assert dedupe_preserve_order(gen()) == [1, 2, 3]

    def test_iterator_input(self):
        assert dedupe_preserve_order(iter([1, 2, 2, 3])) == [1, 2, 3]

    def test_boolean_and_int_distinction(self):
        assert dedupe_preserve_order([True, 1, False, 0]) == [True, 1, False, 0]
        assert dedupe_preserve_order([False, 0, True, 1]) == [False, 0, True, 1]

    def test_unhashable_types_raises_error(self):
        with pytest.raises(TypeError):
            dedupe_preserve_order([{1: 2}, {3: 4}])
        with pytest.raises(TypeError):
            dedupe_preserve_order([[1], [2], [1]])

    def test_preserves_order_with_multiple_duplicate_groups(self):
        input_list = [1, 2, 3, 2, 4, 1, 5, 3, 6]
        expected = [1, 2, 3, 4, 5, 6]
        assert dedupe_preserve_order(input_list) == expected

    def test_floats_and_ints(self):
        assert dedupe_preserve_order([1, 1.0, 2, 2.0]) == [1, 2]
        assert dedupe_preserve_order([1.0, 1, 2.0, 2]) == [1.0, 2.0]

    def test_complex_numbers(self):
        assert dedupe_preserve_order([1+2j, 3+4j, 1+2j, 5+6j]) == [1+2j, 3+4j, 5+6j]

    def test_frozensets(self):
        fs1 = frozenset([1, 2])
        fs2 = frozenset([3, 4])
        assert dedupe_preserve_order([fs1, fs2, fs1]) == [fs1, fs2]
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
