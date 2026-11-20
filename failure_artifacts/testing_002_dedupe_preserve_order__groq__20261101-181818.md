# Failure artifact: testing_002_dedupe_preserve_order (testing)

- Provider: groq
- Model: openai/gpt-oss-120b
- Score: 0.0
- Status: failed
- Error: reference_impl_failed
- Latency (ms): 1950
- Written (UTC): 20261101-181818
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
        # Empty list
        ([], []),
        # All unique elements
        ([1, 2, 3, 4], [1, 2, 3, 4]),
        # All duplicates
        (['a', 'a', 'a'], ['a']),
        # Mixed duplicates, preserving first occurrence order
        (['a', 'b', 'a', 'c', 'b', 'd'], ['a', 'b', 'c', 'd']),
        # Integers with zero and negative values
        ([0, -1, 0, -1, 2], [0, -1, 2]),
        # Different types, hashable
        ([(1, 2), (1, 2), (2, 3)], [(1, 2), (2, 3)]),
        # None and False values (distinct hashable objects)
        ([None, False, None, False, 0], [None, False, 0]),
        # Large list with repeated pattern
        (list(range(1000)) + list(range(500)), list(range(1000))),
    ],
)
def test_dedupe_preserve_order_various_cases(input_list, expected):
    # Ensure original list is not modified
    original = list(input_list)
    result = dedupe_preserve_order(input_list)
    assert result == expected
    assert input_list == original  # function should not mutate input


def test_dedupe_preserve_order_order_stability():
    """Explicitly verify that the order of first occurrence is kept."""
    lst = ['z', 'x', 'y', 'x', 'z', 'a']
    expected = ['z', 'x', 'y', 'a']
    assert dedupe_preserve_order(lst) == expected


def test_dedupe_preserve_order_unhashable_raises():
    """The function relies on a set; unhashable items should raise TypeError."""
    lst = [[1, 2], [1, 2], [3, 4]]
    with pytest.raises(TypeError):
        dedupe_preserve_order(lst)


def test_dedupe_preserve_order_mutable_hashable_objects():
    """Mutable objects that are hashable (e.g., frozenset) should work."""
    a = frozenset([1, 2])
    b = frozenset([2, 3])
    lst = [a, b, a, b]
    expected = [a, b]
    assert dedupe_preserve_order(lst) == expected
```
```

## Extracted code, before import fix

```python
import pytest
from solution import dedupe_preserve_order

@pytest.mark.parametrize(
    "input_list, expected",
    [
        # Empty list
        ([], []),
        # All unique elements
        ([1, 2, 3, 4], [1, 2, 3, 4]),
        # All duplicates
        (['a', 'a', 'a'], ['a']),
        # Mixed duplicates, preserving first occurrence order
        (['a', 'b', 'a', 'c', 'b', 'd'], ['a', 'b', 'c', 'd']),
        # Integers with zero and negative values
        ([0, -1, 0, -1, 2], [0, -1, 2]),
        # Different types, hashable
        ([(1, 2), (1, 2), (2, 3)], [(1, 2), (2, 3)]),
        # None and False values (distinct hashable objects)
        ([None, False, None, False, 0], [None, False, 0]),
        # Large list with repeated pattern
        (list(range(1000)) + list(range(500)), list(range(1000))),
    ],
)
def test_dedupe_preserve_order_various_cases(input_list, expected):
    # Ensure original list is not modified
    original = list(input_list)
    result = dedupe_preserve_order(input_list)
    assert result == expected
    assert input_list == original  # function should not mutate input


def test_dedupe_preserve_order_order_stability():
    """Explicitly verify that the order of first occurrence is kept."""
    lst = ['z', 'x', 'y', 'x', 'z', 'a']
    expected = ['z', 'x', 'y', 'a']
    assert dedupe_preserve_order(lst) == expected


def test_dedupe_preserve_order_unhashable_raises():
    """The function relies on a set; unhashable items should raise TypeError."""
    lst = [[1, 2], [1, 2], [3, 4]]
    with pytest.raises(TypeError):
        dedupe_preserve_order(lst)


def test_dedupe_preserve_order_mutable_hashable_objects():
    """Mutable objects that are hashable (e.g., frozenset) should work."""
    a = frozenset([1, 2])
    b = frozenset([2, 3])
    lst = [a, b, a, b]
    expected = [a, b]
    assert dedupe_preserve_order(lst) == expected
```

## Executed code

```python
import pytest
from solution import dedupe_preserve_order

@pytest.mark.parametrize(
    "input_list, expected",
    [
        # Empty list
        ([], []),
        # All unique elements
        ([1, 2, 3, 4], [1, 2, 3, 4]),
        # All duplicates
        (['a', 'a', 'a'], ['a']),
        # Mixed duplicates, preserving first occurrence order
        (['a', 'b', 'a', 'c', 'b', 'd'], ['a', 'b', 'c', 'd']),
        # Integers with zero and negative values
        ([0, -1, 0, -1, 2], [0, -1, 2]),
        # Different types, hashable
        ([(1, 2), (1, 2), (2, 3)], [(1, 2), (2, 3)]),
        # None and False values (distinct hashable objects)
        ([None, False, None, False, 0], [None, False, 0]),
        # Large list with repeated pattern
        (list(range(1000)) + list(range(500)), list(range(1000))),
    ],
)
def test_dedupe_preserve_order_various_cases(input_list, expected):
    # Ensure original list is not modified
    original = list(input_list)
    result = dedupe_preserve_order(input_list)
    assert result == expected
    assert input_list == original  # function should not mutate input


def test_dedupe_preserve_order_order_stability():
    """Explicitly verify that the order of first occurrence is kept."""
    lst = ['z', 'x', 'y', 'x', 'z', 'a']
    expected = ['z', 'x', 'y', 'a']
    assert dedupe_preserve_order(lst) == expected


def test_dedupe_preserve_order_unhashable_raises():
    """The function relies on a set; unhashable items should raise TypeError."""
    lst = [[1, 2], [1, 2], [3, 4]]
    with pytest.raises(TypeError):
        dedupe_preserve_order(lst)


def test_dedupe_preserve_order_mutable_hashable_objects():
    """Mutable objects that are hashable (e.g., frozenset) should work."""
    a = frozenset([1, 2])
    b = frozenset([2, 3])
    lst = [a, b, a, b]
    expected = [a, b]
    assert dedupe_preserve_order(lst) == expected
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
