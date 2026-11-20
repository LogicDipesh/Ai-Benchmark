# Failure artifact: testing_002_dedupe_preserve_order (testing)

- Provider: groq
- Model: openai/gpt-oss-120b
- Score: 0.0
- Status: failed
- Error: reference_impl_failed
- Latency (ms): 3684
- Written (UTC): 20261031-144209
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
    "input_list,expected",
    [
        ([], []),  # empty list
        ([1, 2, 3], [1, 2, 3]),  # no duplicates
        ([1, 1, 1, 1], [1]),  # all duplicates
        ([3, 1, 2, 3, 2, 4, 1], [3, 1, 2, 4]),  # mixed duplicates
        (["a", "b", "a", "c", "b"], ["a", "b", "c"]),  # strings
        ([None, None, 1, None, 2], [None, 1, 2]),  # None values
        ([True, False, True, 0, 1], [True, False, 0, 1]),  # booleans and ints (True == 1)
        (["", "", " ", " "], ["", " "]),  # empty and space strings
    ],
)
def test_dedupe_preserve_order_basic(input_list, expected):
    assert dedupe_preserve_order(input_list) == expected


def test_dedupe_preserve_order_order_preserved():
    lst = ["first", "second", "first", "third", "second", "fourth"]
    result = dedupe_preserve_order(lst)
    # ensure the first occurrence order is retained
    assert result == ["first", "second", "third", "fourth"]
    # verify each element appears only once
    assert len(set(result)) == len(result)


def test_dedupe_preserve_order_mutable_unhashable():
    # Lists are unhashable, should raise a TypeError
    with pytest.raises(TypeError):
        dedupe_preserve_order([[1], [2], [1]])


def test_dedupe_preserve_order_mixed_hashable_types():
    mixed = [1, "1", 1.0, (1,), 1]  # note 1 == 1.0 but different hash behaviour
    # Python treats 1 and 1.0 as equal for set membership
    assert dedupe_preserve_order(mixed) == [1, "1", (1,)]


def test_dedupe_preserve_order_large_input():
    # Large list with repeating pattern
    pattern = list(range(100))
    large = pattern * 1000  # 100,000 elements with many duplicates
    result = dedupe_preserve_order(large)
    assert result == pattern
    assert len(result) == 100
```
```

## Extracted code, before import fix

```python
import pytest
from solution import dedupe_preserve_order

@pytest.mark.parametrize(
    "input_list,expected",
    [
        ([], []),  # empty list
        ([1, 2, 3], [1, 2, 3]),  # no duplicates
        ([1, 1, 1, 1], [1]),  # all duplicates
        ([3, 1, 2, 3, 2, 4, 1], [3, 1, 2, 4]),  # mixed duplicates
        (["a", "b", "a", "c", "b"], ["a", "b", "c"]),  # strings
        ([None, None, 1, None, 2], [None, 1, 2]),  # None values
        ([True, False, True, 0, 1], [True, False, 0, 1]),  # booleans and ints (True == 1)
        (["", "", " ", " "], ["", " "]),  # empty and space strings
    ],
)
def test_dedupe_preserve_order_basic(input_list, expected):
    assert dedupe_preserve_order(input_list) == expected


def test_dedupe_preserve_order_order_preserved():
    lst = ["first", "second", "first", "third", "second", "fourth"]
    result = dedupe_preserve_order(lst)
    # ensure the first occurrence order is retained
    assert result == ["first", "second", "third", "fourth"]
    # verify each element appears only once
    assert len(set(result)) == len(result)


def test_dedupe_preserve_order_mutable_unhashable():
    # Lists are unhashable, should raise a TypeError
    with pytest.raises(TypeError):
        dedupe_preserve_order([[1], [2], [1]])


def test_dedupe_preserve_order_mixed_hashable_types():
    mixed = [1, "1", 1.0, (1,), 1]  # note 1 == 1.0 but different hash behaviour
    # Python treats 1 and 1.0 as equal for set membership
    assert dedupe_preserve_order(mixed) == [1, "1", (1,)]


def test_dedupe_preserve_order_large_input():
    # Large list with repeating pattern
    pattern = list(range(100))
    large = pattern * 1000  # 100,000 elements with many duplicates
    result = dedupe_preserve_order(large)
    assert result == pattern
    assert len(result) == 100
```

## Executed code

```python
import pytest
from solution import dedupe_preserve_order

@pytest.mark.parametrize(
    "input_list,expected",
    [
        ([], []),  # empty list
        ([1, 2, 3], [1, 2, 3]),  # no duplicates
        ([1, 1, 1, 1], [1]),  # all duplicates
        ([3, 1, 2, 3, 2, 4, 1], [3, 1, 2, 4]),  # mixed duplicates
        (["a", "b", "a", "c", "b"], ["a", "b", "c"]),  # strings
        ([None, None, 1, None, 2], [None, 1, 2]),  # None values
        ([True, False, True, 0, 1], [True, False, 0, 1]),  # booleans and ints (True == 1)
        (["", "", " ", " "], ["", " "]),  # empty and space strings
    ],
)
def test_dedupe_preserve_order_basic(input_list, expected):
    assert dedupe_preserve_order(input_list) == expected


def test_dedupe_preserve_order_order_preserved():
    lst = ["first", "second", "first", "third", "second", "fourth"]
    result = dedupe_preserve_order(lst)
    # ensure the first occurrence order is retained
    assert result == ["first", "second", "third", "fourth"]
    # verify each element appears only once
    assert len(set(result)) == len(result)


def test_dedupe_preserve_order_mutable_unhashable():
    # Lists are unhashable, should raise a TypeError
    with pytest.raises(TypeError):
        dedupe_preserve_order([[1], [2], [1]])


def test_dedupe_preserve_order_mixed_hashable_types():
    mixed = [1, "1", 1.0, (1,), 1]  # note 1 == 1.0 but different hash behaviour
    # Python treats 1 and 1.0 as equal for set membership
    assert dedupe_preserve_order(mixed) == [1, "1", (1,)]


def test_dedupe_preserve_order_large_input():
    # Large list with repeating pattern
    pattern = list(range(100))
    large = pattern * 1000  # 100,000 elements with many duplicates
    result = dedupe_preserve_order(large)
    assert result == pattern
    assert len(result) == 100
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
