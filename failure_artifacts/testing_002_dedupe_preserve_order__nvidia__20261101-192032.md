# Failure artifact: testing_002_dedupe_preserve_order (testing)

- Provider: nvidia
- Model: nvidia/nemotron-3-ultra-550b-a55b
- Score: 0.0
- Status: failed
- Error: reference_impl_failed
- Latency (ms): 18881
- Written (UTC): 20261101-192032
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


def test_empty_list():
    assert dedupe_preserve_order([]) == []


def test_single_element():
    assert dedupe_preserve_order([1]) == [1]
    assert dedupe_preserve_order(["a"]) == ["a"]
    assert dedupe_preserve_order([None]) == [None]


def test_no_duplicates():
    assert dedupe_preserve_order([1, 2, 3]) == [1, 2, 3]
    assert dedupe_preserve_order(["a", "b", "c"]) == ["a", "b", "c"]
    assert dedupe_preserve_order([1, "a", 2.5, True]) == [1, "a", 2.5, True]


def test_all_duplicates():
    assert dedupe_preserve_order([1, 1, 1, 1]) == [1]
    assert dedupe_preserve_order(["x", "x", "x"]) == ["x"]


def test_some_duplicates():
    assert dedupe_preserve_order([1, 2, 2, 3, 3, 3]) == [1, 2, 3]
    assert dedupe_preserve_order(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]


def test_order_preservation():
    result = dedupe_preserve_order([3, 1, 2, 1, 3, 2])
    assert result == [3, 1, 2]
    assert result.index(3) < result.index(1) < result.index(2)


def test_mixed_types():
    assert dedupe_preserve_order([1, "1", 1.0, True]) == [1, "1", 1.0, True]
    assert dedupe_preserve_order([None, 0, False, ""]) == [None, 0, False, ""]


def test_none_values():
    assert dedupe_preserve_order([None, 1, None, 2, None]) == [None, 1, 2]
    assert dedupe_preserve_order([None, None]) == [None]


def test_original_list_unmodified():
    original = [1, 2, 2, 3]
    original_copy = original.copy()
    dedupe_preserve_order(original)
    assert original == original_copy


def test_strings():
    assert dedupe_preserve_order(["apple", "banana", "apple", "cherry"]) == ["apple", "banana", "cherry"]
    assert dedupe_preserve_order(["a", "b", "c", "a", "b"]) == ["a", "b", "c"]


def test_tuples_as_elements():
    assert dedupe_preserve_order([(1, 2), (3, 4), (1, 2)]) == [(1, 2), (3, 4)]


def test_large_list():
    large = list(range(1000)) + list(range(1000))
    result = dedupe_preserve_order(large)
    assert result == list(range(1000))
    assert len(result) == 1000


def test_negative_numbers():
    assert dedupe_preserve_order([-1, -2, -1, 0, -2]) == [-1, -2, 0]


def test_floats():
    assert dedupe_preserve_order([1.1, 2.2, 1.1, 3.3]) == [1.1, 2.2, 3.3]


def test_booleans():
    assert dedupe_preserve_order([True, False, True, False]) == [True, False]
    assert dedupe_preserve_order([True, 1, False, 0]) == [True, False]


def test_complex_numbers():
    assert dedupe_preserve_order([1+2j, 3+4j, 1+2j]) == [1+2j, 3+4j]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```
```

## Extracted code, before import fix

```python
import pytest
from solution import dedupe_preserve_order


def test_empty_list():
    assert dedupe_preserve_order([]) == []


def test_single_element():
    assert dedupe_preserve_order([1]) == [1]
    assert dedupe_preserve_order(["a"]) == ["a"]
    assert dedupe_preserve_order([None]) == [None]


def test_no_duplicates():
    assert dedupe_preserve_order([1, 2, 3]) == [1, 2, 3]
    assert dedupe_preserve_order(["a", "b", "c"]) == ["a", "b", "c"]
    assert dedupe_preserve_order([1, "a", 2.5, True]) == [1, "a", 2.5, True]


def test_all_duplicates():
    assert dedupe_preserve_order([1, 1, 1, 1]) == [1]
    assert dedupe_preserve_order(["x", "x", "x"]) == ["x"]


def test_some_duplicates():
    assert dedupe_preserve_order([1, 2, 2, 3, 3, 3]) == [1, 2, 3]
    assert dedupe_preserve_order(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]


def test_order_preservation():
    result = dedupe_preserve_order([3, 1, 2, 1, 3, 2])
    assert result == [3, 1, 2]
    assert result.index(3) < result.index(1) < result.index(2)


def test_mixed_types():
    assert dedupe_preserve_order([1, "1", 1.0, True]) == [1, "1", 1.0, True]
    assert dedupe_preserve_order([None, 0, False, ""]) == [None, 0, False, ""]


def test_none_values():
    assert dedupe_preserve_order([None, 1, None, 2, None]) == [None, 1, 2]
    assert dedupe_preserve_order([None, None]) == [None]


def test_original_list_unmodified():
    original = [1, 2, 2, 3]
    original_copy = original.copy()
    dedupe_preserve_order(original)
    assert original == original_copy


def test_strings():
    assert dedupe_preserve_order(["apple", "banana", "apple", "cherry"]) == ["apple", "banana", "cherry"]
    assert dedupe_preserve_order(["a", "b", "c", "a", "b"]) == ["a", "b", "c"]


def test_tuples_as_elements():
    assert dedupe_preserve_order([(1, 2), (3, 4), (1, 2)]) == [(1, 2), (3, 4)]


def test_large_list():
    large = list(range(1000)) + list(range(1000))
    result = dedupe_preserve_order(large)
    assert result == list(range(1000))
    assert len(result) == 1000


def test_negative_numbers():
    assert dedupe_preserve_order([-1, -2, -1, 0, -2]) == [-1, -2, 0]


def test_floats():
    assert dedupe_preserve_order([1.1, 2.2, 1.1, 3.3]) == [1.1, 2.2, 3.3]


def test_booleans():
    assert dedupe_preserve_order([True, False, True, False]) == [True, False]
    assert dedupe_preserve_order([True, 1, False, 0]) == [True, False]


def test_complex_numbers():
    assert dedupe_preserve_order([1+2j, 3+4j, 1+2j]) == [1+2j, 3+4j]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

## Executed code

```python
import pytest
from solution import dedupe_preserve_order


def test_empty_list():
    assert dedupe_preserve_order([]) == []


def test_single_element():
    assert dedupe_preserve_order([1]) == [1]
    assert dedupe_preserve_order(["a"]) == ["a"]
    assert dedupe_preserve_order([None]) == [None]


def test_no_duplicates():
    assert dedupe_preserve_order([1, 2, 3]) == [1, 2, 3]
    assert dedupe_preserve_order(["a", "b", "c"]) == ["a", "b", "c"]
    assert dedupe_preserve_order([1, "a", 2.5, True]) == [1, "a", 2.5, True]


def test_all_duplicates():
    assert dedupe_preserve_order([1, 1, 1, 1]) == [1]
    assert dedupe_preserve_order(["x", "x", "x"]) == ["x"]


def test_some_duplicates():
    assert dedupe_preserve_order([1, 2, 2, 3, 3, 3]) == [1, 2, 3]
    assert dedupe_preserve_order(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]


def test_order_preservation():
    result = dedupe_preserve_order([3, 1, 2, 1, 3, 2])
    assert result == [3, 1, 2]
    assert result.index(3) < result.index(1) < result.index(2)


def test_mixed_types():
    assert dedupe_preserve_order([1, "1", 1.0, True]) == [1, "1", 1.0, True]
    assert dedupe_preserve_order([None, 0, False, ""]) == [None, 0, False, ""]


def test_none_values():
    assert dedupe_preserve_order([None, 1, None, 2, None]) == [None, 1, 2]
    assert dedupe_preserve_order([None, None]) == [None]


def test_original_list_unmodified():
    original = [1, 2, 2, 3]
    original_copy = original.copy()
    dedupe_preserve_order(original)
    assert original == original_copy


def test_strings():
    assert dedupe_preserve_order(["apple", "banana", "apple", "cherry"]) == ["apple", "banana", "cherry"]
    assert dedupe_preserve_order(["a", "b", "c", "a", "b"]) == ["a", "b", "c"]


def test_tuples_as_elements():
    assert dedupe_preserve_order([(1, 2), (3, 4), (1, 2)]) == [(1, 2), (3, 4)]


def test_large_list():
    large = list(range(1000)) + list(range(1000))
    result = dedupe_preserve_order(large)
    assert result == list(range(1000))
    assert len(result) == 1000


def test_negative_numbers():
    assert dedupe_preserve_order([-1, -2, -1, 0, -2]) == [-1, -2, 0]


def test_floats():
    assert dedupe_preserve_order([1.1, 2.2, 1.1, 3.3]) == [1.1, 2.2, 3.3]


def test_booleans():
    assert dedupe_preserve_order([True, False, True, False]) == [True, False]
    assert dedupe_preserve_order([True, 1, False, 0]) == [True, False]


def test_complex_numbers():
    assert dedupe_preserve_order([1+2j, 3+4j, 1+2j]) == [1+2j, 3+4j]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
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
