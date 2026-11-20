# Failure artifact: testing_002_dedupe_preserve_order (testing)

- Provider: groq
- Model: openai/gpt-oss-120b
- Score: 0.0
- Status: failed
- Error: reference_impl_failed
- Latency (ms): 3311
- Written (UTC): 20261102-101633
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

@pytest.mark.parametrize(
    "input_list, expected",
    [
        ([], []),  # empty list
        ([1, 2, 3], [1, 2, 3]),  # all unique
        ([1, 1, 1, 1], [1]),  # all duplicates
        ([1, 2, 1, 3, 2, 4], [1, 2, 3, 4]),  # mixed duplicates
        (["a", "b", "a", "c", "b"], ["a", "b", "c"]),  # strings
        ([(1, 2), (1, 2), (2, 3)], [(1, 2), (2, 3)]),  # tuples (hashable)
        ([None, None, 0, False, 0], [None, 0, False]),  # falsy values
    ],
)
def test_dedupe_preserve_order_basic(input_list, expected):
    # Ensure function returns expected deduped list
    result = dedupe_preserve_order(input_list)
    assert result == expected
    # Ensure original list is not mutated
    assert input_list == input_list[:]  # simple identity check


def test_dedupe_preserve_order_original_unchanged():
    original = [1, 2, 2, 3]
    copy = original.copy()
    _ = dedupe_preserve_order(original)
    assert original == copy, "Original list should remain unchanged after call"


def test_dedupe_preserve_order_with_unhashable_raises():
    # Lists are unhashable; expect a TypeError when trying to add to a set
    with pytest.raises(TypeError):
        dedupe_preserve_order([1, [2], 1])


def test_dedupe_preserve_order_large_input():
    # Stress test with a large repeating pattern
    large_input = list(range(1000)) + list(range(500))
    expected = list(range(1000))
    assert dedupe_preserve_order(large_input) == expected


def test_dedupe_preserve_order_preserves_order_of_first_occurrence():
    input_list = ["x", "y", "x", "z", "y", "w"]
    result = dedupe_preserve_order(input_list)
    # The order should follow the first time each element appears
    assert result == ["x", "y", "z", "w"]
```
```

## Extracted code, before import fix

```python
import pytest
from solution import dedupe_preserve_order

@pytest.mark.parametrize(
    "input_list, expected",
    [
        ([], []),  # empty list
        ([1, 2, 3], [1, 2, 3]),  # all unique
        ([1, 1, 1, 1], [1]),  # all duplicates
        ([1, 2, 1, 3, 2, 4], [1, 2, 3, 4]),  # mixed duplicates
        (["a", "b", "a", "c", "b"], ["a", "b", "c"]),  # strings
        ([(1, 2), (1, 2), (2, 3)], [(1, 2), (2, 3)]),  # tuples (hashable)
        ([None, None, 0, False, 0], [None, 0, False]),  # falsy values
    ],
)
def test_dedupe_preserve_order_basic(input_list, expected):
    # Ensure function returns expected deduped list
    result = dedupe_preserve_order(input_list)
    assert result == expected
    # Ensure original list is not mutated
    assert input_list == input_list[:]  # simple identity check


def test_dedupe_preserve_order_original_unchanged():
    original = [1, 2, 2, 3]
    copy = original.copy()
    _ = dedupe_preserve_order(original)
    assert original == copy, "Original list should remain unchanged after call"


def test_dedupe_preserve_order_with_unhashable_raises():
    # Lists are unhashable; expect a TypeError when trying to add to a set
    with pytest.raises(TypeError):
        dedupe_preserve_order([1, [2], 1])


def test_dedupe_preserve_order_large_input():
    # Stress test with a large repeating pattern
    large_input = list(range(1000)) + list(range(500))
    expected = list(range(1000))
    assert dedupe_preserve_order(large_input) == expected


def test_dedupe_preserve_order_preserves_order_of_first_occurrence():
    input_list = ["x", "y", "x", "z", "y", "w"]
    result = dedupe_preserve_order(input_list)
    # The order should follow the first time each element appears
    assert result == ["x", "y", "z", "w"]
```

## Executed code

```python
import pytest
from solution import dedupe_preserve_order

@pytest.mark.parametrize(
    "input_list, expected",
    [
        ([], []),  # empty list
        ([1, 2, 3], [1, 2, 3]),  # all unique
        ([1, 1, 1, 1], [1]),  # all duplicates
        ([1, 2, 1, 3, 2, 4], [1, 2, 3, 4]),  # mixed duplicates
        (["a", "b", "a", "c", "b"], ["a", "b", "c"]),  # strings
        ([(1, 2), (1, 2), (2, 3)], [(1, 2), (2, 3)]),  # tuples (hashable)
        ([None, None, 0, False, 0], [None, 0, False]),  # falsy values
    ],
)
def test_dedupe_preserve_order_basic(input_list, expected):
    # Ensure function returns expected deduped list
    result = dedupe_preserve_order(input_list)
    assert result == expected
    # Ensure original list is not mutated
    assert input_list == input_list[:]  # simple identity check


def test_dedupe_preserve_order_original_unchanged():
    original = [1, 2, 2, 3]
    copy = original.copy()
    _ = dedupe_preserve_order(original)
    assert original == copy, "Original list should remain unchanged after call"


def test_dedupe_preserve_order_with_unhashable_raises():
    # Lists are unhashable; expect a TypeError when trying to add to a set
    with pytest.raises(TypeError):
        dedupe_preserve_order([1, [2], 1])


def test_dedupe_preserve_order_large_input():
    # Stress test with a large repeating pattern
    large_input = list(range(1000)) + list(range(500))
    expected = list(range(1000))
    assert dedupe_preserve_order(large_input) == expected


def test_dedupe_preserve_order_preserves_order_of_first_occurrence():
    input_list = ["x", "y", "x", "z", "y", "w"]
    result = dedupe_preserve_order(input_list)
    # The order should follow the first time each element appears
    assert result == ["x", "y", "z", "w"]
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
